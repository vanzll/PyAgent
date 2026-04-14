from __future__ import annotations

import asyncio

import httpx
import pandas as pd
import pytest

import cave_agent.webapp.agent_runner as agent_runner_module
from cave_agent.webapp.financial_data import (
    AlphaVantageClient,
    DemoFinancialDataProvider,
    FinancialDataProvider,
    FredClient,
    SecEdgarClient,
)
from cave_agent.webapp.agent_runner import FinancialResearchRunner
from cave_agent.webapp.service import ParsedInputBundle


@pytest.mark.asyncio
async def test_alpha_vantage_client_parses_price_history_and_overview() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        function = request.url.params["function"]
        if function == "TIME_SERIES_DAILY_ADJUSTED":
            return httpx.Response(
                200,
                json={
                    "Meta Data": {"2. Symbol": "AAPL"},
                    "Time Series (Daily)": {
                        "2026-04-10": {
                            "1. open": "190.0",
                            "2. high": "195.0",
                            "3. low": "189.0",
                            "4. close": "194.0",
                            "5. adjusted close": "194.0",
                            "6. volume": "1000",
                        },
                        "2026-04-09": {
                            "1. open": "188.0",
                            "2. high": "191.0",
                            "3. low": "187.0",
                            "4. close": "190.0",
                            "5. adjusted close": "190.0",
                            "6. volume": "900",
                        },
                    },
                },
            )
        if function == "OVERVIEW":
            return httpx.Response(
                200,
                json={
                    "Symbol": "AAPL",
                    "Name": "Apple Inc.",
                    "Sector": "Technology",
                    "MarketCapitalization": "3000000000000",
                    "PERatio": "31.2",
                    "52WeekHigh": "199.62",
                    "52WeekLow": "164.08",
                    "Description": "Apple designs consumer electronics.",
                },
            )
        raise AssertionError(f"Unexpected function: {function}")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://www.alphavantage.co") as client:
        alpha = AlphaVantageClient(api_key="demo", http_client=client)
        snapshot = await alpha.fetch_security_snapshot("AAPL")

    assert snapshot["ticker"] == "AAPL"
    assert snapshot["profile"]["name"] == "Apple Inc."
    assert snapshot["market_snapshot"]["latest_close"] == 194.0
    assert list(snapshot["price_history"].columns) == ["date", "open", "high", "low", "close", "adjusted_close", "volume"]


@pytest.mark.asyncio
async def test_sec_client_parses_companyfacts_and_submissions() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url.endswith("/company_tickers.json"):
            return httpx.Response(
                200,
                json={"0": {"ticker": "AAPL", "cik_str": 320193, "title": "Apple Inc."}},
            )
        if url.endswith("/submissions/CIK0000320193.json"):
            return httpx.Response(
                200,
                json={
                    "filings": {
                        "recent": {
                            "form": ["10-Q", "10-K"],
                            "filingDate": ["2026-02-01", "2025-11-01"],
                            "accessionNumber": ["0000320193-26-000001", "0000320193-25-000111"],
                            "primaryDocument": ["aapl-20260201x10q.htm", "aapl-20251101x10k.htm"],
                        }
                    }
                },
            )
        if url.endswith("/api/xbrl/companyfacts/CIK0000320193.json"):
            return httpx.Response(
                200,
                json={
                    "facts": {
                        "us-gaap": {
                            "Revenues": {
                                "units": {
                                    "USD": [
                                        {"fy": 2025, "fp": "Q1", "form": "10-Q", "end": "2025-12-31", "val": 124300000000},
                                        {"fy": 2024, "fp": "FY", "form": "10-K", "end": "2024-09-28", "val": 391000000000},
                                    ]
                                }
                            },
                            "NetIncomeLoss": {
                                "units": {
                                    "USD": [
                                        {"fy": 2025, "fp": "Q1", "form": "10-Q", "end": "2025-12-31", "val": 36330000000}
                                    ]
                                }
                            },
                        }
                    }
                },
            )
        raise AssertionError(f"Unexpected URL: {url}")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://data.sec.gov") as client:
        sec = SecEdgarClient(http_client=client, user_agent="cave-agent-tests")
        profile = await sec.fetch_company_profile("AAPL")

    assert profile["ticker"] == "AAPL"
    assert profile["cik"] == "0000320193"
    assert profile["company_name"] == "Apple Inc."
    assert profile["recent_filings"][0]["form"] == "10-Q"
    assert profile["company_facts"]["latest_revenue"] == 124300000000
    assert profile["company_facts"]["latest_net_income"] == 36330000000


