from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ArtifactRecord:
    name: str
    path: Path
    content_type: str
    kind: str
    label: str

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "content_type": self.content_type,
            "kind": self.kind,
            "label": self.label,
        }


@dataclass
class InputFileRecord:
    name: str
    media_type: str
    saved_path: Path
    kind: str

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "media_type": self.media_type,
            "kind": self.kind,
        }


@dataclass
class RunResult:
    summary_text: str
    artifacts: list[ArtifactRecord] = field(default_factory=list)
    snapshot_cards: list[dict[str, Any]] = field(default_factory=list)
    preview_tables: list[dict[str, Any]] = field(default_factory=list)
    preview_charts: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class RunEvent:
    event: str
    data: dict[str, Any]


@dataclass
class RunRecord:
    run_id: str
    prompt: str
    workspace: Path
    tickers: list[str] = field(default_factory=list)
    status: str = "pending"
    input_files: list[InputFileRecord] = field(default_factory=list)
    artifacts: list[ArtifactRecord] = field(default_factory=list)
    summary_text: str = ""
    preview_tables: list[dict[str, Any]] = field(default_factory=list)
    preview_charts: list[dict[str, Any]] = field(default_factory=list)
    snapshot_cards: list[dict[str, Any]] = field(default_factory=list)
    error_message: str | None = None
    events: list[RunEvent] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        preview_charts = []
        for chart in self.preview_charts:
            hydrated = dict(chart)
            if "name" in hydrated and "url" not in hydrated:
                hydrated["url"] = f"/api/runs/{self.run_id}/artifacts/{hydrated['name']}"
            preview_charts.append(hydrated)

        return {
            "run_id": self.run_id,
            "status": self.status,
            "prompt": self.prompt,
            "tickers": self.tickers,
            "input_files": [record.to_dict() for record in self.input_files],
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "summary_text": self.summary_text,
            "snapshot_cards": self.snapshot_cards,
            "preview_tables": self.preview_tables,
            "preview_charts": preview_charts,
            "error_message": self.error_message,
        }
