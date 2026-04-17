# PyCallingAgent

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/NUS-CS5260%20Final%20Project-003D7C?style=flat-square" alt="NUS CS5260 Final Project"></a>
  <a href="https://pycallingagent.onrender.com"><img src="https://img.shields.io/badge/Live%20Demo-pycallingagent.onrender.com-2ea44f?style=flat-square" alt="Live Demo"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square" alt="Python 3.10+"></a>
</p>

> **NUS CS5260 — Neural Networks: Foundations to Applications**
> Final project submission. This public-facing agent product is entirely derived from work conducted as part of the NUS CS5260 course.
> **Research-only demonstration. Not investment advice.**

---

## About

**PyCallingAgent** is a prompt-first financial research agent built on top of a persistent Python runtime. A user types one natural-language question; the agent infers the target (e.g. `AAPL`, `NVDA`, `SPY`), pulls grounded data from SEC EDGAR and public market sources, runs Python code inside a live runtime, and returns a written answer together with charts, tables, and a downloadable report — all on a single page.

The project is packaged as a deployable web app with a FastAPI backend and a lightweight browser UI. A public instance is live at **[pycallingagent.onrender.com](https://pycallingagent.onrender.com)**.

### What it is

- A **financial research agent** that returns language answers **and** visible work products (chart + table + report) in one turn.
- A **deployable product**: FastAPI service, session/run orchestration, artifact download, and a simple web frontend.
- A **course deliverable** for NUS CS5260, built around the idea that an LLM should drive a live Python process instead of reasoning about text snapshots of one.

### What it is not

- Not a general-purpose agent framework. The underlying agent core is provided by the [CaveAgent](https://github.com/acodercat/cave-agent) open-source library; this repository adds the financial research pipeline and the web application on top.
- Not a financial advisory product. All outputs are generated for coursework and demonstration.

---

## Quick Look

- **Live demo:** https://pycallingagent.onrender.com
- **Try prompts such as:**
  - `Summarize Apple and show the recent price trend.`
  - `Compare AMD and Nvidia on valuation and performance.`
  - `Give me a market snapshot for SPY and highlight the risks.`

Non-financial prompts (e.g. `hello`) fall through to generic chat, so the app does not error on small talk.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Run the Web App Locally](#run-the-web-app-locally)
- [Deploy Your Own Public Instance](#deploy-your-own-public-instance)
- [Repository Layout](#repository-layout)
- [Architecture Overview](#architecture-overview)
- [Underlying Agent Core](#underlying-agent-core)
- [Acknowledgements](#acknowledgements)
- [License](#license)

---

## Getting Started

### Requirements

- Python 3.10 or newer
- An LLM endpoint that speaks the OpenAI-compatible API (any provider works)
- Optional: an SEC-compliant user agent string if you want to query SEC EDGAR
- Optional: an Alpha Vantage API key for live market data

### Install

```bash
git clone https://github.com/vanzll/PyAgent.git
cd PyAgent
pip install -e '.[openai,webapp]'
```

---

## Run the Web App Locally

Set the environment variables required by the app:

```bash
export LLM_MODEL_ID="your-model"
export LLM_API_KEY="your-api-key"
# Optional for OpenAI-compatible endpoints
export LLM_BASE_URL="https://api.openai.com/v1"

# SEC requires an identifying user agent
export SEC_USER_AGENT="Your Name your.email@example.com"

# Optional: Alpha Vantage for live market data
export ALPHAVANTAGE_API_KEY="your-alpha-vantage-key"
```

Start the web app:

```bash
cave-agent-webapp
```

Open `http://localhost:8000` in your browser.

Without `ALPHAVANTAGE_API_KEY`, the app runs in **public-data mode** — it still serves SEC filings plus a stable market-data fallback, which keeps the demo usable when free market APIs are rate-limited.

### Classroom Demo Mode

A deterministic demo mode is included for classroom presentations. It skips live credentials and serves built-in sample data for `AAPL`, `AMD`, `NVDA`, and `SPY`:

```bash
bash examples/run_financial_research_demo.sh
```

This is the recommended mode for live demos, since it does not depend on any third-party API being available at presentation time.

---

## Deploy Your Own Public Instance

The repository includes a top-level [`render.yaml`](render.yaml) blueprint and a [`Procfile`](Procfile) so the app can be deployed directly from GitHub.

**Simplest path — Render:**

1. Fork or push this repository to your own GitHub account.
2. Create a new Web Service on [Render](https://render.com/) and point it at your repository.
3. Render will pick up the included blueprint. If you prefer to configure manually:
   - Build command: `pip install '.[openai,webapp]'`
   - Start command: `cave-agent-webapp`
4. Configure environment variables in the Render dashboard:
   - `LLM_MODEL_ID`, `LLM_API_KEY`, optional `LLM_BASE_URL`
   - `SEC_USER_AGENT`
   - optional `ALPHAVANTAGE_API_KEY`
5. Render assigns a default `*.onrender.com` URL, which is enough for a course submission.

A fuller walkthrough is in [`docs/render-deployment.md`](docs/render-deployment.md).

---

## Repository Layout

```
.
├── src/cave_agent/            # Agent core library (imported from CaveAgent)
│   ├── runtime/               # IPythonRuntime / IPyKernelRuntime
│   ├── models/                # LLM adapters (OpenAI, LiteLLM)
│   ├── skills/                # Agent Skills loader
│   └── webapp/                # FastAPI product layer (project contribution)
│       ├── app.py             # FastAPI entrypoint
│       ├── agent_runner.py    # FinancialResearchRunner orchestration
│       ├── service.py         # Session / run routing
│       ├── financial_data.py  # SEC EDGAR + market data providers
│       ├── finance_skills/    # Finance-specific runtime skills
│       ├── templates/         # Jinja2 HTML
│       └── static/            # CSS + vanilla JS frontend
├── tests/                     # Pytest suite for agent core and webapp
├── examples/                  # Usage scripts and demo launchers
├── slides/                    # Course presentation deck and speaker notes
├── docs/                      # Deployment and handoff notes
├── render.yaml                # Render deployment blueprint
└── Procfile                   # Alternative start command
```

---

## Architecture Overview

The product is a thin FastAPI application on top of a persistent Python runtime.

```
┌─────────────┐    ┌───────────────┐    ┌───────────────────────┐    ┌──────────────┐
│ Browser UI  │ -> │ FastAPI layer │ -> │ FinancialResearchRunner│ -> │ Data layer  │
│ Jinja2 + JS │ <- │ sessions/runs │ <- │ (agent + skills)      │ <- │ SEC · Market │
└─────────────┘    └───────────────┘    └───────────────────────┘    └──────────────┘
                          │                        │
                          ▼                        ▼
                    SSE / polling          IPython runtime
                    artifact download      (live DataFrames, skills)
```

**Execution flow for one prompt:**

1. **Parse** — route finance vs. generic, extract tickers or market proxies.
2. **Fetch** — load SEC filings and market data; fall back to the public-data provider if needed.
3. **Inject** — insert price frames, fundamentals, and helper functions into the runtime as live Python variables.
4. **Run** — the agent calls runtime skills to produce the answer and visual work products.
5. **Materialize** — save charts, tables, and a markdown report to the session workspace.

The FastAPI layer keeps the web concerns simple: each session owns a message history and a working folder, each user prompt becomes a cancellable run, and progress is streamed back to the page via SSE with a polling fallback.

---

## Underlying Agent Core

The agent core (the `cave_agent` Python package in `src/`) is the [CaveAgent](https://github.com/acodercat/cave-agent) open-source library. It provides the persistent Python runtime, the `Variable` / `Function` / `Type` injection API, the Agent Skills loader, and the streaming LLM adapters used by this project.

A minimal agent loop using the core library looks like this:

```python
import asyncio
from cave_agent import CaveAgent
from cave_agent.runtime import IPythonRuntime, Variable, Function
from cave_agent.models import LiteLLMModel

model = LiteLLMModel(model_id="your-model", api_key="your-key", custom_llm_provider="openai")

async def main():
    def reverse(s: str) -> str:
        """Reverse a string"""
        return s[::-1]

    runtime = IPythonRuntime(
        variables=[Variable("secret", "!dlrow ,olleH", "A reversed message")],
        functions=[Function(reverse)],
    )
    agent = CaveAgent(model, runtime=runtime)
    response = await agent.run("Reverse the secret")
    print(response.content)

asyncio.run(main())
```

Additional usage examples live under [`examples/`](examples/).

---

## Acknowledgements

- **NUS CS5260 — Neural Networks: Foundations to Applications** — the course that framed this project and its scope.
- **[CaveAgent](https://github.com/acodercat/cave-agent)** — the open-source agent core (runtime, skills, LLM adapters) used as a library.
- **SEC EDGAR** — public U.S. company filings data source.
- **Render** — public hosting used for the deployed instance.

This repository is a coursework submission. It is released under an open-source license so that the teaching staff and teammates can reproduce, inspect, and extend it.

---

## License

This project is distributed under the [MIT License](LICENSE).