@pytest.mark.asyncio
async def test_sec_client_tolerates_missing_companyfacts() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url.endswith("/company_tickers.json"):
            return httpx.Response(
                200,
                json={"0": {"ticker": "SPY", "cik_str": 884394, "title": "SPDR S&P 500 ETF TRUST"}},
            )
        if url.endswith("/submissions/CIK0000884394.json"):
            return httpx.Response(
                200,
                json={
                    "filings": {
                        "recent": {
                            "form": ["10-K"],
                            "filingDate": ["2026-01-31"],
                            "accessionNumber": ["0000884394-26-000001"],
                            "primaryDocument": ["spy-20260131x10k.htm"],
                        }
                    }
                },
            )
        if url.endswith("/api/xbrl/companyfacts/CIK0000884394.json"):
            return httpx.Response(404, json={"detail": "Not found"})
        raise AssertionError(f"Unexpected URL: {url}")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://data.sec.gov") as client:
        sec = SecEdgarClient(http_client=client, user_agent="cave-agent-tests")
        profile = await sec.fetch_company_profile("SPY")

    assert profile["ticker"] == "SPY"
    assert profile["company_name"] == "SPDR S&P 500 ETF TRUST"
    assert profile["recent_filings"][0]["form"] == "10-K"
    assert profile["company_facts"] == {"latest_revenue": None, "latest_net_income": None}


@pytest.mark.asyncio
async def test_financial_data_provider_builds_comparison_frame_without_macro_key() -> None:
    class FakeAlpha:
        async def fetch_security_snapshot(self, ticker: str):
            return {
                "ticker": ticker,
                "profile": {"name": f"{ticker} Corp", "sector": "Technology", "description": f"{ticker} description"},
                "market_snapshot": {
                    "latest_close": 100.0 if ticker == "AMD" else 120.0,
                    "market_cap": 1000000 if ticker == "AMD" else 1500000,
                    "pe_ratio": 25.0 if ticker == "AMD" else 30.0,
                    "week_52_high": 150.0,
                    "week_52_low": 80.0,
                },
                "price_history": __import__("pandas").DataFrame(
                    [
                        {"date": "2026-04-09", "open": 95.0, "high": 101.0, "low": 94.0, "close": 100.0, "adjusted_close": 100.0, "volume": 1000},
                        {"date": "2026-04-10", "open": 100.0, "high": 121.0, "low": 99.0, "close": 120.0 if ticker == "NVDA" else 101.0, "adjusted_close": 120.0 if ticker == "NVDA" else 101.0, "volume": 1200},
                    ]
                ),
                "news_items": [],
            }

    class FakeSec:
        async def fetch_company_profile(self, ticker: str):
            return {
                "ticker": ticker,
                "company_name": f"{ticker} Corp",
                "cik": f"0000{ticker}",
                "recent_filings": [{"form": "10-Q", "filing_date": "2026-02-01"}],
                "company_facts": {"latest_revenue": 1000, "latest_net_income": 200},
            }

    class FakeFred:
        async def fetch_default_macro_series(self):
            return {}

    provider = FinancialDataProvider(alpha_vantage=FakeAlpha(), sec_edgar=FakeSec(), fred=FakeFred())
    bundle = await provider.build_bundle(["AMD", "NVDA"], "Compare AMD and NVDA")

    assert bundle["tickers"] == ["AMD", "NVDA"]
    assert list(bundle["comparison_frame"]["ticker"]) == ["AMD", "NVDA"]
    assert "AMD" in bundle["price_history"]
    assert bundle["macro_series"] == {}


@pytest.mark.asyncio
async def test_demo_financial_data_provider_returns_stable_bundle() -> None:
    provider = DemoFinancialDataProvider()
    bundle = await provider.build_bundle(["AAPL", "SPY"], "Demo this app")

    assert bundle["demo_mode"] is True
    assert bundle["tickers"] == ["AAPL", "SPY"]
    assert list(bundle["comparison_frame"]["ticker"]) == ["AAPL", "SPY"]
    assert bundle["price_history"]["AAPL"].iloc[-1]["adjusted_close"] > 0
    assert "FEDFUNDS" in bundle["macro_series"]


