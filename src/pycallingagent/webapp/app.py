from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .agent_runner import FinancialResearchRunner
from .service import RunService


def create_app(service: RunService | None = None) -> FastAPI:
    package_dir = Path(__file__).parent
    templates = Jinja2Templates(directory=str(package_dir / "templates"))
    service = service or RunService(
        storage_root=Path(os.getenv("WEBAPP_STORAGE_ROOT", ".pycallingagent-webapp")),
        runner=FinancialResearchRunner(),
    )

    app = FastAPI(title="PyCallingAgent Financial Research Agent")
    app.state.run_service = service
    app.mount("/static", StaticFiles(directory=str(package_dir / "static")), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        demo_mode = os.getenv("WEBAPP_DEMO_MODE", "").strip().lower() in {"1", "true", "yes", "on"}
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"demo_mode": demo_mode},
        )

    @app.post("/api/runs")
    async def create_run(
        prompt: str = Form(...),
        tickers: str = Form(default=""),
        files: list[UploadFile] | None = File(default=None),
    ):
        try:
            record = await app.state.run_service.create_run(prompt, tickers, files)
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return JSONResponse(
            status_code=202,
            content={
                "run_id": record.run_id,
                "status_url": f"/api/runs/{record.run_id}",
                "events_url": f"/api/runs/{record.run_id}/events",
            },
        )

    @app.post("/api/sessions")
    async def create_session(tickers: str = Form(default="")):
        session = await app.state.run_service.create_session(tickers)
        return JSONResponse(
            status_code=201,
            content={
                "session_id": session.session_id,
                "status_url": f"/api/sessions/{session.session_id}",
                "events_url": f"/api/sessions/{session.session_id}/events",
            },
        )

    @app.get("/api/sessions/{session_id}")
    async def get_session(session_id: str):
        try:
            session = app.state.run_service.get_session(session_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Session not found")
        return session.to_dict()

    @app.post("/api/sessions/{session_id}/messages")
    async def create_session_message(
        session_id: str,
        prompt: str = Form(...),
        tickers: str = Form(default=""),
        files: list[UploadFile] | None = File(default=None),
    ):
        try:
            record = await app.state.run_service.create_session_message(session_id, prompt, tickers, files)
        except KeyError:
            raise HTTPException(status_code=404, detail="Session not found")
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return JSONResponse(
            status_code=202,
            content={
                "session_id": session_id,
                "run_id": record.run_id,
                "status_url": f"/api/sessions/{session_id}",
                "events_url": f"/api/sessions/{session_id}/events",
            },
        )

    @app.get("/api/sessions/{session_id}/events")
    async def stream_session_events(session_id: str):
        try:
            app.state.run_service.get_session(session_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Session not found")
        return StreamingResponse(app.state.run_service.stream_session_events(session_id), media_type="text/event-stream")

    @app.get("/api/runs/{run_id}")
    async def get_run(run_id: str):
        try:
            record = app.state.run_service.get_run(run_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Run not found")
        return record.to_dict()

    @app.get("/api/runs/{run_id}/events")
    async def stream_events(run_id: str):
        try:
            app.state.run_service.get_run(run_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Run not found")
        return StreamingResponse(app.state.run_service.stream_events(run_id), media_type="text/event-stream")

    @app.get("/api/runs/{run_id}/artifacts/{artifact_name}")
    async def download_artifact(run_id: str, artifact_name: str):
        try:
            artifact = app.state.run_service.get_artifact(run_id, artifact_name)
        except KeyError:
            raise HTTPException(status_code=404, detail="Artifact not found")
        return FileResponse(path=artifact.path, media_type=artifact.content_type, filename=artifact.name)

    return app
