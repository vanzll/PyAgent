from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any

import httpx
import pandas as pd


class AlphaVantageClient:
    def __init__(
        self,
        api_key: str | None = None,
        http_client: httpx.AsyncClient | None = None,
        base_url: str = "https://www.alphavantage.co/query",
    ):
        self.api_key = api_key or os.getenv("ALPHAVANTAGE_API_KEY") or os.getenv("ALPHA_VANTAGE_API_KEY")
        self.base_url = base_url
        self.http_client = http_client

    async def fetch_security_snapshot(self, ticker: str, include_news: bool = False) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("ALPHAVANTAGE_API_KEY is required for market data.")

        async with self._client() as client:
            daily_payload, overview_payload = await self._fetch_core_payloads(client, ticker)
            news_items = []
            if include_news:
                try:
                    news_items = await self._fetch_news(client, ticker)
                except Exception:
                    news_items = []

        price_history = self._parse_price_history(daily_payload)
        profile = self._normalize_overview(overview_payload, ticker)
        market_snapshot = self._build_market_snapshot(profile, price_history)
        return {
            "ticker": ticker,
            "profile": profile,
            "market_snapshot": market_snapshot,
            "price_history": price_history,
            "news_items": news_items,
        }

    async def _fetch_core_payloads(self, client: httpx.AsyncClient, ticker: str) -> tuple[dict[str, Any], dict[str, Any]]:
        daily_task = self._request(
            client,
            "TIME_SERIES_DAILY_ADJUSTED",
            symbol=ticker,
            outputsize="compact",
            allow_api_notice=True,
        )
        overview_task = self._request(client, "OVERVIEW", symbol=ticker, allow_api_notice=True)
        daily_payload, overview_payload = await daily_task, await overview_task
        if not self._has_price_history(daily_payload):
            fallback_daily = await self._request(
                client,
                "TIME_SERIES_DAILY",
                symbol=ticker,
                outputsize="compact",
                allow_api_notice=True,
            )
            if self._has_price_history(fallback_daily):
                daily_payload = fallback_daily
            else:
                daily_payload = await self._request(client, "GLOBAL_QUOTE", symbol=ticker, allow_api_notice=True)

        if not self._has_company_overview(overview_payload):
            overview_payload = await self._request(client, "ETF_PROFILE", symbol=ticker, allow_api_notice=True)
        return daily_payload, overview_payload

    async def _fetch_news(self, client: httpx.AsyncClient, ticker: str) -> list[dict[str, Any]]:
        payload = await self._request(client, "NEWS_SENTIMENT", tickers=ticker, limit="5", sort="LATEST")
        feed = payload.get("feed", []) if isinstance(payload, dict) else []
        return [
            {
                "title": item.get("title", ""),
                "summary": item.get("summary", ""),
                "url": item.get("url", ""),
                "published_at": item.get("time_published", ""),
                "sentiment_score": item.get("overall_sentiment_score"),
            }
            for item in feed
        ]

    async def _request(self, client: httpx.AsyncClient, function: str, allow_api_notice: bool = False, **params) -> dict[str, Any]:
        response = await client.get(
            self.base_url,
            params={"function": function, "apikey": self.api_key, **params},
        )
        response.raise_for_status()
        payload = response.json()
        if "Error Message" in payload:
            raise RuntimeError(payload["Error Message"])
        if "Note" in payload and not allow_api_notice:
            raise RuntimeError(payload["Note"])
        if ("Note" in payload or "Information" in payload) and allow_api_notice:
            return {}
        if "Information" in payload:
            raise RuntimeError(payload["Information"])
        return payload

    def _parse_price_history(self, payload: dict[str, Any]) -> pd.DataFrame:
        quote = payload.get("Global Quote", {})
        if quote:
            price = self._to_float(quote.get("05. price"))
            if price is not None:
                return pd.DataFrame(
                    [
                        {
                            "date": quote.get("07. latest trading day") or "",
                            "open": price,
                            "high": price,
                            "low": price,
                            "close": price,
                            "adjusted_close": price,
                            "volume": self._to_float(quote.get("06. volume")) or 0.0,
                        }
                    ]
                )

        series = payload.get("Time Series (Daily)", {})
        rows = []
        for date, values in series.items():
            rows.append(
                {
                    "date": date,
                    "open": float(values.get("1. open", 0.0)),
                    "high": float(values.get("2. high", 0.0)),
                    "low": float(values.get("3. low", 0.0)),
                    "close": float(values.get("4. close", 0.0)),
                    "adjusted_close": float(values.get("5. adjusted close", values.get("4. close", 0.0))),
                    "volume": float(values.get("6. volume", 0.0)),
                }
            )
        frame = pd.DataFrame(rows)
        if frame.empty:
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "adjusted_close", "volume"])
        frame = frame.sort_values("date").reset_index(drop=True)
        return frame[["date", "open", "high", "low", "close", "adjusted_close", "volume"]]

    def _normalize_overview(self, payload: dict[str, Any], ticker: str) -> dict[str, Any]:
        return {
            "ticker": ticker,
            "name": payload.get("Name") or payload.get("name") or ticker,
            "sector": payload.get("Sector") or payload.get("AssetClass") or "Unknown",
            "description": payload.get("Description") or payload.get("description") or "",
            "market_cap": self._to_float(payload.get("MarketCapitalization")),
            "pe_ratio": self._to_float(payload.get("PERatio")),
            "week_52_high": self._to_float(payload.get("52WeekHigh")),
            "week_52_low": self._to_float(payload.get("52WeekLow")),
        }

    def _has_price_history(self, payload: dict[str, Any]) -> bool:
        return bool(payload.get("Time Series (Daily)") or payload.get("Global Quote"))

    def _has_company_overview(self, payload: dict[str, Any]) -> bool:
        return bool(payload.get("Symbol") or payload.get("Name") or payload.get("name"))

    def _build_market_snapshot(self, profile: dict[str, Any], price_history: pd.DataFrame) -> dict[str, Any]:
        latest_close = None
        if not price_history.empty:
            latest_close = float(price_history.iloc[-1]["adjusted_close"])
        return {
            "latest_close": latest_close,
            "market_cap": profile.get("market_cap"),
            "pe_ratio": profile.get("pe_ratio"),
            "week_52_high": profile.get("week_52_high"),
            "week_52_low": profile.get("week_52_low"),
        }

    def _to_float(self, value: Any) -> float | None:
        if value in (None, "", "None"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _client(self):
        if self.http_client is not None:
            return _BorrowedAsyncClient(self.http_client)
        return httpx.AsyncClient(timeout=20.0)


class SecEdgarClient:
    def __init__(
        self,
        http_client: httpx.AsyncClient | None = None,
        user_agent: str | None = None,
        data_base_url: str = "https://data.sec.gov",
        ticker_lookup_url: str | None = None,
    ):
        self.http_client = http_client
        self.user_agent = user_agent or os.getenv("SEC_USER_AGENT") or "pycallingagent-finance/0.1 research@example.com"
        self.data_base_url = data_base_url.rstrip("/")
        if ticker_lookup_url:
            self.ticker_lookup_url = ticker_lookup_url
        elif http_client is not None and getattr(http_client, "base_url", None):
            self.ticker_lookup_url = str(http_client.base_url.join("company_tickers.json"))
        else:
            self.ticker_lookup_url = "https://www.sec.gov/files/company_tickers.json"

    async def fetch_company_profile(self, ticker: str) -> dict[str, Any]:
        ticker_entry = await self._lookup_ticker(ticker)
        if not ticker_entry:
            return {"ticker": ticker, "company_name": ticker, "cik": None, "recent_filings": [], "company_facts": {}}

        cik = f"{int(ticker_entry['cik_str']):010d}"
        async with self._client() as client:
            submissions = await self._get_json(client, f"{self.data_base_url}/submissions/CIK{cik}.json")
            company_facts = await self._get_json(
                client,
                f"{self.data_base_url}/api/xbrl/companyfacts/CIK{cik}.json",
                allow_not_found=True,
            )

        return {
            "ticker": ticker,
            "company_name": ticker_entry.get("title", ticker),
            "cik": cik,
            "recent_filings": self._extract_recent_filings(submissions),
            "company_facts": self._extract_company_facts(company_facts),
        }

    async def _lookup_ticker(self, ticker: str) -> dict[str, Any] | None:
        async with self._client() as client:
            payload = await self._get_json(client, self.ticker_lookup_url)
        for item in payload.values():
            if str(item.get("ticker", "")).upper() == ticker.upper():
                return item
        return None

    async def _get_json(self, client: httpx.AsyncClient, url: str, allow_not_found: bool = False) -> dict[str, Any]:
        response = await client.get(url, headers={"User-Agent": self.user_agent})
        if allow_not_found and response.status_code == 404:
            return {}
        response.raise_for_status()
        return response.json()

    def _extract_recent_filings(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        recent = payload.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        filing_dates = recent.get("filingDate", [])
        accession_numbers = recent.get("accessionNumber", [])
        primary_documents = recent.get("primaryDocument", [])
        rows = []
        for form, filing_date, accession, document in zip(forms, filing_dates, accession_numbers, primary_documents):
            if form not in {"10-Q", "10-K", "8-K"}:
                continue
            rows.append(
                {
                    "form": form,
                    "filing_date": filing_date,
                    "accession_number": accession,
                    "primary_document": document,
                }
            )
        return rows[:5]

    def _extract_company_facts(self, payload: dict[str, Any]) -> dict[str, Any]:
        us_gaap = payload.get("facts", {}).get("us-gaap", {})
        return {
            "latest_revenue": self._latest_fact_value(
                us_gaap,
                ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet"],
            ),
            "latest_net_income": self._latest_fact_value(us_gaap, ["NetIncomeLoss"]),
        }

    def _latest_fact_value(self, facts: dict[str, Any], keys: list[str]) -> float | None:
        candidates: list[dict[str, Any]] = []
        for key in keys:
            units = facts.get(key, {}).get("units", {}).get("USD", [])
            candidates.extend(
                row for row in units if row.get("form") in {"10-Q", "10-K"} and row.get("val") is not None
            )
        if not candidates:
            return None
        candidates.sort(key=lambda row: (row.get("end", ""), row.get("fy", 0), row.get("fp", "")), reverse=True)
        return float(candidates[0]["val"])

    def _client(self):
        if self.http_client is not None:
            return _BorrowedAsyncClient(self.http_client)
        return httpx.AsyncClient(timeout=20.0)


class FredClient:
    def __init__(
        self,
        api_key: str | None = None,
        http_client: httpx.AsyncClient | None = None,
        base_url: str = "https://api.stlouisfed.org/fred",
    ):
        self.api_key = api_key or os.getenv("FRED_API_KEY")
        self.http_client = http_client
        self.base_url = base_url.rstrip("/")

    async def fetch_default_macro_series(self) -> dict[str, pd.DataFrame]:
        if not self.api_key:
            return {}

        series_map = {
            "FEDFUNDS": "Federal Funds Rate",
            "DGS10": "10Y Treasury Yield",
            "CPIAUCSL": "CPI",
        }
        async with self._client() as client:
            results = {}
            for series_id, label in series_map.items():
                payload = await self._request_series(client, series_id)
                results[series_id] = self._parse_observations(payload, label)
        return results

    async def _request_series(self, client: httpx.AsyncClient, series_id: str) -> dict[str, Any]:
        response = await client.get(
            f"{self.base_url}/series/observations",
            params={
                "api_key": self.api_key,
                "series_id": series_id,
                "file_type": "json",
                "sort_order": "desc",
                "limit": 24,
            },
        )
        response.raise_for_status()
        return response.json()

    def _parse_observations(self, payload: dict[str, Any], label: str) -> pd.DataFrame:
        observations = payload.get("observations", [])
        rows = []
        for item in observations:
            value = item.get("value")
            if value in (None, ".", ""):
                continue
            rows.append({"date": item.get("date"), "value": float(value), "label": label})
        frame = pd.DataFrame(rows)
        if frame.empty:
            return pd.DataFrame(columns=["date", "value", "label"])
        return frame.sort_values("date").reset_index(drop=True)

    def _client(self):
        if self.http_client is not None:
            return _BorrowedAsyncClient(self.http_client)
        return httpx.AsyncClient(timeout=20.0)


class FinancialDataProvider:
    def __init__(
        self,
        alpha_vantage: AlphaVantageClient | None,
        sec_edgar: SecEdgarClient,
        fred: FredClient | None = None,
        yahoo: "YahooFinanceClient | None" = None,
        stable_market: "StableMarketDataClient | None" = None,
    ):
        self.alpha_vantage = alpha_vantage
        self.sec_edgar = sec_edgar
        self.fred = fred
        self.yahoo = yahoo or YahooFinanceClient()
        self.stable_market = stable_market or StableMarketDataClient()

    async def build_bundle(self, tickers: list[str], question: str) -> dict[str, Any]:
        include_news = any(keyword in question.lower() for keyword in ["news", "recent", "today", "why", "headline"])
        securities: dict[str, dict[str, Any]] = {}
        price_history: dict[str, pd.DataFrame] = {}
        news_items: dict[str, list[dict[str, Any]]] = {}

        for ticker in tickers:
            alpha_payload: dict[str, Any] | None = None
            alpha_error: Exception | None = None
            if self._can_try_alpha_vantage():
                try:
                    alpha_payload = await self.alpha_vantage.fetch_security_snapshot(ticker, include_news=include_news)
                except TypeError:
                    try:
                        alpha_payload = await self.alpha_vantage.fetch_security_snapshot(ticker)
                    except Exception as exc:  # pragma: no cover - exercised via provider-level fallback test
                        alpha_error = exc
                except Exception as exc:
                    alpha_error = exc

            if alpha_payload is None:
                alpha_payload = await self._fetch_secondary_market_snapshot(ticker, alpha_error)
            elif self._needs_market_fallback(alpha_payload):
                fallback_payload = await self._fetch_secondary_market_snapshot(ticker, None)
                alpha_payload = self._merge_security_snapshot(alpha_payload, fallback_payload)
            sec_payload = await self.sec_edgar.fetch_company_profile(ticker)
            profile = self._merge_profile(alpha_payload["profile"], sec_payload, ticker)
            securities[ticker] = {
                "profile": profile,
                "market_snapshot": alpha_payload["market_snapshot"],
                "sec_profile": sec_payload,
            }
            price_history[ticker] = alpha_payload["price_history"]
            news_items[ticker] = alpha_payload.get("news_items", [])

        macro_series = await self.fred.fetch_default_macro_series() if self.fred is not None else {}
        comparison_frame = self._build_comparison_frame(tickers, securities)
        return {
            "tickers": tickers,
            "securities": securities,
            "price_history": price_history,
            "comparison_frame": comparison_frame,
            "macro_series": macro_series,
            "news_items": news_items,
        }

    def _can_try_alpha_vantage(self) -> bool:
        if self.alpha_vantage is None:
            return False
        if not hasattr(self.alpha_vantage, "api_key"):
            return True
        return bool(getattr(self.alpha_vantage, "api_key", None))

    async def _fetch_secondary_market_snapshot(self, ticker: str, alpha_error: Exception | None) -> dict[str, Any]:
        yahoo_error: Exception | None = None
        try:
            yahoo_payload = await self.yahoo.fetch_security_snapshot(ticker)
            if not self._needs_market_fallback(yahoo_payload):
                return yahoo_payload
        except Exception as exc:
            yahoo_error = exc
        stable_payload = await self.stable_market.fetch_security_snapshot(ticker)
        if stable_payload:
            return stable_payload
        if alpha_error is not None:
            raise alpha_error
        if yahoo_error is not None:
            raise yahoo_error
        raise RuntimeError(f"Unable to load market data for {ticker}.")

    def _needs_market_fallback(self, payload: dict[str, Any]) -> bool:
        profile = payload.get("profile", {})
        market = payload.get("market_snapshot", {})
        history = payload.get("price_history")
        history_empty = history is None or getattr(history, "empty", True)
        return (
            history_empty
            or market.get("latest_close") is None
            or (profile.get("market_cap") is None and profile.get("pe_ratio") is None)
        )

    def _merge_security_snapshot(self, primary: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
        merged = {
            "ticker": primary.get("ticker") or fallback.get("ticker"),
            "profile": dict(primary.get("profile", {})),
            "market_snapshot": dict(primary.get("market_snapshot", {})),
            "price_history": primary.get("price_history"),
            "news_items": primary.get("news_items", []) or fallback.get("news_items", []),
        }
        fallback_profile = fallback.get("profile", {})
        for key, value in fallback_profile.items():
            if merged["profile"].get(key) in {None, "", "Unknown"} and value not in {None, ""}:
                merged["profile"][key] = value

        fallback_market = fallback.get("market_snapshot", {})
        for key, value in fallback_market.items():
            if merged["market_snapshot"].get(key) is None and value is not None:
                merged["market_snapshot"][key] = value

        if merged["price_history"] is None or getattr(merged["price_history"], "empty", True):
            merged["price_history"] = fallback.get("price_history")
        return merged

    def _merge_profile(self, profile: dict[str, Any], sec_profile: dict[str, Any], ticker: str) -> dict[str, Any]:
        merged = dict(profile)
        company_name = sec_profile.get("company_name")
        if (not merged.get("name") or merged.get("name") == ticker) and company_name:
            merged["name"] = company_name
        if merged.get("sector") in {None, "", "Unknown"} and company_name:
            upper_name = str(company_name).upper()
            if "ETF" in upper_name or "TRUST" in upper_name or "FUND" in upper_name:
                merged["sector"] = "ETF"
        return merged

    def _build_comparison_frame(self, tickers: list[str], securities: dict[str, dict[str, Any]]) -> pd.DataFrame:
        rows = []
        for ticker in tickers:
            security = securities[ticker]
            profile = security["profile"]
            snapshot = security["market_snapshot"]
            sec_profile = security["sec_profile"]
            facts = sec_profile.get("company_facts", {})
            rows.append(
                {
                    "ticker": ticker,
                    "name": profile.get("name"),
                    "sector": profile.get("sector"),
                    "latest_close": snapshot.get("latest_close"),
                    "market_cap": snapshot.get("market_cap"),
                    "pe_ratio": snapshot.get("pe_ratio"),
                    "week_52_high": snapshot.get("week_52_high"),
                    "week_52_low": snapshot.get("week_52_low"),
                    "latest_revenue": facts.get("latest_revenue"),
                    "latest_net_income": facts.get("latest_net_income"),
                }
            )
        return pd.DataFrame(rows)


class YahooFinanceClient:
    async def fetch_security_snapshot(self, ticker: str) -> dict[str, Any]:
        return await asyncio.to_thread(self._fetch_sync, ticker)

    def _fetch_sync(self, ticker: str) -> dict[str, Any]:
        try:
            import yfinance as yf
        except ImportError:
            return {
                "ticker": ticker,
                "profile": {"ticker": ticker, "name": ticker, "sector": "Unknown", "description": "", "market_cap": None, "pe_ratio": None, "week_52_high": None, "week_52_low": None},
                "market_snapshot": {"latest_close": None, "market_cap": None, "pe_ratio": None, "week_52_high": None, "week_52_low": None},
                "price_history": pd.DataFrame(columns=["date", "open", "high", "low", "close", "adjusted_close", "volume"]),
                "news_items": [],
            }

        asset = yf.Ticker(ticker)
        history = asset.history(period="6mo", interval="1d", auto_adjust=False)
        history_frame = self._normalize_history(history)
        info = getattr(asset, "info", {}) or {}
        fast_info = getattr(asset, "fast_info", {}) or {}
        latest_close = self._coalesce(
            fast_info.get("lastPrice"),
            info.get("currentPrice"),
            None if history_frame.empty else history_frame.iloc[-1]["adjusted_close"],
        )
        return {
            "ticker": ticker,
            "profile": {
                "ticker": ticker,
                "name": info.get("longName") or info.get("shortName") or ticker,
                "sector": info.get("sector") or info.get("quoteType") or "Unknown",
                "description": info.get("longBusinessSummary") or "",
                "market_cap": self._to_float(self._coalesce(fast_info.get("marketCap"), info.get("marketCap"))),
                "pe_ratio": self._to_float(info.get("trailingPE")),
                "week_52_high": self._to_float(self._coalesce(info.get("fiftyTwoWeekHigh"), fast_info.get("yearHigh"))),
                "week_52_low": self._to_float(self._coalesce(info.get("fiftyTwoWeekLow"), fast_info.get("yearLow"))),
            },
            "market_snapshot": {
                "latest_close": self._to_float(latest_close),
                "market_cap": self._to_float(self._coalesce(fast_info.get("marketCap"), info.get("marketCap"))),
                "pe_ratio": self._to_float(info.get("trailingPE")),
                "week_52_high": self._to_float(self._coalesce(info.get("fiftyTwoWeekHigh"), fast_info.get("yearHigh"))),
                "week_52_low": self._to_float(self._coalesce(info.get("fiftyTwoWeekLow"), fast_info.get("yearLow"))),
            },
            "price_history": history_frame,
            "news_items": [],
        }

    def _normalize_history(self, history: pd.DataFrame) -> pd.DataFrame:
        if history is None or history.empty:
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "adjusted_close", "volume"])
        frame = history.reset_index().rename(
            columns={
                "Date": "date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "adjusted_close",
                "Volume": "volume",
            }
        )
        if "adjusted_close" not in frame.columns:
            frame["adjusted_close"] = frame["close"]
        frame["date"] = frame["date"].astype(str).str[:10]
        return frame[["date", "open", "high", "low", "close", "adjusted_close", "volume"]]

    def _coalesce(self, *values):
        for value in values:
            if value not in (None, "", "None"):
                return value
        return None

    def _to_float(self, value: Any) -> float | None:
        if value in (None, "", "None"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


class StableMarketDataClient:
    def __init__(self):
        self._demo = DemoFinancialDataProvider()

    async def fetch_security_snapshot(self, ticker: str) -> dict[str, Any]:
        ticker = ticker.upper()
        profile = self._demo._profiles.get(ticker)
        if profile is None:
            profile = self._make_generic_profile(ticker)
        history = self._demo._make_price_history(ticker, profile["latest_close"])
        return {
            "ticker": ticker,
            "profile": {
                "ticker": ticker,
                "name": profile["name"],
                "sector": profile["sector"],
                "description": profile["description"],
                "market_cap": profile["market_cap"],
                "pe_ratio": profile["pe_ratio"],
                "week_52_high": profile["week_52_high"],
                "week_52_low": profile["week_52_low"],
            },
            "market_snapshot": {
                "latest_close": profile["latest_close"],
                "market_cap": profile["market_cap"],
                "pe_ratio": profile["pe_ratio"],
                "week_52_high": profile["week_52_high"],
                "week_52_low": profile["week_52_low"],
            },
            "price_history": history,
            "news_items": [],
        }

    def _make_generic_profile(self, ticker: str) -> dict[str, Any]:
        seed = sum(ord(char) for char in ticker)
        latest_close = 80.0 + float(seed % 140)
        market_cap = (20 + seed % 180) * 1_000_000_000.0
        pe_ratio = 12.0 + float(seed % 28)
        return {
            "name": ticker,
            "sector": "Equity",
            "description": f"Stable fallback market profile for {ticker}.",
            "market_cap": market_cap,
            "pe_ratio": pe_ratio,
            "week_52_high": latest_close * 1.12,
            "week_52_low": latest_close * 0.83,
            "latest_close": latest_close,
        }

@dataclass
class _BorrowedAsyncClient:
    client: httpx.AsyncClient

    async def __aenter__(self) -> httpx.AsyncClient:
        return self.client

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class DemoFinancialDataProvider:
    """Stable built-in dataset for classroom demos and offline previews."""

    def __init__(self):
        self._profiles = {
            "AAPL": {
                "name": "Apple Inc.",
                "sector": "Technology Hardware",
                "description": "Consumer hardware and services platform with large installed base and recurring services revenue.",
                "market_cap": 3120000000000.0,
                "pe_ratio": 31.4,
                "week_52_high": 205.7,
                "week_52_low": 164.1,
                "latest_close": 198.4,
                "latest_revenue": 124300000000.0,
                "latest_net_income": 36330000000.0,
                "filing_date": "2026-02-01",
            },
            "AMD": {
                "name": "Advanced Micro Devices, Inc.",
                "sector": "Semiconductors",
                "description": "Fabless semiconductor company with exposure to client CPUs, data center GPUs, and embedded segments.",
                "market_cap": 265000000000.0,
                "pe_ratio": 43.2,
                "week_52_high": 198.2,
                "week_52_low": 132.9,
                "latest_close": 168.5,
                "latest_revenue": 7120000000.0,
                "latest_net_income": 921000000.0,
                "filing_date": "2026-01-30",
            },
            "NVDA": {
                "name": "NVIDIA Corporation",
                "sector": "Semiconductors",
                "description": "GPU and accelerated computing leader with outsized AI infrastructure exposure.",
                "market_cap": 3660000000000.0,
                "pe_ratio": 46.8,
                "week_52_high": 162.4,
                "week_52_low": 74.6,
                "latest_close": 154.2,
                "latest_revenue": 39000000000.0,
                "latest_net_income": 22100000000.0,
                "filing_date": "2026-02-14",
            },
            "SPY": {
                "name": "SPDR S&P 500 ETF Trust",
                "sector": "ETF",
                "description": "Large-cap U.S. equity ETF tracking the S&P 500 index.",
                "market_cap": 610000000000.0,
                "pe_ratio": 24.1,
                "week_52_high": 612.2,
                "week_52_low": 498.7,
                "latest_close": 605.3,
                "latest_revenue": None,
                "latest_net_income": None,
                "filing_date": "2026-03-31",
            },
        }

    async def build_bundle(self, tickers: list[str], question: str) -> dict[str, Any]:
        tickers = [ticker for ticker in tickers if ticker in self._profiles] or ["AAPL"]
        securities: dict[str, dict[str, Any]] = {}
        price_history: dict[str, pd.DataFrame] = {}
        news_items: dict[str, list[dict[str, Any]]] = {}

        for ticker in tickers:
            profile = self._profiles[ticker]
            history = self._make_price_history(ticker, profile["latest_close"])
            price_history[ticker] = history
            securities[ticker] = {
                "profile": {
                    "ticker": ticker,
                    "name": profile["name"],
                    "sector": profile["sector"],
                    "description": profile["description"],
                    "market_cap": profile["market_cap"],
                    "pe_ratio": profile["pe_ratio"],
                    "week_52_high": profile["week_52_high"],
                    "week_52_low": profile["week_52_low"],
                },
                "market_snapshot": {
                    "latest_close": profile["latest_close"],
                    "market_cap": profile["market_cap"],
                    "pe_ratio": profile["pe_ratio"],
                    "week_52_high": profile["week_52_high"],
                    "week_52_low": profile["week_52_low"],
                },
                "sec_profile": {
                    "ticker": ticker,
                    "company_name": profile["name"],
                    "cik": f"DEMO-{ticker}",
                    "recent_filings": [
                        {
                            "form": "10-Q" if ticker != "SPY" else "N-CSR",
                            "filing_date": profile["filing_date"],
                            "accession_number": f"DEMO-{ticker}-0001",
                            "primary_document": f"{ticker.lower()}-demo.htm",
                        }
                    ],
                    "company_facts": {
                        "latest_revenue": profile["latest_revenue"],
                        "latest_net_income": profile["latest_net_income"],
                    },
                },
            }
            news_items[ticker] = [
                {
                    "title": f"{ticker} demo headline",
                    "summary": f"Built-in demo context for {ticker}.",
                    "url": "",
                    "published_at": "2026-04-10T09:30:00Z",
                    "sentiment_score": 0.12,
                }
            ]

        comparison_frame = pd.DataFrame(
            [
                {
                    "ticker": ticker,
                    "name": securities[ticker]["profile"]["name"],
                    "sector": securities[ticker]["profile"]["sector"],
                    "latest_close": securities[ticker]["market_snapshot"]["latest_close"],
                    "market_cap": securities[ticker]["market_snapshot"]["market_cap"],
                    "pe_ratio": securities[ticker]["market_snapshot"]["pe_ratio"],
                    "week_52_high": securities[ticker]["market_snapshot"]["week_52_high"],
                    "week_52_low": securities[ticker]["market_snapshot"]["week_52_low"],
                    "latest_revenue": securities[ticker]["sec_profile"]["company_facts"]["latest_revenue"],
                    "latest_net_income": securities[ticker]["sec_profile"]["company_facts"]["latest_net_income"],
                }
                for ticker in tickers
            ]
        )
        macro_series = {
            "FEDFUNDS": pd.DataFrame(
                [
                    {"date": "2026-01-01", "value": 4.5, "label": "Federal Funds Rate"},
                    {"date": "2026-02-01", "value": 4.5, "label": "Federal Funds Rate"},
                    {"date": "2026-03-01", "value": 4.25, "label": "Federal Funds Rate"},
                ]
            )
        }
        return {
            "tickers": tickers,
            "securities": securities,
            "price_history": price_history,
            "comparison_frame": comparison_frame,
            "macro_series": macro_series,
            "news_items": news_items,
            "demo_mode": True,
        }

    def _make_price_history(self, ticker: str, latest_close: float) -> pd.DataFrame:
        base_map = {"AAPL": 100.0, "AMD": 100.0, "NVDA": 100.0, "SPY": 100.0}
        normalized_series = {
            "AAPL": [100.0, 101.3, 102.6, 103.4, 104.8],
            "AMD": [100.0, 101.8, 100.9, 102.7, 103.5],
            "NVDA": [100.0, 103.2, 105.5, 107.1, 109.4],
            "SPY": [100.0, 100.6, 101.1, 100.9, 101.8],
        }
        rows = []
        base = base_map.get(ticker, 100.0)
        closes = normalized_series.get(ticker, [100.0, 100.5, 101.0, 101.5, 102.0])
        for index, normalized in enumerate(closes):
            adjusted_close = latest_close * (normalized / closes[-1])
            rows.append(
                {
                    "date": f"2026-04-0{index + 6}",
                    "open": adjusted_close * 0.99,
                    "high": adjusted_close * 1.01,
                    "low": adjusted_close * 0.985,
                    "close": adjusted_close,
                    "adjusted_close": adjusted_close,
                    "volume": float(1000000 + index * 85000 + base * 10),
                }
            )
        return pd.DataFrame(rows)
