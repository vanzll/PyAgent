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
            summary_text=(
                f"Answer to: {prompt}\n"
                f"Generated equity research for {', '.join(bundle.tickers)}. "
                "For research use only, not investment advice."
            ),
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


class NaNRunner:
    async def run(self, prompt: str, bundle: ParsedInputBundle, workspace: Path, emit) -> RunResult:
        emit("status", {"message": "nan runner started"})
        artifact_path = workspace / "outputs" / "summary.md"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text("ok", encoding="utf-8")
        return RunResult(
            summary_text="Contains missing values",
            artifacts=[
                ArtifactRecord(
                    name="summary.md",
                    path=artifact_path,
                    content_type="text/markdown",
                    kind="report",
                    label="Summary",
                )
            ],
            snapshot_cards=[
                {
                    "ticker": "SPY",
                    "name": "SPDR S&P 500 ETF Trust",
                    "sector": "ETF",
                    "latest_close": 605.3,
                    "market_cap": float("nan"),
                    "pe_ratio": float("nan"),
                    "latest_revenue": float("nan"),
                    "latest_net_income": float("nan"),
                    "recent_filing_form": "N-CSR",
                    "description": "ETF with missing fundamentals.",
                }
            ],
            preview_tables=[
                {
                    "name": "comparison",
                    "columns": ["ticker", "market_cap"],
                    "rows": [["SPY", float("nan")]],
                }
            ],
        )


class MixedRunner:
    async def run(self, prompt: str, bundle: ParsedInputBundle, workspace: Path, emit) -> RunResult:
        emit("status", {"message": "mixed runner started"})
        if bundle.tickers:
            return RunResult(
                summary_text=f"Financial answer for {', '.join(bundle.tickers)}",
                snapshot_cards=[{"ticker": bundle.tickers[0], "name": bundle.tickers[0], "sector": "Tech"}],
            )
        return RunResult(summary_text="Hello. I can answer general questions and also help with stock research.")


def test_run_service_normalizes_tickers_without_files(tmp_path: Path) -> None:
    service = RunService(storage_root=tmp_path, runner=FakeRunner())
    bundle = service.build_bundle("amd, nvda")

    assert bundle.tickers == ["AMD", "NVDA"]
    assert bundle.dataframes == {}
    assert bundle.pdf_documents == {}


def test_webapp_chat_session_lifecycle_and_artifact_download(tmp_path: Path) -> None:
    service = RunService(storage_root=tmp_path, runner=FakeRunner())
    client = TestClient(create_app(service))

    response = client.get("/")
    assert response.status_code == 200
    assert "Financial Research Agent" in response.text
    assert "Ask the agent with one prompt" in response.text
    assert "Prompt" in response.text
    assert "Tickers" not in response.text
    assert "NUS CS5260" in response.text
    assert "Yahoo Finance" in response.text
    assert "SEC EDGAR" in response.text
    assert "Results" in response.text

    create_session_response = client.post("/api/sessions")
    assert create_session_response.status_code == 201
    session_id = create_session_response.json()["session_id"]

    message_response = client.post(
        f"/api/sessions/{session_id}/messages",
        data={"prompt": "Compare AMD and NVDA on valuation and recent performance"},
    )
    assert message_response.status_code == 202
    run_id = message_response.json()["run_id"]

    result = None
    for _ in range(50):
        result_response = client.get(f"/api/sessions/{session_id}")
        assert result_response.status_code == 200
        result = result_response.json()
        if result["status"] == "completed":
            break
        time.sleep(0.01)

    assert result is not None
    assert result["status"] == "completed"
    assert result["tickers"] == ["AMD", "NVDA"]
    assert result["run_id"] == run_id
    assert "research use only" in result["summary_text"].lower()
    assert result["snapshot_cards"][0]["ticker"] == "AMD"
    assert result["artifacts"][0]["name"] == "comparison.csv"
    assert result["messages"][0]["role"] == "user"
    assert result["messages"][0]["content"] == "Compare AMD and NVDA on valuation and recent performance"
    assert result["messages"][1]["role"] == "assistant"
    assert "Compare AMD and NVDA on valuation and recent performance" in result["messages"][1]["content"]
    assert result["preview_charts"][0]["url"].endswith(f"/api/runs/{run_id}/artifacts/normalized-returns.png")

    download_response = client.get(f"/api/runs/{run_id}/artifacts/comparison.csv")
    assert download_response.status_code == 200
    assert "ticker,latest_close" in download_response.text


