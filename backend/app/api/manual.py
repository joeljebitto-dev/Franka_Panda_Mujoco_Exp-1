from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..mujoco_sim import PickPlaceSimulator
from .dependencies import get_simulator
from .schemas import ManualJointsRequest, ManualModeRequest


router = APIRouter(prefix="/api/manual", tags=["manual"])


@router.post("/mode")
async def set_manual_mode(
    payload: ManualModeRequest,
    simulator: PickPlaceSimulator = Depends(get_simulator),
) -> dict:
    return simulator.set_interaction_mode(payload.mode)


@router.post("/joints")
async def set_manual_joints(
    payload: ManualJointsRequest,
    simulator: PickPlaceSimulator = Depends(get_simulator),
) -> dict:
    try:
        return simulator.set_manual_targets(payload.joints, payload.gripper)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
