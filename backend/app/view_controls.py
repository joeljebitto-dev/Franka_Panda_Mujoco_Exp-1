from __future__ import annotations

from typing import Literal

import mujoco
import numpy as np

from .config import ViewPresetConfig


ViewPresetName = Literal["overview", "side", "wrist"]
ViewMoveAction = Literal["orbit", "pan", "zoom"]


def apply_view_preset(camera: mujoco.MjvCamera, preset: ViewPresetConfig, track_body_id: int = -1) -> None:
    camera.lookat[:] = preset.lookat
    camera.distance = preset.distance
    camera.azimuth = preset.azimuth
    camera.elevation = preset.elevation
    camera.fixedcamid = -1
    camera.trackbodyid = track_body_id if preset.track_body else -1
    camera.type = mujoco.mjtCamera.mjCAMERA_TRACKING if preset.track_body else mujoco.mjtCamera.mjCAMERA_FREE


def serialize_camera(camera: mujoco.MjvCamera, mode: str, width: int, height: int) -> dict:
    return {
        "mode": mode,
        "lookat": _vector(camera.lookat),
        "distance": round(float(camera.distance), 4),
        "azimuth": round(float(camera.azimuth), 3),
        "elevation": round(float(camera.elevation), 3),
        "tracking": int(camera.trackbodyid) >= 0,
        "size": [int(width), int(height)],
    }


def move_camera(
    model: mujoco.MjModel,
    scene: mujoco.MjvScene,
    camera: mujoco.MjvCamera,
    action: ViewMoveAction,
    dx: float,
    dy: float,
    zoom_min: float,
    zoom_max: float,
) -> None:
    if action == "orbit":
        mujoco.mjv_moveCamera(model, mujoco.mjtMouse.mjMOUSE_ROTATE_H, dx, dy, scene, camera)
    elif action == "pan":
        mujoco.mjv_moveCamera(model, mujoco.mjtMouse.mjMOUSE_MOVE_H, dx, 0.0, scene, camera)
        mujoco.mjv_moveCamera(model, mujoco.mjtMouse.mjMOUSE_MOVE_V, 0.0, dy, scene, camera)
    elif action == "zoom":
        mujoco.mjv_moveCamera(model, mujoco.mjtMouse.mjMOUSE_ZOOM, 0.0, dy, scene, camera)
    camera.distance = float(np.clip(camera.distance, zoom_min, zoom_max))


def project_screen_to_plane(
    model: mujoco.MjModel,
    scene: mujoco.MjvScene,
    screen_x: float,
    screen_y: float,
    viewport_width: float,
    viewport_height: float,
    plane_z: float,
    min_viewport_size: float,
    frustum_epsilon: float,
    normalize_epsilon: float,
) -> np.ndarray:
    width = max(float(viewport_width), min_viewport_size)
    height = max(float(viewport_height), min_viewport_size)
    x = float(np.clip(screen_x, 0.0, width))
    y = float(np.clip(screen_y, 0.0, height))

    head = np.zeros(3)
    forward = np.zeros(3)
    up = np.zeros(3)
    mujoco.mjv_cameraInModel(head, forward, up, scene)

    forward = _normalized(forward, normalize_epsilon)
    up = _normalized(up, normalize_epsilon)
    right = _normalized(np.cross(forward, up), normalize_epsilon)

    gl_camera = scene.camera[0]
    near = max(float(gl_camera.frustum_near), frustum_epsilon)
    vertical_scale = abs(float(gl_camera.frustum_top)) / near
    if vertical_scale <= 0:
        vertical_scale = np.tan(np.deg2rad(float(model.vis.global_.fovy)) * 0.5)
    horizontal_scale = vertical_scale * (width / height)

    ndc_x = (2.0 * x / width) - 1.0
    ndc_y = 1.0 - (2.0 * y / height)
    ray = _normalized(forward + right * ndc_x * horizontal_scale + up * ndc_y * vertical_scale, normalize_epsilon)
    if abs(float(ray[2])) < frustum_epsilon:
        return head.copy()

    hit_distance = (float(plane_z) - float(head[2])) / float(ray[2])
    if hit_distance < 0:
        return head.copy()
    return head + ray * hit_distance


def _normalized(vector: np.ndarray, epsilon: float) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm <= epsilon:
        return vector
    return vector / norm


def _vector(values: np.ndarray) -> list[float]:
    return [round(float(value), 4) for value in values]