@pytest.mark.asyncio
async def test_financial_research_runner_uses_deterministic_demo_without_model(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("LLM_MODEL_ID", raising=False)
    monkeypatch.setenv("WEBAPP_DEMO_MODE", "1")

    runner = FinancialResearchRunner(provider=DemoFinancialDataProvider())
    result = await runner.run(
        "Compare AMD and NVDA",
        ParsedInputBundle(tickers=["AMD", "NVDA"]),
        tmp_path,
        lambda *_args, **_kwargs: None,
    )

    assert "For research use only. Not investment advice." in result.summary_text
    assert any(artifact.name == "comparison.csv" for artifact in result.artifacts)
    assert any(card["ticker"] == "AMD" for card in result.snapshot_cards)
    assert any(chart["name"] == "normalized-returns.png" for chart in result.preview_charts)


@pytest.mark.asyncio
async def test_alpha_vantage_client_falls_back_when_adjusted_and_overview_are_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        function = request.url.params["function"]
        if function == "TIME_SERIES_DAILY_ADJUSTED":
            return httpx.Response(200, json={"Information": "Adjusted endpoint unavailable"})
        if function == "TIME_SERIES_DAILY":
            return httpx.Response(
                200,
                json={
                    "Time Series (Daily)": {
                        "2026-04-11": {
                            "1. open": "198.0",
                            "2. high": "201.0",
                            "3. low": "197.5",
                            "4. close": "200.0",
                            "6. volume": "1200",
                        },
                        "2026-04-10": {
                            "1. open": "196.0",
                            "2. high": "199.0",
                            "3. low": "195.5",
                            "4. close": "198.0",
                            "6. volume": "1100",
                        },
                    }
                },
            )
        if function == "OVERVIEW":
            return httpx.Response(200, json={"Information": "Overview unavailable"})
        if function == "ETF_PROFILE":
            return httpx.Response(200, json={})
        if function == "GLOBAL_QUOTE":
            return httpx.Response(
                200,
                json={
                    "Global Quote": {
                        "05. price": "200.0",
                        "07. latest trading day": "2026-04-11",
                    }
                },
            )
        raise AssertionError(f"Unexpected function: {function}")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://www.alphavantage.co") as client:
        alpha = AlphaVantageClient(api_key="demo", http_client=client)
        snapshot = await alpha.fetch_security_snapshot("AAPL")

    assert snapshot["market_snapshot"]["latest_close"] == 200.0
    assert not snapshot["price_history"].empty
    assert snapshot["profile"]["name"] == "AAPL"


@pytest.mark.asyncio
async def test_financial_data_provider_uses_sec_company_name_when_alpha_profile_is_sparse() -> None:
    class FakeAlpha:
        async def fetch_security_snapshot(self, ticker: str, include_news: bool = False):
            return {
                "ticker": ticker,
                "profile": {
                    "name": ticker,
                    "sector": "Unknown",
                    "description": "",
                    "market_cap": None,
                    "pe_ratio": None,
                    "week_52_high": None,
                    "week_52_low": None,
                },
                "market_snapshot": {
                    "latest_close": 200.0,
                    "market_cap": None,
                    "pe_ratio": None,
                    "week_52_high": None,
                    "week_52_low": None,
                },
                "price_history": pd.DataFrame(
                    [
                        {"date": "2026-04-10", "open": 198.0, "high": 201.0, "low": 197.0, "close": 200.0, "adjusted_close": 200.0, "volume": 1000}
                    ]
                ),
                "news_items": [],
            }

    class FakeSec:
        async def fetch_company_profile(self, ticker: str):
            return {
                "ticker": ticker,
                "company_name": "Apple Inc.",
                "cik": "0000320193",
                "recent_filings": [{"form": "10-Q", "filing_date": "2026-02-01"}],
                "company_facts": {"latest_revenue": 1000, "latest_net_income": 200},
            }

    provider = FinancialDataProvider(alpha_vantage=FakeAlpha(), sec_edgar=FakeSec(), fred=None)
    bundle = await provider.build_bundle(["AAPL"], "Summarize Apple")

    assert bundle["securities"]["AAPL"]["profile"]["name"] == "Apple Inc."
    assert bundle["comparison_frame"].iloc[0]["name"] == "Apple Inc."


@pytest.mark.asyncio
async def test_financial_data_provider_uses_secondary_market_source_when_alpha_is_sparse() -> None:
    class FakeAlpha:
        async def fetch_security_snapshot(self, ticker: str, include_news: bool = False):
            return {
                "ticker": ticker,
                "profile": {
                    "name": ticker,
                    "sector": "Unknown",
                    "description": "",
                    "market_cap": None,
                    "pe_ratio": None,
                    "week_52_high": None,
                    "week_52_low": None,
                },
                "market_snapshot": {
                    "latest_close": None,
                    "market_cap": None,
                    "pe_ratio": None,
                    "week_52_high": None,
                    "week_52_low": None,
                },
                "price_history": pd.DataFrame(columns=["date", "open", "high", "low", "close", "adjusted_close", "volume"]),
                "news_items": [],
            }

    class FakeYahoo:
        async def fetch_security_snapshot(self, ticker: str):
            return {
                "ticker": ticker,
                "profile": {
                    "name": "Apple Inc.",
                    "sector": "Technology",
                    "description": "Devices and services company.",
                    "market_cap": 3000000000000.0,
                    "pe_ratio": 31.2,
                    "week_52_high": 205.0,
                    "week_52_low": 164.0,
                },
                "market_snapshot": {
                    "latest_close": 200.0,
                    "market_cap": 3000000000000.0,
                    "pe_ratio": 31.2,
                    "week_52_high": 205.0,
                    "week_52_low": 164.0,
                },
                "price_history": pd.DataFrame(
                    [
                        {"date": "2026-04-10", "open": 198.0, "high": 201.0, "low": 197.0, "close": 200.0, "adjusted_close": 200.0, "volume": 1000}
                    ]
                ),
                "news_items": [],
            }

    class FakeSec:
        async def fetch_company_profile(self, ticker: str):
            return {
                "ticker": ticker,
                "company_name": "Apple Inc.",
                "cik": "0000320193",
                "recent_filings": [{"form": "10-Q", "filing_date": "2026-02-01"}],
                "company_facts": {"latest_revenue": 1000, "latest_net_income": 200},
            }

    provider = FinancialDataProvider(alpha_vantage=FakeAlpha(), sec_edgar=FakeSec(), fred=None, yahoo=FakeYahoo())
    bundle = await provider.build_bundle(["AAPL"], "Summarize Apple")

    security = bundle["securities"]["AAPL"]
    assert security["market_snapshot"]["latest_close"] == 200.0
    assert not bundle["price_history"]["AAPL"].empty
    assert security["profile"]["sector"] == "Technology"


@pytest.mark.asyncio
async def test_financial_research_runner_falls_back_when_agent_times_out(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("WEBAPP_DEMO_MODE", "1")
    monkeypatch.setenv("LLM_MODEL_ID", "gpt-5.4")
    monkeypatch.setenv("WEBAPP_AGENT_TIMEOUT_SECONDS", "0.01")
    monkeypatch.setattr(FinancialResearchRunner, "_build_model", lambda self: object())

    class HangingAgent:
        def __init__(self, *args, **kwargs):
            pass

        async def run(self, *_args, **_kwargs):
            await asyncio.sleep(0.2)

    monkeypatch.setattr(agent_runner_module, "CaveAgent", HangingAgent)

    events = []
    runner = FinancialResearchRunner(provider=DemoFinancialDataProvider())
    result = await runner.run(
        "Give me a market snapshot for the US equity market.",
        ParsedInputBundle(tickers=["SPY"]),
        tmp_path,
        lambda event, data: events.append((event, data)),
    )

    assert "For research use only. Not investment advice." in result.summary_text
    assert any(artifact.name == "summary.md" for artifact in result.artifacts)
    assert any("fallback summary" in data.get("message", "") for event, data in events if event == "status")


def test_financial_research_runner_demo_summary_tolerates_missing_numeric_values() -> None:
    runner = FinancialResearchRunner(provider=DemoFinancialDataProvider())
    summary = runner._build_demo_summary(
        {
            "comparison_frame": __import__("pandas").DataFrame(
                [
                    {
                        "ticker": "SPY",
                        "latest_close": None,
                        "market_cap": None,
                        "pe_ratio": None,
                        "latest_revenue": None,
                    }
                ]
            )
        },
        "Give me a market snapshot.",
    )

    assert "latest close n/a" in summary
    assert "market cap n/a" in summary
    assert "P/E n/a" in summary


@pytest.mark.asyncio
async def test_financial_research_runner_timeout_clears_partial_outputs(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("WEBAPP_DEMO_MODE", "1")
    monkeypatch.setenv("LLM_MODEL_ID", "gpt-5.4")
    monkeypatch.setenv("WEBAPP_AGENT_TIMEOUT_SECONDS", "0.01")
    monkeypatch.setattr(FinancialResearchRunner, "_build_model", lambda self: object())

    class HangingAgent:
        def __init__(self, *args, **kwargs):
            self.runtime = kwargs["runtime"]

        async def run(self, *_args, **_kwargs):
            workspace = await self.runtime.retrieve("workspace")
            workspace.save_dataframe(pd.DataFrame([{"x": 1}]), "partial", format="csv")
            await asyncio.sleep(0.2)

    monkeypatch.setattr(agent_runner_module, "CaveAgent", HangingAgent)

    runner = FinancialResearchRunner(provider=DemoFinancialDataProvider())
    result = await runner.run(
        "Compare AMD and NVDA",
        ParsedInputBundle(tickers=["AMD", "NVDA"]),
        tmp_path,
        lambda *_args, **_kwargs: None,
    )

    artifact_names = sorted(artifact.name for artifact in result.artifacts)
    assert artifact_names == ["comparison.csv", "normalized-returns.png", "summary.md"]
