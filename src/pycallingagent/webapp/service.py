from __future__ import annotations

import asyncio
import json
import mimetypes
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

import pandas as pd
import pdfplumber
from fastapi import UploadFile

from .models import (
    ArtifactRecord,
    ChatMessageRecord,
    InputFileRecord,
    RunEvent,
    RunRecord,
    RunResult,
    SessionRecord,
)


@dataclass
class ParsedInputBundle:
    tickers: list[str] = field(default_factory=list)
    dataframes: dict[str, pd.DataFrame] = field(default_factory=dict)
    pdf_documents: dict[str, dict[str, Any]] = field(default_factory=dict)
    input_files: list[InputFileRecord] = field(default_factory=list)


class RunnerProtocol(Protocol):
    async def run(
        self,
        prompt: str,
        bundle: ParsedInputBundle,
        workspace: Path,
        emit,
    ) -> RunResult:
        ...


class RunService:
    COMPANY_ALIASES = {
        "advanced micro devices": "AMD",
        "amd": "AMD",
        "nvidia": "NVDA",
        "tesla": "TSLA",
        "apple": "AAPL",
        "microsoft": "MSFT",
        "amazon": "AMZN",
        "alphabet": "GOOGL",
        "google": "GOOGL",
        "meta": "META",
        "facebook": "META",
        "netflix": "NFLX",
        "broadcom": "AVGO",
        "palantir": "PLTR",
        "berkshire hathaway": "BRK.B",
        "spy": "SPY",
        "s&p 500": "SPY",
        "sp 500": "SPY",
        "u.s. equity market": "SPY",
        "us equity market": "SPY",
        "u.s. stock market": "SPY",
        "us stock market": "SPY",
        "equity market": "SPY",
        "stock market": "SPY",
        "market snapshot": "SPY",
    }
    TICKER_STOP_WORDS = {
        "A",
        "AI",
        "AN",
        "AND",
        "ARE",
        "AS",
        "AT",
        "DO",
        "ETF",
        "FOR",
        "GIVE",
        "HOW",
        "I",
        "IN",
        "IS",
        "IT",
        "ME",
        "NOW",
        "OF",
        "ON",
        "OR",
        "SHOW",
        "SUMMARIZE",
        "THE",
        "TO",
        "US",
        "VIEW",
        "VS",
        "WHAT",
    }
    FINANCE_KEYWORDS = {
        "alpha",
        "balance sheet",
        "bull",
        "company",
        "compare",
        "earnings",
        "equity",
        "etf",
        "filing",
        "filings",
        "finance",
        "financial",
        "fund",
        "fundamental",
        "fundamentals",
        "growth",
        "market",
        "market cap",
        "net income",
        "p/e",
        "pe ratio",
        "performance",
        "price",
        "prices",
        "quarter",
        "quarters",
        "research",
        "revenue",
        "risk",
        "sector",
        "snapshot",
        "stock",
        "stocks",
        "ticker",
        "trend",
        "valuation",
        "yield",
    }

    def __init__(self, storage_root: Path, runner: RunnerProtocol):
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.runner = runner
        self._runs: dict[str, RunRecord] = {}
        self._sessions: dict[str, SessionRecord] = {}

    async def create_run(self, prompt: str, tickers: str, files: list[UploadFile] | None = None) -> RunRecord:
        run_id = uuid4().hex[:12]
        workspace = self.storage_root / run_id
        uploads_dir = workspace / "uploads"
        outputs_dir = workspace / "outputs"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir.mkdir(parents=True, exist_ok=True)

        normalized_tickers = self._resolve_tickers(prompt, tickers)
        record = RunRecord(run_id=run_id, prompt=prompt, workspace=workspace, tickers=normalized_tickers)
        self._runs[run_id] = record

        saved_files = await self._save_uploads(uploads_dir, files)
        record.input_files = saved_files
        self._append_run_event(record, "status", {"message": "Run created", "status": "pending"})
        asyncio.create_task(self._execute_run(record, saved_files))
        return record

    async def create_session(self, tickers: str = "") -> SessionRecord:
        session_id = uuid4().hex[:12]
        workspace = self.storage_root / "sessions" / session_id
        workspace.mkdir(parents=True, exist_ok=True)
        session = SessionRecord(
            session_id=session_id,
            workspace=workspace,
            tickers=self._normalize_tickers(tickers),
        )
        self._sessions[session_id] = session
        self._append_session_event(session, "session", {"message": "Session created", "status": "idle"})
        return session

    async def create_session_message(
        self,
        session_id: str,
        prompt: str,
        tickers: str = "",
        files: list[UploadFile] | None = None,
    ) -> RunRecord:
        session = self.get_session(session_id)
        normalized_tickers = self._resolve_tickers(prompt, tickers, session.tickers)
        if not normalized_tickers and self._is_finance_prompt(prompt):
            raise RuntimeError("Could not infer a company, ETF, or market proxy from the prompt.")

        if normalized_tickers:
            session.tickers = normalized_tickers
        user_message = ChatMessageRecord(role="user", content=prompt, tickers=list(normalized_tickers))
        session.messages.append(user_message)
        self._append_session_event(session, "user", {"role": "user", "content": prompt})

        run_id = uuid4().hex[:12]
        workspace = session.workspace / "runs" / run_id
        uploads_dir = workspace / "uploads"
        outputs_dir = workspace / "outputs"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir.mkdir(parents=True, exist_ok=True)

        record = RunRecord(
            run_id=run_id,
            prompt=prompt,
            workspace=workspace,
            tickers=normalized_tickers,
            session_id=session_id,
        )
        self._runs[run_id] = record
        session.run_id = run_id
        session.status = "pending"

        saved_files = await self._save_uploads(uploads_dir, files)
        record.input_files = saved_files
        self._append_run_event(record, "status", {"message": "Run created", "status": "pending"})
        self._append_session_event(session, "status", {"message": "Run created", "status": "pending", "run_id": run_id})
        asyncio.create_task(self._execute_session_run(session, record, saved_files))
        return record

    def get_run(self, run_id: str) -> RunRecord:
        if run_id not in self._runs:
            raise KeyError(run_id)
        return self._runs[run_id]

    def get_session(self, session_id: str) -> SessionRecord:
        if session_id not in self._sessions:
            raise KeyError(session_id)
        return self._sessions[session_id]

    def get_artifact(self, run_id: str, artifact_name: str) -> ArtifactRecord:
        record = self.get_run(run_id)
        for artifact in record.artifacts:
            if artifact.name == artifact_name:
                return artifact
        raise KeyError(artifact_name)

    def parse_saved_files(self, saved_paths: list[Path]) -> ParsedInputBundle:
        records = [
            InputFileRecord(
                name=path.name,
                media_type=mimetypes.guess_type(path.name)[0] or "application/octet-stream",
                saved_path=path,
                kind=self._classify_file(path.name),
            )
            for path in saved_paths
        ]
        return self._parse_file_records(records)

    def build_bundle(self, tickers: str, saved_paths: list[Path] | None = None) -> ParsedInputBundle:
        bundle = self.parse_saved_files(saved_paths or []) if saved_paths else ParsedInputBundle()
        bundle.tickers = self._normalize_tickers(tickers)
        return bundle

    def infer_tickers_from_prompt(self, prompt: str) -> list[str]:
        candidates: list[tuple[int, str]] = []
        lowered = prompt.lower()

        for phrase, ticker in sorted(self.COMPANY_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
            start = lowered.find(phrase)
            if start >= 0:
                candidates.append((start, ticker))

        for match in re.finditer(r"\b[A-Z]{1,5}(?:\.[A-Z])?\b", prompt):
            candidate = match.group(0).upper()
            if candidate in self.TICKER_STOP_WORDS:
                continue
            candidates.append((match.start(), candidate))

        candidates.sort(key=lambda item: item[0])
        normalized = []
        for _, ticker in candidates:
            if ticker not in normalized:
                normalized.append(ticker)
        return normalized

    async def stream_events(self, run_id: str):
        record = self.get_run(run_id)
        async for event in self._stream_from_events(record.events, lambda: record.status):
            yield event

    async def stream_session_events(self, session_id: str):
        session = self.get_session(session_id)
        async for event in self._stream_from_events(session.events, lambda: session.status):
            yield event

    async def _stream_from_events(self, events: list[RunEvent], status_fn):
        index = 0
        while True:
            while index < len(events):
                event = events[index]
                payload = json.dumps(event.data, ensure_ascii=False)
                yield f"event: {event.event}\ndata: {payload}\n\n"
                index += 1
            if status_fn() in {"completed", "failed"} and index >= len(events):
                break
            await asyncio.sleep(0.05)

    async def _execute_run(self, record: RunRecord, saved_files: list[InputFileRecord]) -> None:
        try:
            run_label = "Running general assistant" if not record.tickers else "Running financial research agent"
            record.status = "parsing"
            self._append_run_event(record, "status", {"message": "Preparing research inputs", "status": "parsing"})
            bundle = self._parse_file_records(saved_files) if saved_files else ParsedInputBundle()
            bundle.tickers = list(record.tickers)
            record.input_files = bundle.input_files

            record.status = "running"
            self._append_run_event(record, "status", {"message": run_label, "status": "running"})
            result = await self.runner.run(
                record.prompt,
                bundle,
                record.workspace,
                lambda event, data: self._append_run_event(record, event, data),
            )

            self._hydrate_run_record(record, result)
            record.status = "completed"
            self._append_run_event(record, "completed", {"status": "completed"})
        except Exception as exc:
            record.status = "failed"
            record.error_message = str(exc)
            self._append_run_event(record, "failed", {"status": "failed", "message": record.error_message})

    async def _execute_session_run(
        self,
        session: SessionRecord,
        record: RunRecord,
        saved_files: list[InputFileRecord],
    ) -> None:
        try:
            run_label = "Running general assistant" if not record.tickers else "Running financial research agent"
            record.status = "parsing"
            session.status = "parsing"
            self._append_run_event(record, "status", {"message": "Preparing research inputs", "status": "parsing"})
            self._append_session_event(session, "status", {"message": "Preparing research inputs", "status": "parsing", "run_id": record.run_id})

            bundle = self._parse_file_records(saved_files) if saved_files else ParsedInputBundle()
            bundle.tickers = list(record.tickers)
            record.input_files = bundle.input_files

            record.status = "running"
            session.status = "running"
            self._append_run_event(record, "status", {"message": run_label, "status": "running"})
            self._append_session_event(session, "status", {"message": run_label, "status": "running", "run_id": record.run_id})

            result = await self.runner.run(
                record.prompt,
                bundle,
                record.workspace,
                lambda event, data: self._forward_runner_event(session, record, event, data),
            )

            self._hydrate_run_record(record, result)
            session.messages.append(
                ChatMessageRecord(
                    role="assistant",
                    content=result.summary_text,
                    tickers=list(record.tickers),
                    run_id=record.run_id,
                )
            )
            session.run_id = record.run_id
            session.summary_text = result.summary_text
            session.snapshot_cards = result.snapshot_cards
            session.preview_tables = result.preview_tables
            session.preview_charts = [self._attach_chart_run_id(chart, record.run_id) for chart in result.preview_charts]
            session.artifacts = self._merge_session_artifacts(session.artifacts, record.artifacts)
            record.status = "completed"
            session.status = "completed"
            self._append_run_event(record, "completed", {"status": "completed"})
            self._append_session_event(session, "completed", {"status": "completed", "run_id": record.run_id})
        except Exception as exc:
            record.status = "failed"
            record.error_message = str(exc)
            session.status = "failed"
            session.error_message = str(exc)
            self._append_run_event(record, "failed", {"status": "failed", "message": record.error_message})
            self._append_session_event(session, "failed", {"status": "failed", "message": session.error_message, "run_id": record.run_id})

    def _hydrate_run_record(self, record: RunRecord, result: RunResult) -> None:
        record.summary_text = result.summary_text
        record.artifacts = [self._attach_artifact_run_id(artifact, record.run_id) for artifact in result.artifacts]
        record.snapshot_cards = result.snapshot_cards
        record.preview_tables = result.preview_tables
        record.preview_charts = [self._attach_chart_run_id(chart, record.run_id) for chart in result.preview_charts]

    def _forward_runner_event(self, session: SessionRecord, record: RunRecord, event: str, data: dict[str, Any]) -> None:
        self._append_run_event(record, event, data)
        payload = dict(data)
        payload.setdefault("run_id", record.run_id)
        self._append_session_event(session, event, payload)

    def _merge_session_artifacts(
        self,
        existing_artifacts: list[ArtifactRecord],
        new_artifacts: list[ArtifactRecord],
    ) -> list[ArtifactRecord]:
        existing = {
            (artifact.run_id, artifact.name): artifact
            for artifact in existing_artifacts
        }
        ordered = []
        for artifact in new_artifacts:
            key = (artifact.run_id, artifact.name)
            if key not in existing:
                ordered.append(artifact)
        ordered.extend(existing_artifacts)
        return ordered

    def _attach_artifact_run_id(self, artifact: ArtifactRecord, run_id: str) -> ArtifactRecord:
        return ArtifactRecord(
            name=artifact.name,
            path=artifact.path,
            content_type=artifact.content_type,
            kind=artifact.kind,
            label=artifact.label,
            run_id=run_id,
        )

    def _attach_chart_run_id(self, chart: dict[str, Any], run_id: str) -> dict[str, Any]:
        hydrated = dict(chart)
        hydrated["run_id"] = run_id
        return hydrated

    async def _save_uploads(self, uploads_dir: Path, files: list[UploadFile] | None) -> list[InputFileRecord]:
        saved_files: list[InputFileRecord] = []
        for upload in files or []:
            safe_name = self._sanitize_filename(upload.filename or "upload.bin")
            saved_path = uploads_dir / safe_name
            content = await upload.read()
            saved_path.write_bytes(content)
            saved_files.append(
                InputFileRecord(
                    name=safe_name,
                    media_type=upload.content_type or mimetypes.guess_type(safe_name)[0] or "application/octet-stream",
                    saved_path=saved_path,
                    kind=self._classify_file(safe_name),
                )
            )
        return saved_files

    def _parse_file_records(self, records: list[InputFileRecord]) -> ParsedInputBundle:
        bundle = ParsedInputBundle(input_files=records)
        for record in records:
            if record.kind == "csv":
                bundle.dataframes[record.name] = pd.read_csv(record.saved_path)
            elif record.kind == "xlsx":
                sheets = pd.read_excel(record.saved_path, sheet_name=None)
                for sheet_name, dataframe in sheets.items():
                    bundle.dataframes[f"{record.name}:{sheet_name}"] = dataframe
            elif record.kind == "pdf":
                bundle.pdf_documents[record.name] = self._parse_pdf(record.saved_path)
        return bundle

    def _parse_pdf(self, path: Path) -> dict[str, Any]:
        try:
            pages: list[dict[str, Any]] = []
            tables: list[dict[str, Any]] = []
            with pdfplumber.open(path) as pdf:
                for page_number, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    pages.append({"page": page_number, "text": text})
                    for table_index, table in enumerate(page.extract_tables(), start=1):
                        if not table:
                            continue
                        frame = pd.DataFrame(table[1:], columns=table[0] or None)
                        tables.append(
                            {
                                "page": page_number,
                                "table_index": table_index,
                                "dataframe": frame,
                            }
                        )
            return {
                "status": "ok",
                "pages": pages,
                "tables": tables,
                "text": "\n\n".join(page["text"] for page in pages if page["text"]),
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc), "pages": [], "tables": [], "text": ""}

    def _append_run_event(self, record: RunRecord, event: str, data: dict[str, Any]) -> None:
        record.events.append(RunEvent(event=event, data=data))

    def _append_session_event(self, session: SessionRecord, event: str, data: dict[str, Any]) -> None:
        session.events.append(RunEvent(event=event, data=data))

    def _classify_file(self, filename: str) -> str:
        lower = filename.lower()
        if lower.endswith(".csv"):
            return "csv"
        if lower.endswith(".xlsx") or lower.endswith(".xlsm"):
            return "xlsx"
        if lower.endswith(".pdf"):
            return "pdf"
        return "binary"

    def _sanitize_filename(self, filename: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", filename).strip("-")
        return cleaned or "upload.bin"

    def _normalize_tickers(self, tickers: str | list[str]) -> list[str]:
        if isinstance(tickers, list):
            raw_values = tickers
        else:
            raw_values = tickers.split(",")
        normalized = []
        for value in raw_values:
            cleaned = re.sub(r"[^A-Za-z0-9.-]+", "", value.strip().upper())
            if cleaned and cleaned not in normalized:
                normalized.append(cleaned)
        return normalized

    def _resolve_tickers(
        self,
        prompt: str,
        explicit_tickers: str | list[str] | None = None,
        fallback_tickers: list[str] | None = None,
    ) -> list[str]:
        if explicit_tickers:
            normalized = self._normalize_tickers(explicit_tickers)
            if normalized:
                return normalized

        inferred = self.infer_tickers_from_prompt(prompt)
        if inferred:
            return inferred

        if self._is_market_context_prompt(prompt):
            return ["SPY"]

        if fallback_tickers and self._is_finance_prompt(prompt):
            return self._normalize_tickers(fallback_tickers)

        return []

    def _is_finance_prompt(self, prompt: str) -> bool:
        lowered = prompt.lower()
        if self.infer_tickers_from_prompt(prompt):
            return True
        return any(keyword in lowered for keyword in self.FINANCE_KEYWORDS)

    def _is_market_context_prompt(self, prompt: str) -> bool:
        lowered = prompt.lower()
        return any(
            phrase in lowered
            for phrase in {
                "market snapshot",
                "stock market",
                "equity market",
                "us market",
                "u.s. market",
                "market risk",
                "analyze the market",
                "analyse the market",
            }
        )