def test_webapp_homepage_defaults_to_public_data_mode_without_alpha_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("WEBAPP_DEMO_MODE", raising=False)
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)
    monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)

    service = RunService(storage_root=tmp_path, runner=FakeRunner())
    client = TestClient(create_app(service))

    response = client.get("/")

    assert response.status_code == 200
    assert "Public Data Mode" in response.text
    assert "Demo mode" not in response.text


def test_webapp_preserves_multi_turn_session_context(tmp_path: Path) -> None:
    service = RunService(storage_root=tmp_path, runner=FakeRunner())
    client = TestClient(create_app(service))

    session_id = client.post("/api/sessions").json()["session_id"]
    first_run_id = client.post(
        f"/api/sessions/{session_id}/messages",
        data={"prompt": "Summarize AMD and NVDA"},
    ).json()["run_id"]

    for _ in range(50):
        payload = client.get(f"/api/sessions/{session_id}").json()
        if payload["status"] == "completed":
            break
        time.sleep(0.01)

    second_run_id = client.post(
        f"/api/sessions/{session_id}/messages",
        data={"prompt": "Now focus on the key valuation difference"},
    ).json()["run_id"]

    final_payload = None
    for _ in range(50):
        final_payload = client.get(f"/api/sessions/{session_id}").json()
        if final_payload["status"] == "completed" and final_payload["run_id"] == second_run_id:
            break
        time.sleep(0.01)

    assert final_payload is not None
    assert final_payload["tickers"] == ["AMD", "NVDA"]
    assert len(final_payload["messages"]) == 4
    assert final_payload["messages"][2]["role"] == "user"
    assert final_payload["messages"][2]["content"] == "Now focus on the key valuation difference"
    assert final_payload["messages"][3]["role"] == "assistant"
    assert "Now focus on the key valuation difference" in final_payload["messages"][3]["content"]
    assert final_payload["run_id"] == second_run_id
    assert first_run_id != second_run_id


def test_webapp_streams_session_sse_events(tmp_path: Path) -> None:
    service = RunService(storage_root=tmp_path, runner=FakeRunner())
    client = TestClient(create_app(service))

    session_id = client.post("/api/sessions").json()["session_id"]
    client.post(
        f"/api/sessions/{session_id}/messages",
        data={"prompt": "Summarize AMD and NVDA"},
    )

    with client.stream("GET", f"/api/sessions/{session_id}/events") as response:
        body = "".join(
            line.decode("utf-8") if isinstance(line, bytes) else line
            for line in response.iter_lines()
        )

    assert 'event: sessiondata: {"message": "Session created", "status": "idle"}' in body
    assert 'event: userdata: {"role": "user", "content": "Summarize AMD and NVDA"}' in body
    assert 'event: artifactdata: {"name": "comparison.csv", "run_id": "' in body
    assert 'event: completeddata: {"status": "completed", "run_id": "' in body


def test_run_service_infers_tickers_from_prompt_and_market_aliases(tmp_path: Path) -> None:
    service = RunService(storage_root=tmp_path, runner=FakeRunner())

    inferred = service.build_bundle("", [])
    assert inferred.tickers == []

    assert service.infer_tickers_from_prompt("Compare AMD and NVDA on valuation") == ["AMD", "NVDA"]
    assert service.infer_tickers_from_prompt("Give me a quick view of Apple and Tesla") == ["AAPL", "TSLA"]
    assert service.infer_tickers_from_prompt("What are the key risks in the current US equity market?") == ["SPY"]


