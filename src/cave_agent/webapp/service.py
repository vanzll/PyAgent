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

from .models import ArtifactRecord, InputFileRecord, RunEvent, RunRecord, RunResult


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
    def __init__(self, storage_root: Path, runner: RunnerProtocol):
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.runner = runner
        self._runs: dict[str, RunRecord] = {}

    async def create_run(self, prompt: str, tickers: str, files: list[UploadFile] | None = None) -> RunRecord:
        run_id = uuid4().hex[:12]
        workspace = self.storage_root / run_id
        uploads_dir = workspace / "uploads"
        outputs_dir = workspace / "outputs"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir.mkdir(parents=True, exist_ok=True)

        normalized_tickers = self._normalize_tickers(tickers)
        record = RunRecord(run_id=run_id, prompt=prompt, workspace=workspace, tickers=normalized_tickers)
        self._runs[run_id] = record

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

        record.input_files = saved_files
        self._append_event(record, "status", {"message": "Run created", "status": "pending"})
        asyncio.create_task(self._execute_run(record, saved_files))
        return record

    def get_run(self, run_id: str) -> RunRecord:
        if run_id not in self._runs:
            raise KeyError(run_id)
        return self._runs[run_id]

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

    async def stream_events(self, run_id: str):
        record = self.get_run(run_id)
        index = 0
        while True:
            while index < len(record.events):
                event = record.events[index]
                payload = json.dumps(event.data, ensure_ascii=False)
                yield f"event: {event.event}\ndata: {payload}\n\n"
                index += 1
            if record.status in {"completed", "failed"} and index >= len(record.events):
                break
            await asyncio.sleep(0.05)

    async def _execute_run(self, record: RunRecord, saved_files: list[InputFileRecord]) -> None:
        try:
            record.status = "parsing"
            self._append_event(record, "status", {"message": "Preparing research inputs", "status": "parsing"})
            bundle = self._parse_file_records(saved_files) if saved_files else ParsedInputBundle()
            bundle.tickers = list(record.tickers)
            record.input_files = bundle.input_files

            record.status = "running"
            self._append_event(record, "status", {"message": "Running financial research agent", "status": "running"})
            result = await self.runner.run(record.prompt, bundle, record.workspace, lambda event, data: self._append_event(record, event, data))

            record.summary_text = result.summary_text
            record.artifacts = result.artifacts
            record.snapshot_cards = result.snapshot_cards
            record.preview_tables = result.preview_tables
            record.preview_charts = result.preview_charts
            record.status = "completed"
            self._append_event(record, "completed", {"status": "completed"})
        except Exception as exc:
            record.status = "failed"
            record.error_message = str(exc)
            self._append_event(record, "failed", {"status": "failed", "message": record.error_message})

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

    def _append_event(self, record: RunRecord, event: str, data: dict[str, Any]) -> None:
        record.events.append(RunEvent(event=event, data=data))

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
