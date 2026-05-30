from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from ..config import AppSettings
from ..mujoco_sim import PickPlaceSimulator
from .dependencies import get_app_settings, get_simulator
from .schemas import CameraName, SceneRequest


router = APIRouter(prefix="/api", tags=["simulation"])


@router.get("/state")
async def state(simulator: PickPlaceSimulator = Depends(get_simulator)) -> dict:
    return simulator.state()


@router.get("/frame.jpg")
async def frame(
    camera: CameraName | None = None,
    simulator: PickPlaceSimulator = Depends(get_simulator),
    settings: AppSettings = Depends(get_app_settings),
) -> Response:
    try:
        image = simulator.render_jpeg(camera=camera)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return Response(
        content=image,
        media_type="image/jpeg",
        headers={"Cache-Control": settings.simulator.render.cache_control},
    )


@router.post("/start")
async def start(simulator: PickPlaceSimulator = Depends(get_simulator)) -> dict:
    return simulator.start()


@router.post("/pause")
async def pause(simulator: PickPlaceSimulator = Depends(get_simulator)) -> dict:
    return simulator.pause()


@router.post("/resume")
async def resume(simulator: PickPlaceSimulator = Depends(get_simulator)) -> dict:
    return simulator.resume()


@router.post("/step")
async def step(simulator: PickPlaceSimulator = Depends(get_simulator)) -> dict:
    return simulator.step_once()


@router.post("/reset")
async def reset(simulator: PickPlaceSimulator = Depends(get_simulator)) -> dict:
    return simulator.reset()


@router.post("/scene")
async def configure_scene(
    payload: SceneRequest,
    simulator: PickPlaceSimulator = Depends(get_simulator),
) -> dict:
    try:
        return simulator.configure_scene(
            pickup_x=payload.pickup_x,
            pickup_y=payload.pickup_y,
            target_x=payload.target_x,
            target_y=payload.target_y,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