def test_webapp_session_endpoint_sanitizes_nan_values(tmp_path: Path) -> None:
    service = RunService(storage_root=tmp_path, runner=NaNRunner())
    client = TestClient(create_app(service))

    session_id = client.post("/api/sessions").json()["session_id"]
    run_id = client.post(
        f"/api/sessions/{session_id}/messages",
        data={"prompt": "Give me a market snapshot for the US equity market."},
    ).json()["run_id"]

    payload = None
    for _ in range(50):
        response = client.get(f"/api/sessions/{session_id}")
        if response.status_code == 200:
            payload = response.json()
            if payload["status"] == "completed" and payload["run_id"] == run_id:
                break
        time.sleep(0.01)

    assert payload is not None
    assert payload["status"] == "completed"
    assert payload["snapshot_cards"][0]["market_cap"] is None
    assert payload["snapshot_cards"][0]["pe_ratio"] is None
    assert payload["preview_tables"][0]["rows"][0][1] is None


def test_webapp_returns_prompt_inference_error_as_bad_request(tmp_path: Path) -> None:
    service = RunService(storage_root=tmp_path, runner=FakeRunner())
    client = TestClient(create_app(service))

    session_id = client.post("/api/sessions").json()["session_id"]
    response = client.post(
        f"/api/sessions/{session_id}/messages",
        data={"prompt": "Analyze company valuation and earnings."},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Could not infer a company, ETF, or market proxy from the prompt."


def test_webapp_generic_chat_prompt_succeeds_without_finance_target(tmp_path: Path) -> None:
    service = RunService(storage_root=tmp_path, runner=MixedRunner())
    client = TestClient(create_app(service))

    session_id = client.post("/api/sessions").json()["session_id"]
    response = client.post(
        f"/api/sessions/{session_id}/messages",
        data={"prompt": "hello"},
    )

    assert response.status_code == 202

    payload = None
    for _ in range(50):
        payload = client.get(f"/api/sessions/{session_id}").json()
        if payload["status"] == "completed":
            break
        time.sleep(0.01)

    assert payload is not None
    assert payload["status"] == "completed"
    assert payload["messages"][0]["content"] == "hello"
    assert payload["messages"][0]["tickers"] == []
    assert payload["messages"][1]["role"] == "assistant"
    assert "general questions" in payload["messages"][1]["content"].lower()
    assert payload["messages"][1]["tickers"] == []


def test_webapp_generic_chat_does_not_inherit_previous_finance_tickers(tmp_path: Path) -> None:
    service = RunService(storage_root=tmp_path, runner=MixedRunner())
    client = TestClient(create_app(service))

    session_id = client.post("/api/sessions").json()["session_id"]
    first_run_id = client.post(
        f"/api/sessions/{session_id}/messages",
        data={"prompt": "Compare AMD and NVDA on valuation"},
    ).json()["run_id"]

    for _ in range(50):
        payload = client.get(f"/api/sessions/{session_id}").json()
        if payload["status"] == "completed" and payload["run_id"] == first_run_id:
            break
        time.sleep(0.01)

    second_run_id = client.post(
        f"/api/sessions/{session_id}/messages",
        data={"prompt": "hello"},
    ).json()["run_id"]

    final_payload = None
    for _ in range(50):
        final_payload = client.get(f"/api/sessions/{session_id}").json()
        if final_payload["status"] == "completed" and final_payload["run_id"] == second_run_id:
            break
        time.sleep(0.01)

    assert final_payload is not None
    assert final_payload["status"] == "completed"
    assert final_payload["tickers"] == ["AMD", "NVDA"]
    assert final_payload["messages"][2]["content"] == "hello"
    assert final_payload["messages"][2]["tickers"] == []
    assert final_payload["messages"][3]["tickers"] == []
