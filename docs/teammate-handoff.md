# CS5260 Financial Agent Handoff

## 1. Project Goal

This project is a public-facing **Financial Research Agent** for the NUS CS5260 final project.

The product accepts one or more U.S. stock or ETF tickers plus a natural-language question, then returns:

- a short research brief
- snapshot cards
- a comparison table
- a price/performance chart
- downloadable artifacts

The product is intentionally positioned as a **research assistant**, not an investment advisor.

## 2. Canonical Repository And Working Copy

Use these as the source of truth:

- GitHub repo: `https://github.com/vanzll/PyAgent`
- Clean local working copy on this machine: `/mnt/data/wanzl/PyAgent-release`

Do **not** continue product delivery work from `/mnt/data/wanzl/cave-agent`.
That directory is a historical development workspace with unrelated changes and an unresolved merge conflict.

## 3. Current Product Status

The product is already in a shippable state for a course demo.

Implemented:

- FastAPI web app for financial research
- homepage with product framing and CS5260 course statement
- deterministic demo mode
- market/fundamental/provider layer
- finance-oriented agent skills
- snapshot cards, preview tables, preview charts, artifact downloads
- Render deployment configuration
- 5-minute presentation deck
- 90-second demo video

Still required to complete course delivery:

1. Deploy to a real public URL
2. Put the real public URL into the slide deck
3. Smoke-test the deployed site
4. Prepare the final submission note

## 4. Important Files

### Product

- `src/cave_agent/webapp/app.py`
- `src/cave_agent/webapp/agent_runner.py`
- `src/cave_agent/webapp/financial_data.py`
- `src/cave_agent/webapp/service.py`
- `src/cave_agent/webapp/templates/index.html`
- `src/cave_agent/webapp/static/app.css`
- `src/cave_agent/webapp/static/app.js`

### Deployment

- `render.yaml`
- `Procfile`
- `docs/render-deployment.md`

### Demo / Presentation

- `docs/financial-agent-demo-script.md`
- `slides/cs5260_financial_agent_demo.pptx`
- `slides/financial_agent_speaker_notes.md`
- `video/financial_agent_demo_90s.mp4`

### Tests

- `tests/test_webapp.py`
- `tests/test_financial_data.py`
- `tests/test_webapp_main.py`

## 5. How To Run Locally

### Option A: Stable Demo Mode

This is the default for course rehearsal and grading:

```bash
bash examples/run_financial_research_demo.sh
```

Then open:

```text
http://localhost:8000
```

### Option B: Manual Demo Mode

```bash
export WEBAPP_DEMO_MODE=1
export PYTHONPATH=src
python3.10 -m cave_agent.webapp
```

## 6. How To Deploy

Use Render.

Quick path:

1. Go to Render
2. Create a `Blueprint`
3. Connect `https://github.com/vanzll/PyAgent`
4. Let Render read `render.yaml`
5. Deploy with `WEBAPP_DEMO_MODE=1`
6. Copy the resulting `*.onrender.com` URL

Detailed instructions:

- `docs/render-deployment.md`

Recommended deployment mode:

- `WEBAPP_DEMO_MODE=1`

Reason:

- deterministic output
- no live API quota issues
- no LLM key required
- lower demo risk

## 7. Demo Script For Presentation

Use these three demo cases:

### Demo 1

- Tickers: `AAPL`
- Question: `Summarize AAPL and show the recent price trend.`

### Demo 2

- Tickers: `AMD, NVDA`
- Question: `Compare AMD and NVDA on valuation, latest fundamentals, and recent performance.`

### Demo 3

- Tickers: `SPY`
- Question: `Give me a market snapshot for SPY and highlight the main risks.`

Detailed talk track:

- `docs/financial-agent-demo-script.md`

## 8. Final Deliverables Required By The Course

Before submission, the team must have:

1. A public URL to the product
2. A 5-minute presentation deck or demo video
3. A visible statement on the product homepage that the work comes from NUS CS5260
4. A low-cost demo path

This repo already includes:

- slide deck
- speaker notes
- demo video
- homepage course statement
- demo mode

The missing piece is the final public URL.

## 9. Acceptance Checklist

The product is ready to submit only if all of these are true:

- the public URL loads without login
- the homepage shows `NUS CS5260`
- the homepage shows `For research use only`
- one demo run completes successfully from a fresh browser session
- the output includes a summary, a chart, and a downloadable artifact
- the URL is inserted into the presentation deck
- the team has a backup demo video

## 10. Suggested Task Ownership For The Teammate

Recommended delegation scope:

1. Deploy the product to Render in demo mode
2. Verify the public URL works from a fresh browser session
3. Update the final slide with the public URL
4. Prepare the submission note using the provided template
5. Rehearse the 5-minute talk using the provided script and deck

## 11. What Not To Do

- Do not continue from the dirty `cave-agent` workspace
- Do not switch to live data mode right before grading
- Do not remove the homepage disclaimer
- Do not promise investment advice or trading recommendations
- Do not rely on temporary tunnels for the final submission

## 12. Recovery Notes

If deployment fails:

1. check the Render build logs
2. check that `render.yaml` is detected
3. confirm `WEBAPP_DEMO_MODE=1`
4. confirm the start command is `cave-agent-webapp`
5. re-deploy and test again

If a live public demo becomes unstable, fall back to:

- deployed demo mode site
- local demo mode
- 90-second backup video

## 13. One-Line Summary For The Teammate

Your job is not to redesign the product. Your job is to take the existing repo, deploy it cleanly, verify the public demo, update the presentation materials, and make sure the team can submit a stable CS5260 final project.
