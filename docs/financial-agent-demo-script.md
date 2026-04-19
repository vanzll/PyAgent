# Financial Agent Demo Script

## Goal

Show that the product is:

1. A real public-facing agent, not just a notebook
2. Grounded in public financial data
3. Able to compare companies, summarize evidence, and produce artifacts

## Demo Setup

Run the app in deterministic demo mode:

```bash
bash examples/run_financial_research_demo.sh
```

This avoids failures from API rate limits, missing credentials, or model latency during the live presentation.

For a temporary public URL during rehearsal:

```bash
bash examples/run_public_financial_demo.sh
```

This starts the same deterministic demo app and exposes it through a temporary Cloudflare quick tunnel. Keep that shell running to keep the public URL alive.

Generate the presentation deck:

```bash
python3.10 -m pip install -r slides/requirements.txt
python3.10 slides/generate_financial_agent_deck.py
```

The generated deck will be written to:

```text
slides/cs5260_financial_agent_demo.pptx
```

## Suggested Live Flow

### Demo 1: Single-stock brief

Tickers:

```text
AAPL
```

Question:

```text
Summarize AAPL and show the recent price trend.
```

What to point out:

- Snapshot card with price, market cap, valuation, and latest filing
- Research brief written in plain English
- Downloadable markdown summary and chart artifact

### Demo 2: Peer comparison

Tickers:

```text
AMD, NVDA
```

Question:

```text
Compare AMD and NVDA on valuation, latest fundamentals, and recent performance.
```

What to point out:

- Two-company snapshot cards
- Comparison table artifact
- Relative performance chart
- Structured, agent-generated comparison summary

### Demo 3: ETF snapshot

Tickers:

```text
SPY
```

Question:

```text
Give me a market snapshot for SPY and highlight the main risks.
```

What to point out:

- ETF use case, not only single-company equities
- Macro-aware framing
- Public-market research positioning

## Talk Track

### 30-second opening

This project is a public financial research agent built on top of PyCallingAgent. Instead of asking users to manually gather price data, filings, and comparison metrics, the system accepts tickers and a research question, then automatically produces a short research brief, charts, and downloadable artifacts.

### 60-second technical explanation

The backend uses a structured provider layer for market data, SEC filing data, and optional macro data. These normalized objects are injected into PyCallingAgent's persistent runtime. The agent then activates domain-specific skills for market inspection, fundamentals, comparisons, charting, and report writing. The UI streams progress live and renders the resulting snapshot cards, tables, and charts.

### 30-second product positioning

The product is intentionally framed as a financial research assistant, not an investment advisor. Every result is marked as research-only and not investment advice. That keeps the scope academically strong and product-like without over-claiming reliability.

## What To Emphasize To Maximize Score

- Public URL product shape rather than notebook-only output
- Grounding in real or official public data sources
- Agent behavior rather than static dashboard behavior
- Clear output artifacts: summary, chart, table
- Sensible product safety language
- Stable demo mode for live presentation reliability
