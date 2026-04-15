from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

import pandas as pd
import matplotlib.pyplot as plt

from cave_agent import CaveAgent
from cave_agent.models import LiteLLMModel, OpenAIServerModel
from cave_agent.runtime import IPythonRuntime, Variable
from cave_agent.skills import SkillDiscovery

from .financial_data import AlphaVantageClient, DemoFinancialDataProvider, FinancialDataProvider, FredClient, SecEdgarClient
from .models import ArtifactRecord, RunResult
from .service import ParsedInputBundle


class ArtifactWorkspace:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._artifacts: list[ArtifactRecord] = []
        self.preview_tables: list[dict[str, Any]] = []
        self.preview_charts: list[dict[str, Any]] = []
        self.summary_text = ""

    def save_dataframe(self, dataframe: pd.DataFrame, name: str, format: str = "csv") -> str:
        suffix = ".xlsx" if format == "xlsx" else ".csv"
        filename = name if name.endswith(suffix) else f"{name}{suffix}"
        path = self.root / filename
        if format == "xlsx":
            dataframe.to_excel(path, index=False)
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            dataframe.to_csv(path, index=False)
            content_type = "text/csv"
        self._artifacts.append(ArtifactRecord(name=path.name, path=path, content_type=content_type, kind="table", label=path.name))
        self.preview_tables.append(self._preview_table(path.name, dataframe))
        return str(path)

    def save_markdown(self, text: str, name: str = "summary.md") -> str:
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        self.summary_text = text
        self._artifacts.append(ArtifactRecord(name=path.name, path=path, content_type="text/markdown", kind="report", label="Summary"))
        return str(path)

    def save_chart(self, figure, name: str) -> str:
        filename = name if name.endswith(".png") else f"{name}.png"
        path = self.root / filename
        figure.savefig(path, bbox_inches="tight")
        self._artifacts.append(ArtifactRecord(name=path.name, path=path, content_type="image/png", kind="chart", label=path.name))
        self.preview_charts.append({"name": path.name, "label": path.name})
        return str(path)

    def list_artifacts(self) -> list[ArtifactRecord]:
        return self._artifacts

    def clear_outputs(self) -> None:
        self._artifacts = []
        self.preview_tables = []
        self.preview_charts = []
        self.summary_text = ""

    def _preview_table(self, name: str, dataframe: pd.DataFrame) -> dict[str, Any]:
        preview = dataframe.head(10)
        return {
            "name": name,
            "columns": [str(column) for column in preview.columns.tolist()],
            "rows": preview.where(pd.notnull(preview), None).values.tolist(),
        }


