from __future__ import annotations

from fastapi import Request

from ..config import AppSettings
from ..mujoco_sim import PickPlaceSimulator


def get_simulator(request: Request) -> PickPlaceSimulator:
    return request.app.state.simulator


def get_app_settings(request: Request) -> AppSettings:
    return request.app.state.settings
