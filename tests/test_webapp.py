from __future__ import annotations

import time
from pathlib import Path

from fastapi.testclient import TestClient
from cave_agent.webapp.app import create_app
from cave_agent.webapp.models import ArtifactRecord, RunResult
from cave_agent.webapp.service import ParsedInputBundle, RunService


class FakeRunner:
    async def run(self, prompt: str, bundle: ParsedInputBundle, workspace: Path, emit) -> RunResult:
        emit("status", {"message": "fake runner started"})
        assert bundle.tickers == ["AMD", "NVDA"]
        artifact_path = workspace / "outputs" / "comparison.csv"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text("ticker,latest_close\nAMD,100\nNVDA,120\n", encoding="utf-8")
        chart_path = workspace / "outputs" / "normalized-returns.png"
        chart_path.write_bytes(
            bytes.fromhex(
                "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C489"
                "0000000D49444154789C6360606060000000040001F61738550000000049454E44AE426082"
            )
        )
        emit("artifact", {"name": artifact_path.name})
        return RunResult(
            summary_text=f"Generated equity research for {', '.join(bundle.tickers)}. For research use only, not investment advice.",
            artifacts=[
                ArtifactRecord(
                    name="comparison.csv",
                    path=artifact_path,
                    content_type="text/csv",
                    kind="table",
                    label="Peer Comparison",
                ),
                ArtifactRecord(
                    name="normalized-returns.png",
                    path=chart_path,
                    content_type="image/png",
                    kind="chart",
                    label="Relative Returns",
                ),
            ],
            snapshot_cards=[
                {
                    "ticker": "AMD",
                    "name": "Advanced Micro Devices, Inc.",
                    "sector": "Semiconductors",
                    "latest_close": 100.0,
                    "market_cap": 265000000000.0,
                    "pe_ratio": 43.2,
                    "latest_revenue": 7120000000.0,
                    "latest_net_income": 921000000.0,
                    "recent_filing_form": "10-Q",
                    "recent_filing_date": "2026-01-30",
                    "description": "CPU and GPU designer.",
                },
                {
                    "ticker": "NVDA",
                    "name": "NVIDIA Corporation",
                    "sector": "Semiconductors",
                    "latest_close": 120.0,
                    "market_cap": 3660000000000.0,
                    "pe_ratio": 46.8,
                    "latest_revenue": 39000000000.0,
                    "latest_net_income": 22100000000.0,
                    "recent_filing_form": "10-Q",
                    "recent_filing_date": "2026-02-14",
                    "description": "AI infrastructure leader.",
                },
            ],
            preview_tables=[
                {
                    "name": "peer-comparison",
                    "columns": ["ticker", "latest_close"],
                    "rows": [["AMD", 100], ["NVDA", 120]],
                }
            ],
            preview_charts=[
                {
                    "name": "normalized-returns.png",
                    "label": "Relative Returns",
                }
            ],
        )


def test_run_service_normalizes_tickers_without_files(tmp_path: Path) -> None:
    service = RunService(storage_root=tmp_path, runner=FakeRunner())
    bundle = service.build_bundle("amd, nvda")

    assert bundle.tickers == ["AMD", "NVDA"]
    assert bundle.dataframes == {}
    assert bundle.pdf_documents == {}


def test_webapp_run_lifecycle_and_artifact_download(tmp_path: Path) -> None:
    service = RunService(storage_root=tmp_path, runner=FakeRunner())
    client = TestClient(create_app(service))

    response = client.get("/")
    assert response.status_code == 200
    assert "Financial Research Agent" in response.text
    assert "Demo mode" in response.text
    assert "NUS CS5260" in response.text
    assert "Alpha Vantage" in response.text
    assert "SEC EDGAR" in response.text
    assert "SGD 0 in demo mode" in response.text

    create_response = client.post(
        "/api/runs",
        data={"prompt": "Compare valuation and recent performance", "tickers": "AMD, NVDA"},
    )
    assert create_response.status_code == 202
    run_id = create_response.json()["run_id"]

    result = None
    for _ in range(50):
        result_response = client.get(f"/api/runs/{run_id}")
        assert result_response.status_code == 200
        result = result_response.json()
        if result["status"] == "completed":
            break
        time.sleep(0.01)

    assert result is not None
    assert result["status"] == "completed"
    assert result["tickers"] == ["AMD", "NVDA"]
    assert "research use only" in result["summary_text"].lower()
    assert result["snapshot_cards"][0]["ticker"] == "AMD"
    assert result["artifacts"][0]["name"] == "comparison.csv"
    assert result["preview_charts"][0]["url"].endswith(f"/api/runs/{run_id}/artifacts/normalized-returns.png")

    download_response = client.get(f"/api/runs/{run_id}/artifacts/comparison.csv")
    assert download_response.status_code == 200
    assert "ticker,latest_close" in download_response.text


def test_webapp_streams_sse_events(tmp_path: Path) -> None:
    service = RunService(storage_root=tmp_path, runner=FakeRunner())
    client = TestClient(create_app(service))

    create_response = client.post(
        "/api/runs",
        data={"prompt": "Summarize AMD and NVDA", "tickers": "AMD, NVDA"},
    )
    run_id = create_response.json()["run_id"]

    with client.stream("GET", f"/api/runs/{run_id}/events") as response:
        body = "".join(
            line.decode("utf-8") if isinstance(line, bytes) else line
            for line in response.iter_lines()
        )

    assert 'event: statusdata: {"message": "Run created", "status": "pending"}' in body
    assert 'event: artifactdata: {"name": "comparison.csv"}' in body
    assert 'event: completeddata: {"status": "completed"}' in body