class FinancialResearchRunner:
    def __init__(self, skills_dir: Path | None = None, provider: FinancialDataProvider | None = None):
        self.skills_dir = skills_dir or Path(__file__).with_name("finance_skills")
        self.provider = provider or self._build_provider()

    async def run(self, prompt: str, bundle: ParsedInputBundle, workspace: Path, emit) -> RunResult:
        if not bundle.tickers:
            return await self._run_generic_chat(prompt, emit)

        outputs_dir = workspace / "outputs"
        artifact_workspace = ArtifactWorkspace(outputs_dir)
        emit("status", {"message": "Fetching public market data"})
        research_bundle = await self.provider.build_bundle(bundle.tickers, prompt)
        if research_bundle.get("demo_mode"):
            emit("status", {"message": "Using built-in demo market dataset"})
        emit("status", {"message": "Market data loaded"})

        skills = SkillDiscovery.from_directory(self.skills_dir)
        comparison_frame = research_bundle["comparison_frame"]
        if research_bundle.get("demo_mode") and not os.getenv("LLM_MODEL_ID"):
            emit("status", {"message": "Generating deterministic demo brief"})
            summary_text = self._build_demo_summary(research_bundle, prompt)
            artifact_workspace.save_markdown(summary_text)
            self._ensure_default_artifacts(artifact_workspace, comparison_frame, research_bundle["price_history"])
            snapshot_cards = self._build_snapshot_cards(research_bundle)
            for artifact in artifact_workspace.list_artifacts():
                emit("artifact", {"name": artifact.name, "kind": artifact.kind})
            return RunResult(
                summary_text=summary_text,
                artifacts=artifact_workspace.list_artifacts(),
                snapshot_cards=snapshot_cards,
                preview_tables=artifact_workspace.preview_tables,
                preview_charts=artifact_workspace.preview_charts,
            )

        runtime = IPythonRuntime(
            variables=[
                Variable("tickers", research_bundle["tickers"], "List of normalized equity or ETF tickers under analysis."),
                Variable("question", prompt, "The user's financial research question."),
                Variable("research_data", research_bundle["securities"], "Per-ticker structured research data including profile, market snapshot, SEC facts, and filings."),
                Variable("price_history", research_bundle["price_history"], "Dictionary mapping ticker to pandas DataFrame price history."),
                Variable("comparison_frame", comparison_frame, "Comparison DataFrame across all requested tickers."),
                Variable("macro_series", research_bundle["macro_series"], "Dictionary of FRED macroeconomic series DataFrames."),
                Variable("news_items", research_bundle["news_items"], "Optional recent news items keyed by ticker."),
                Variable("workspace", artifact_workspace, "Artifact workspace. Use workspace.save_dataframe(), workspace.save_markdown(), and workspace.save_chart()."),
                Variable("summary_text", "", "Write the final user-facing research brief here."),
            ]
        )

        instructions = (
            "You are a financial research agent inside a public web product. "
            "Use activated financial skills for market data inspection, fundamentals, comparisons, charting, and report writing. "
            "Always save user-visible output tables or charts through workspace methods. "
            "Write a concise research brief into the summary_text variable. "
            "Every summary must explicitly say it is for research use only and not investment advice."
        )
        agent = CaveAgent(
            model=self._build_model(),
            runtime=runtime,
            skills=skills,
            instructions=instructions,
            max_steps=12,
            max_exec_output=12000,
            display=False,
        )
        emit("status", {"message": "Research workspace prepared"})
        summary_text = await self._run_agent_with_fallback(
            agent=agent,
            runtime=runtime,
            prompt=prompt,
            research_bundle=research_bundle,
            artifact_workspace=artifact_workspace,
            emit=emit,
        )

        self._ensure_default_artifacts(artifact_workspace, comparison_frame, research_bundle["price_history"])
        snapshot_cards = self._build_snapshot_cards(research_bundle)

        for artifact in artifact_workspace.list_artifacts():
            emit("artifact", {"name": artifact.name, "kind": artifact.kind})

        return RunResult(
            summary_text=summary_text,
            artifacts=artifact_workspace.list_artifacts(),
            snapshot_cards=snapshot_cards,
            preview_tables=artifact_workspace.preview_tables,
            preview_charts=artifact_workspace.preview_charts,
        )

    async def _run_generic_chat(self, prompt: str, emit) -> RunResult:
        emit("status", {"message": "Running general assistant"})
        if not os.getenv("LLM_MODEL_ID"):
            return RunResult(summary_text=self._build_generic_fallback(prompt))

        runtime = IPythonRuntime(variables=[Variable("answer_text", "", "Write the final assistant answer here.")])
        agent = CaveAgent(
            model=self._build_model(),
            runtime=runtime,
            instructions=(
                "You are a concise general assistant inside a financial research product. "
                "If the user asks a non-financial question, answer it normally. "
                "If appropriate, briefly mention that you can also help with stock research, ETF comparison, and market snapshots. "
                "Write the final response into answer_text."
            ),
            max_steps=6,
            max_exec_output=8000,
            display=False,
        )
        timeout_seconds = float(os.getenv("WEBAPP_AGENT_TIMEOUT_SECONDS", "20"))
        try:
            response = await asyncio.wait_for(agent.run(prompt), timeout=timeout_seconds)
            answer_text = await runtime.retrieve("answer_text")
            return RunResult(summary_text=answer_text or response.content)
        except Exception:
            return RunResult(summary_text=self._build_generic_fallback(prompt))

    async def _run_agent_with_fallback(
        self,
        agent: CaveAgent,
        runtime: IPythonRuntime,
        prompt: str,
        research_bundle: dict[str, Any],
        artifact_workspace: ArtifactWorkspace,
        emit,
    ) -> str:
        agent_prompt = (
            f"User request: {prompt}\n"
            f"Tickers: {', '.join(research_bundle['tickers'])}\n"
            "The runtime already contains structured market data, SEC facts, price history, macro series, and optional news. "
            "Inspect the data, activate relevant skills, save at least one table and one chart, then set summary_text."
        )
        timeout_seconds = float(os.getenv("WEBAPP_AGENT_TIMEOUT_SECONDS", "20"))
        try:
            response = await asyncio.wait_for(agent.run(agent_prompt), timeout=timeout_seconds)
            summary_text = await runtime.retrieve("summary_text")
            if not summary_text:
                summary_text = response.content
            if not any(artifact.name == "summary.md" for artifact in artifact_workspace.list_artifacts()):
                artifact_workspace.save_markdown(summary_text)
            return summary_text
        except asyncio.TimeoutError:
            emit("status", {"message": "LLM timed out, using fallback summary"})
        except Exception as exc:
            emit("status", {"message": f"LLM failed, using fallback summary: {exc}"})

        artifact_workspace.clear_outputs()
        summary_text = self._build_demo_summary(research_bundle, prompt)
        if not any(artifact.name == "summary.md" for artifact in artifact_workspace.list_artifacts()):
            artifact_workspace.save_markdown(summary_text)
        return summary_text

    def _ensure_default_artifacts(
        self,
        artifact_workspace: ArtifactWorkspace,
        comparison_frame: pd.DataFrame,
        price_history: dict[str, pd.DataFrame],
    ) -> None:
        if not any(artifact.kind == "table" for artifact in artifact_workspace.list_artifacts()):
            artifact_workspace.save_dataframe(comparison_frame, "comparison", format="csv")

        if any(artifact.kind == "chart" for artifact in artifact_workspace.list_artifacts()):
            return

        figure, axis = plt.subplots(figsize=(8, 4.8))
        normalized = False
        for ticker, frame in price_history.items():
            if frame.empty:
                continue
            series = frame.copy()
            base = float(series.iloc[0]["adjusted_close"])
            if base > 0:
                series["normalized_close"] = (series["adjusted_close"] / base) * 100.0
                axis.plot(series["date"], series["normalized_close"], label=ticker)
                normalized = True
            else:
                axis.plot(series["date"], series["adjusted_close"], label=ticker)
        axis.set_title("Relative Performance" if normalized else "Price History")
        axis.set_ylabel("Normalized Return" if normalized else "Adjusted Close")
        axis.tick_params(axis="x", rotation=45)
        axis.legend()
        artifact_workspace.save_chart(figure, "normalized-returns")
        plt.close(figure)

    def _build_snapshot_cards(self, research_bundle: dict[str, Any]) -> list[dict[str, Any]]:
        cards = []
        for ticker in research_bundle["tickers"]:
            security = research_bundle["securities"][ticker]
            profile = security["profile"]
            market = security["market_snapshot"]
            sec_profile = security["sec_profile"]
            facts = sec_profile.get("company_facts", {})
            filings = sec_profile.get("recent_filings", [])
            cards.append(
                {
                    "ticker": ticker,
                    "name": profile.get("name", ticker),
                    "sector": profile.get("sector", "Unknown"),
                    "latest_close": market.get("latest_close"),
                    "market_cap": market.get("market_cap"),
                    "pe_ratio": market.get("pe_ratio"),
                    "latest_revenue": facts.get("latest_revenue"),
                    "latest_net_income": facts.get("latest_net_income"),
                    "recent_filing_form": filings[0]["form"] if filings else None,
                    "recent_filing_date": filings[0]["filing_date"] if filings else None,
                    "description": profile.get("description", ""),
                }
            )
        return cards

    def _build_provider(self):
        if self._should_use_demo_provider():
            return DemoFinancialDataProvider()
        return FinancialDataProvider(
            alpha_vantage=AlphaVantageClient(),
            sec_edgar=SecEdgarClient(),
            fred=FredClient(),
        )

    def _should_use_demo_provider(self) -> bool:
        demo_mode = os.getenv("WEBAPP_DEMO_MODE", "").strip().lower()
        return demo_mode in {"1", "true", "yes", "on"}

    def _build_demo_summary(self, research_bundle: dict[str, Any], prompt: str) -> str:
        frame = research_bundle["comparison_frame"]
        lines = [f"Question: {prompt}", ""]
        for row in frame.itertuples(index=False):
            lines.append(
                f"{row.ticker}: latest close {self._format_decimal(row.latest_close)}, "
                f"market cap {self._format_large_number(row.market_cap)}, "
                f"P/E {self._format_decimal(row.pe_ratio)}, "
                f"latest revenue {self._format_large_number(row.latest_revenue)}."
            )
        if len(frame) >= 2:
            winner = frame.sort_values("market_cap", ascending=False).iloc[0]
            lines.append("")
            lines.append(
                f"Relative view: {winner['ticker']} is the largest name in this comparison set, "
                f"while the chart highlights short-window normalized performance across the selected tickers."
            )
        lines.append("")
        lines.append("For research use only. Not investment advice.")
        return "\n".join(lines)

    def _build_generic_fallback(self, prompt: str) -> str:
        lowered = prompt.strip().lower()
        if lowered in {"hello", "hi", "hey"}:
            return (
                "Hello. I can help with general questions and also help with stock research, "
                "ETF comparison, and market snapshots. Try asking about Apple, Nvidia, or SPY."
            )
        return (
            "I can help with general questions and also help with stock research, ETF comparison, "
            "and market snapshots. For financial analysis, mention a company, ticker, ETF, or market topic."
        )

    def _format_large_number(self, value: float | None) -> str:
        if value is None or pd.isna(value):
            return "n/a"
        absolute = abs(float(value))
        if absolute >= 1_000_000_000_000:
            return f"${value / 1_000_000_000_000:.2f}T"
        if absolute >= 1_000_000_000:
            return f"${value / 1_000_000_000:.1f}B"
        if absolute >= 1_000_000:
            return f"${value / 1_000_000:.1f}M"
        return f"${value:,.0f}"

    def _format_decimal(self, value: float | None) -> str:
        if value is None or pd.isna(value):
            return "n/a"
        return f"{float(value):.1f}"

    def _build_model(self):
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        model_id = os.getenv("LLM_MODEL_ID")
        api_key = os.getenv("LLM_API_KEY")
        base_url = os.getenv("LLM_BASE_URL")
        if not model_id:
            raise RuntimeError("LLM_MODEL_ID is required to run the web app.")
        if provider == "litellm":
            custom_provider = os.getenv("LLM_CUSTOM_PROVIDER", "openai")
            return LiteLLMModel(
                model_id=model_id,
                api_key=api_key,
                base_url=base_url,
                custom_llm_provider=custom_provider,
            )
        return OpenAIServerModel(model_id=model_id, api_key=api_key, base_url=base_url)


DataAgentRunner = FinancialResearchRunner
