# Chat Workspace Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current finance workbench into a multi-turn financial research chat product with persistent in-page session history and a live artifact workspace.

**Architecture:** Keep the existing financial runner, provider layer, artifact generation, and run streaming. Add a session layer on top that stores chat messages, current tickers, and the latest workspace state. Replace the single-form UI with a chat panel plus workspace panel.

**Tech Stack:** FastAPI, Jinja2, vanilla JS, SSE/polling fallback, existing CaveAgent finance runner.

---

### Task 1: Session model and tests

**Files:**
- Modify: `tests/test_webapp.py`
- Modify: `src/cave_agent/webapp/models.py`

- [ ] Add failing tests for session creation, message submission, multi-turn history, and session artifact aggregation.
- [ ] Run the focused test file and confirm the new tests fail for missing session APIs.
- [ ] Add session/message dataclasses and serialization helpers.
- [ ] Re-run the focused tests.

### Task 2: Session service and APIs

**Files:**
- Modify: `src/cave_agent/webapp/service.py`
- Modify: `src/cave_agent/webapp/app.py`

- [ ] Implement session lifecycle methods and session event streaming.
- [ ] Reuse the existing runner to back each assistant turn with a run record.
- [ ] Keep `/api/runs/*` artifact download behavior intact.
- [ ] Re-run the focused backend tests.

### Task 3: Chat + workspace frontend

**Files:**
- Modify: `src/cave_agent/webapp/templates/index.html`
- Modify: `src/cave_agent/webapp/static/app.css`
- Modify: `src/cave_agent/webapp/static/app.js`

- [ ] Replace the single-submit workbench with a multi-turn chat layout.
- [ ] Add session bootstrapping and local session restoration in the browser.
- [ ] Keep live status, workspace artifacts, tables, charts, and downloads visible.
- [ ] Re-run frontend-facing tests and a local smoke test.

### Task 4: Verification and delivery

**Files:**
- Modify if needed: `README.md`

- [ ] Run focused pytest coverage for the web app.
- [ ] Start the app locally in demo mode and verify the chat flow manually.
- [ ] Commit and push to `main` on `https://github.com/vanzll/PyAgent`.
