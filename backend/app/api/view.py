from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..mujoco_sim import PickPlaceSimulator
from ..view_controls import ViewPresetName
from .dependencies import get_simulator
from .schemas import CameraName, ViewMoveRequest, ViewProjectRequest


router = APIRouter(prefix="/api", tags=["view"])


@router.post("/camera/{camera}")
async def set_camera(
    camera: CameraName,
    simulator: PickPlaceSimulator = Depends(get_simulator),
) -> dict:
    return simulator.set_camera(camera)


@router.get("/view")
async def get_view(simulator: PickPlaceSimulator = Depends(get_simulator)) -> dict:
    return simulator.view_state()


@router.post("/view")
async def move_view(
    payload: ViewMoveRequest,
    simulator: PickPlaceSimulator = Depends(get_simulator),
) -> dict:
    try:
        return simulator.move_view(payload.action, payload.dx, payload.dy)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/view/reset")
async def reset_view(simulator: PickPlaceSimulator = Depends(get_simulator)) -> dict:
    return simulator.reset_view()


@router.post("/view/preset/{preset}")
async def set_view_preset(
    preset: ViewPresetName,
    simulator: PickPlaceSimulator = Depends(get_simulator),
) -> dict:
    return simulator.set_view_preset(preset)


@router.post("/view/project")
async def project_view(
    payload: ViewProjectRequest,
    simulator: PickPlaceSimulator = Depends(get_simulator),
) -> dict:
    try:
        return simulator.project_view(
            screen_x=payload.screen_x,
            screen_y=payload.screen_y,
            viewport_width=payload.viewport_width,
            viewport_height=payload.viewport_height,
            tool=payload.tool,
            apply=payload.apply,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
