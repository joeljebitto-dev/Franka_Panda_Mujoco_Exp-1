from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from .api import manual_router, simulation_router, view_router
from .config import AppSettings, get_settings
from .mujoco_sim import PickPlaceSimulator


def create_app(settings: AppSettings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        simulator = PickPlaceSimulator(settings)
        app.state.settings = settings
        app.state.simulator = simulator
        try:
            yield
        finally:
            simulator.close()
            app.state.simulator = None

    app = FastAPI(title=settings.app_title, lifespan=lifespan)
    app.state.settings = settings
    app.state.simulator = None

    app.include_router(simulation_router)
    app.include_router(view_router)
    app.include_router(manual_router)
    _mount_frontend(app, settings)
    return app


def _mount_frontend(app: FastAPI, settings: AppSettings) -> None:
    dist_dir = settings.paths.frontend_dist_dir
    assets_dir = dist_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend_assets")

    @app.get("/", include_in_schema=False, response_model=None)
    async def index() -> Response:
        index_file = dist_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return HTMLResponse(
            "<!doctype html><title>Robot Arm Pick-and-Place Simulator</title>"
            "<body><main style='font-family: sans-serif; padding: 2rem'>"
            "<h1>Frontend build not found</h1>"
            "<p>Run <code>scripts/run.sh</code> for the Vite development server, "
            "or <code>npm run build</code> inside <code>frontend</code>.</p>"
            "</main></body>",
            status_code=200,
        )

    @app.get("/{path:path}", include_in_schema=False, response_model=None)
    async def frontend_asset_or_fallback(path: str) -> Response:
        if path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        file_path = _safe_dist_path(dist_dir, path)
        if file_path and file_path.is_file():
            return FileResponse(file_path)
        return await index()


def _safe_dist_path(root: Path, requested_path: str) -> Path | None:
    candidate = (root / requested_path).resolve()
    root = root.resolve()
    if root == candidate or root in candidate.parents:
        return candidate
    return None


app = create_app()
