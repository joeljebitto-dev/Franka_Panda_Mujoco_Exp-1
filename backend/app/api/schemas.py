from __future__ import annotations

from math import isfinite
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..config import get_settings
from ..view_controls import ViewMoveAction


_settings = get_settings().simulator
_bounds = _settings.scene.marker_bounds

SceneTool = Literal["pickup", "target"]
CameraName = Literal["overview", "side", "wrist"]
ManualMode = Literal["auto", "manual"]


class FiniteBaseModel(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)


class SceneRequest(FiniteBaseModel):
    pickup_x: float = Field(_settings.scene.default_pickup_xy[0], ge=_bounds.x_min, le=_bounds.x_max)
    pickup_y: float = Field(_settings.scene.default_pickup_xy[1], ge=_bounds.y_min, le=_bounds.y_max)
    target_x: float = Field(_settings.scene.default_target_xy[0], ge=_bounds.x_min, le=_bounds.x_max)
    target_y: float = Field(_settings.scene.default_target_xy[1], ge=_bounds.y_min, le=_bounds.y_max)


class ViewMoveRequest(FiniteBaseModel):
    action: ViewMoveAction
    dx: float = 0.0
    dy: float = 0.0


class ViewProjectRequest(FiniteBaseModel):
    screen_x: float = Field(..., ge=0)
    screen_y: float = Field(..., ge=0)
    viewport_width: float = Field(..., gt=0)
    viewport_height: float = Field(..., gt=0)
    tool: SceneTool | None = None
    apply: bool = False


class ManualModeRequest(BaseModel):
    mode: ManualMode


class ManualJointsRequest(FiniteBaseModel):
    joints: list[float] = Field(
        ...,
        min_length=_settings.arm_joint_count,
        max_length=_settings.arm_joint_count,
    )
    gripper: float = Field(
        _settings.gripper.open,
        ge=_settings.gripper.request_min,
        le=_settings.gripper.open,
    )

    @field_validator("joints")
    @classmethod
    def joints_must_be_finite(cls, value: list[float]) -> list[float]:
        if any(not isfinite(item) for item in value):
            raise ValueError("joints must contain only finite numbers")
        return value
