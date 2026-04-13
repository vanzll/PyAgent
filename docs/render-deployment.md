# Render Deployment Guide

This project can be deployed to a public URL without buying a custom domain. For the course requirement, the default Render subdomain is enough.

## What You Need

- A GitHub repository that contains this project
- A Render account
- Optional live-data credentials if you do not want demo mode:
  - `ALPHAVANTAGE_API_KEY`
  - `SEC_USER_AGENT`
  - optional `FRED_API_KEY`
  - `LLM_MODEL_ID`
  - `LLM_API_KEY`
  - optional `LLM_BASE_URL`

## Recommended Deployment Mode

For grading stability, deploy demo mode first:

- `WEBAPP_DEMO_MODE=1`
- no live market API keys required
- no model API keys required
- public site stays deterministic for `AAPL`, `AMD`, `NVDA`, and `SPY`

If you later want live data, switch `WEBAPP_DEMO_MODE` to `0` and add the real credentials.

## Option A: Deploy With The Included Blueprint

The repository includes [`render.yaml`](../render.yaml). Render can read it directly.

1. Push the repository to GitHub.
2. In Render, create a new Blueprint instance.
3. Select the repository.
4. Render will detect `render.yaml` and propose a Python web service.
5. Confirm the service settings and deploy.

The blueprint already sets:

- Build command: `pip install '.[openai,webapp]'`
- Start command: `cave-agent-webapp`
- Health check path: `/`
- Python version: `3.12.8`
- Storage root: `/tmp/cave-agent-webapp`
- Demo mode enabled by default

## Option B: Create The Web Service Manually

If you prefer not to use Blueprints:

1. Push the repository to GitHub.
2. In Render, click `New +` and create a `Web Service`.
3. Select the GitHub repository.
4. Configure:
   - Runtime: `Python`
   - Build Command: `pip install '.[openai,webapp]'`
   - Start Command: `cave-agent-webapp`
5. Add environment variables.
6. Deploy.

## Environment Variables

### Stable Demo

```bash
WEBAPP_DEMO_MODE=1
WEBAPP_STORAGE_ROOT=/tmp/cave-agent-webapp
```

### Live Data + LLM

```bash
WEBAPP_DEMO_MODE=0
WEBAPP_STORAGE_ROOT=/tmp/cave-agent-webapp
ALPHAVANTAGE_API_KEY=your-alpha-vantage-key
SEC_USER_AGENT=Your Name your.email@example.com
FRED_API_KEY=your-fred-key
LLM_MODEL_ID=your-model
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.openai.com/v1
```

## Why The App Starts Correctly On Render

The launcher now reads:

- `HOST`, defaulting to `0.0.0.0`
- `PORT`, defaulting to `8000`

This matters because managed platforms inject their own `PORT` value. The entrypoint is implemented in [src/cave_agent/webapp/__main__.py](../src/cave_agent/webapp/__main__.py).

## Public URL

Once deployment succeeds, Render will assign a default URL like:

```text
https://your-service-name.onrender.com
```

That URL is enough for the CS5260 submission. You only need a custom domain if you want a cleaner brand name.

## Submission Checklist

Before submitting the course project:

1. Open the deployed URL in a fresh browser session.
2. Run one demo scenario such as `AMD, NVDA`.
3. Confirm the home page still shows the course statement and research disclaimer.
4. Put the public URL into the last slide of the deck.
5. Record a short backup video in case the live demo fails.

## Notes

- Render's filesystem is ephemeral, so generated artifacts should be treated as temporary downloads.
- Demo mode is the safer grading path because it avoids live API quotas and rate limits.
- If you later need a more complex multi-step research workflow beyond this single-app deployment, K-Dense Web is worth a look at `www.k-dense.ai`.
