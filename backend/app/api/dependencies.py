from __future__ import annotations

from fastapi import HTTPException, Request

from ..config import AppSettings
from ..mujoco_sim import PickPlaceSimulator


def get_simulator(request: Request) -> PickPlaceSimulator:
    simulator = getattr(request.app.state, "simulator", None)
    if simulator is None:
        raise HTTPException(status_code=503, detail="Simulator is not initialized")
    return simulator


def get_app_settings(request: Request) -> AppSettings:
    settings = getattr(request.app.state, "settings", None)
    if settings is None:
        raise HTTPException(status_code=503, detail="Application settings are not initialized")
    return settings
