from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


@dataclass(frozen=True)
class RunSettings:
    host: str
    port: int


@dataclass(frozen=True)
class PathSettings:
    project_root: Path
    backend_root: Path
    frontend_source_dir: Path
    frontend_dist_dir: Path
    panda_dir: Path
    scene_xml: Path
    mjx_scene_xml: Path


@dataclass(frozen=True)
class MarkerBounds:
    x_min: float
    x_max: float
    y_min: float
    y_max: float


@dataclass(frozen=True)
class SceneSettings:
    default_pickup_xy: tuple[float, float]
    default_target_xy: tuple[float, float]
    marker_bounds: MarkerBounds
    cube_half_size: float
    cube_release_clearance: float
    target_marker_z: float
    tool_offset: tuple[float, float, float]
    success_distance: float


@dataclass(frozen=True)
class GripperSettings:
    closed: float
    open: float
    request_min: float


@dataclass(frozen=True)
class RenderSettings:
    width: int
    height: int
    jpeg_quality: int
    cache_control: str


@dataclass(frozen=True)
class StepSettings:
    reset_settle: int
    manual_apply: int
    single_step: int
    render: int


@dataclass(frozen=True)
class IkSettings:
    max_iterations: int
    position_weight: float
    orientation_weight: float
    position_tolerance: float
    orientation_tolerance: float
    damping: float
    max_delta: float
    joint_margin: float
    orientation_timestep: float
    down_orientation_seed_qpos: tuple[float, ...]


@dataclass(frozen=True)
class MotionSettings:
    pickup_low_z: float
    pickup_high_z: float
    transfer_high_z: float
    place_low_z: float
    retreat_x_offset: float
    retreat_z: float
    home_qpos: tuple[float, ...]
    approach_pickup_duration: float
    lower_to_cube_duration: float
    close_gripper_duration: float
    lift_cube_duration: float
    transfer_duration: float
    lower_to_target_duration: float
    open_gripper_duration: float
    retreat_duration: float
    return_home_duration: float


@dataclass(frozen=True)
class ViewPresetConfig:
    mode: str
    lookat: tuple[float, float, float]
    distance: float
    azimuth: float
    elevation: float
    track_body: bool = False


@dataclass(frozen=True)
class ViewSettings:
    presets: dict[str, ViewPresetConfig]
    zoom_min: float
    zoom_max: float
    projection_plane_z: float
    min_viewport_size: float
    frustum_epsilon: float
    normalize_epsilon: float


@dataclass(frozen=True)
class SimulatorSettings:
    arm_joint_count: int
    scene: SceneSettings
    gripper: GripperSettings
    render: RenderSettings
    steps: StepSettings
    ik: IkSettings
    motion: MotionSettings
    view: ViewSettings


@dataclass(frozen=True)
class AppSettings:
    app_title: str
    run: RunSettings
    paths: PathSettings
    simulator: SimulatorSettings


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    values = _load_env_file(BACKEND_ROOT / ".env")

    def read(key: str, default: str) -> str:
        return os.environ.get(key, values.get(key, default))

    paths = PathSettings(
        project_root=PROJECT_ROOT,
        backend_root=BACKEND_ROOT,
        frontend_source_dir=_path(read("FRONTEND_SOURCE_DIR", "frontend")),
        frontend_dist_dir=_path(read("FRONTEND_DIST_DIR", "frontend/dist")),
        panda_dir=_path(read("PANDA_DIR", "assets/mujoco_menagerie/franka_emika_panda")),
        scene_xml=_path(read("SCENE_XML", "assets/mujoco_menagerie/franka_emika_panda/pick_place_scene.xml")),
        mjx_scene_xml=_path(read("MJX_SCENE_XML", "assets/mujoco_menagerie/franka_emika_panda/mjx_scene.xml")),
    )

    arm_joint_count = _integer(read("ARM_JOINT_COUNT", "7"), "ARM_JOINT_COUNT")
    marker_bounds = MarkerBounds(
        x_min=_floating(read("MARKER_X_MIN", "0.32"), "MARKER_X_MIN"),
        x_max=_floating(read("MARKER_X_MAX", "0.68"), "MARKER_X_MAX"),
        y_min=_floating(read("MARKER_Y_MIN", "-0.34"), "MARKER_Y_MIN"),
        y_max=_floating(read("MARKER_Y_MAX", "0.34"), "MARKER_Y_MAX"),
    )
    scene = SceneSettings(
        default_pickup_xy=(
            _floating(read("PICKUP_DEFAULT_X", "0.50"), "PICKUP_DEFAULT_X"),
            _floating(read("PICKUP_DEFAULT_Y", "-0.22"), "PICKUP_DEFAULT_Y"),
        ),
        default_target_xy=(
            _floating(read("TARGET_DEFAULT_X", "0.50"), "TARGET_DEFAULT_X"),
            _floating(read("TARGET_DEFAULT_Y", "0.22"), "TARGET_DEFAULT_Y"),
        ),
        marker_bounds=marker_bounds,
        cube_half_size=_positive_float(read("CUBE_HALF_SIZE", "0.025"), "CUBE_HALF_SIZE"),
        cube_release_clearance=_positive_float(
            read("CUBE_RELEASE_CLEARANCE", "0.002"), "CUBE_RELEASE_CLEARANCE"
        ),
        target_marker_z=_positive_float(read("TARGET_MARKER_Z", "0.012"), "TARGET_MARKER_Z"),
        tool_offset=_float_tuple(read("TOOL_OFFSET", "0.0,0.0,0.105"), "TOOL_OFFSET", 3),
        success_distance=_positive_float(read("SUCCESS_DISTANCE", "0.055"), "SUCCESS_DISTANCE"),
    )
    gripper = GripperSettings(
        closed=_positive_float(read("GRIPPER_CLOSED", "0.012"), "GRIPPER_CLOSED"),
        open=_positive_float(read("GRIPPER_OPEN", "0.04"), "GRIPPER_OPEN"),
        request_min=_non_negative_float(read("GRIPPER_REQUEST_MIN", "0.0"), "GRIPPER_REQUEST_MIN"),
    )
    render = RenderSettings(
        width=_positive_int(read("RENDER_WIDTH", "640"), "RENDER_WIDTH"),
        height=_positive_int(read("RENDER_HEIGHT", "426"), "RENDER_HEIGHT"),
        jpeg_quality=_bounded_int(read("JPEG_QUALITY", "88"), "JPEG_QUALITY", 1, 100),
        cache_control=read("FRAME_CACHE_CONTROL", "no-store, max-age=0"),
    )
    steps = StepSettings(
        reset_settle=_positive_int(read("RESET_SETTLE_STEPS", "120"), "RESET_SETTLE_STEPS"),
        manual_apply=_positive_int(read("MANUAL_APPLY_STEPS", "16"), "MANUAL_APPLY_STEPS"),
        single_step=_positive_int(read("SINGLE_STEP_STEPS", "12"), "SINGLE_STEP_STEPS"),
        render=_positive_int(read("RENDER_STEPS", "6"), "RENDER_STEPS"),
    )
    ik = IkSettings(
        max_iterations=_positive_int(read("IK_MAX_ITERATIONS", "180"), "IK_MAX_ITERATIONS"),
        position_weight=_positive_float(read("IK_POSITION_WEIGHT", "1.0"), "IK_POSITION_WEIGHT"),
        orientation_weight=_positive_float(read("IK_ORIENTATION_WEIGHT", "0.35"), "IK_ORIENTATION_WEIGHT"),
        position_tolerance=_positive_float(read("IK_POSITION_TOLERANCE", "0.004"), "IK_POSITION_TOLERANCE"),
        orientation_tolerance=_positive_float(
            read("IK_ORIENTATION_TOLERANCE", "0.05"), "IK_ORIENTATION_TOLERANCE"
        ),
        damping=_positive_float(read("IK_DAMPING", "0.035"), "IK_DAMPING"),
        max_delta=_positive_float(read("IK_MAX_DELTA", "0.08"), "IK_MAX_DELTA"),
        joint_margin=_non_negative_float(read("IK_JOINT_MARGIN", "0.01"), "IK_JOINT_MARGIN"),
        orientation_timestep=_positive_float(read("IK_ORIENTATION_TIMESTEP", "1.0"), "IK_ORIENTATION_TIMESTEP"),
        down_orientation_seed_qpos=_float_tuple(
            read("DOWN_ORIENTATION_SEED_QPOS", "0.0,0.45,0.0,-2.12,0.0,2.50,-0.7853"),
            "DOWN_ORIENTATION_SEED_QPOS",
            arm_joint_count,
        ),
    )
    motion = MotionSettings(
        pickup_low_z=_positive_float(read("PICKUP_LOW_Z", "0.075"), "PICKUP_LOW_Z"),
        pickup_high_z=_positive_float(read("PICKUP_HIGH_Z", "0.285"), "PICKUP_HIGH_Z"),
        transfer_high_z=_positive_float(read("TRANSFER_HIGH_Z", "0.30"), "TRANSFER_HIGH_Z"),
        place_low_z=_positive_float(read("PLACE_LOW_Z", "0.075"), "PLACE_LOW_Z"),
        retreat_x_offset=_floating(read("RETREAT_X_OFFSET", "-0.10"), "RETREAT_X_OFFSET"),
        retreat_z=_positive_float(read("RETREAT_Z", "0.33"), "RETREAT_Z"),
        home_qpos=_float_tuple(
            read("HOME_QPOS", "0,0.3,0,-1.57079,0,2.0,-0.7853"),
            "HOME_QPOS",
            arm_joint_count,
        ),
        approach_pickup_duration=_positive_float(
            read("DURATION_APPROACH_PICKUP", "1.15"), "DURATION_APPROACH_PICKUP"
        ),
        lower_to_cube_duration=_positive_float(read("DURATION_LOWER_TO_CUBE", "0.85"), "DURATION_LOWER_TO_CUBE"),
        close_gripper_duration=_positive_float(
            read("DURATION_CLOSE_GRIPPER", "0.55"), "DURATION_CLOSE_GRIPPER"
        ),
        lift_cube_duration=_positive_float(read("DURATION_LIFT_CUBE", "0.85"), "DURATION_LIFT_CUBE"),
        transfer_duration=_positive_float(read("DURATION_TRANSFER", "1.25"), "DURATION_TRANSFER"),
        lower_to_target_duration=_positive_float(
            read("DURATION_LOWER_TO_TARGET", "0.85"), "DURATION_LOWER_TO_TARGET"
        ),
        open_gripper_duration=_positive_float(read("DURATION_OPEN_GRIPPER", "0.45"), "DURATION_OPEN_GRIPPER"),
        retreat_duration=_positive_float(read("DURATION_RETREAT", "0.95"), "DURATION_RETREAT"),
        return_home_duration=_positive_float(read("DURATION_RETURN_HOME", "1.15"), "DURATION_RETURN_HOME"),
    )
    view = ViewSettings(
        presets={
            "overview": _view_preset(read, "OVERVIEW", "overview", "0.46,0.0,0.28", "1.18", "135.0", "-24.0"),
            "side": _view_preset(read, "SIDE", "side", "0.48,0.02,0.24", "1.05", "92.0", "-15.0"),
            "wrist": _view_preset(
                read,
                "WRIST",
                "wrist",
                "0.0,0.0,0.0",
                "0.74",
                "145.0",
                "-28.0",
                default_track=True,
            ),
        },
        zoom_min=_positive_float(read("VIEW_ZOOM_MIN", "0.28"), "VIEW_ZOOM_MIN"),
        zoom_max=_positive_float(read("VIEW_ZOOM_MAX", "3.0"), "VIEW_ZOOM_MAX"),
        projection_plane_z=_floating(read("VIEW_PROJECTION_PLANE_Z", "0.0"), "VIEW_PROJECTION_PLANE_Z"),
        min_viewport_size=_positive_float(read("VIEW_MIN_VIEWPORT_SIZE", "1.0"), "VIEW_MIN_VIEWPORT_SIZE"),
        frustum_epsilon=_positive_float(read("VIEW_FRUSTUM_EPSILON", "0.000001"), "VIEW_FRUSTUM_EPSILON"),
        normalize_epsilon=_positive_float(read("VIEW_NORMALIZE_EPSILON", "0.000000001"), "VIEW_NORMALIZE_EPSILON"),
    )

    simulator = SimulatorSettings(
        arm_joint_count=arm_joint_count,
        scene=scene,
        gripper=gripper,
        render=render,
        steps=steps,
        ik=ik,
        motion=motion,
        view=view,
    )
    settings = AppSettings(
        app_title=read("APP_TITLE", "Robot Arm Pick-and-Place Simulator"),
        run=RunSettings(
            host=read("BACKEND_HOST", "127.0.0.1"),
            port=_positive_int(read("BACKEND_PORT", "8001"), "BACKEND_PORT"),
        ),
        paths=paths,
        simulator=simulator,
    )
    _validate_settings(settings)
    return settings


def _load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = _unquote(value.strip())
    return values


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def _integer(value: str, key: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{key} must be an integer") from exc


def _positive_int(value: str, key: str) -> int:
    parsed = _integer(value, key)
    if parsed <= 0:
        raise ValueError(f"{key} must be greater than 0")
    return parsed


def _bounded_int(value: str, key: str, minimum: int, maximum: int) -> int:
    parsed = _integer(value, key)
    if parsed < minimum or parsed > maximum:
        raise ValueError(f"{key} must be between {minimum} and {maximum}")
    return parsed


def _floating(value: str, key: str) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{key} must be a number") from exc


def _positive_float(value: str, key: str) -> float:
    parsed = _floating(value, key)
    if parsed <= 0:
        raise ValueError(f"{key} must be greater than 0")
    return parsed


def _non_negative_float(value: str, key: str) -> float:
    parsed = _floating(value, key)
    if parsed < 0:
        raise ValueError(f"{key} must be greater than or equal to 0")
    return parsed


def _float_tuple(value: str, key: str, length: int) -> tuple[float, ...]:
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if len(parts) != length:
        raise ValueError(f"{key} must contain exactly {length} comma-separated numbers")
    return tuple(_floating(part, key) for part in parts)


def _boolean(value: str, key: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{key} must be a boolean")


def _view_preset(
    read,
    prefix: str,
    mode: str,
    default_lookat: str,
    default_distance: str,
    default_azimuth: str,
    default_elevation: str,
    default_track: bool = False,
) -> ViewPresetConfig:
    return ViewPresetConfig(
        mode=mode,
        lookat=_float_tuple(read(f"VIEW_{prefix}_LOOKAT", default_lookat), f"VIEW_{prefix}_LOOKAT", 3),
        distance=_positive_float(read(f"VIEW_{prefix}_DISTANCE", default_distance), f"VIEW_{prefix}_DISTANCE"),
        azimuth=_floating(read(f"VIEW_{prefix}_AZIMUTH", default_azimuth), f"VIEW_{prefix}_AZIMUTH"),
        elevation=_floating(read(f"VIEW_{prefix}_ELEVATION", default_elevation), f"VIEW_{prefix}_ELEVATION"),
        track_body=_boolean(read(f"VIEW_{prefix}_TRACK_BODY", str(default_track)), f"VIEW_{prefix}_TRACK_BODY"),
    )


def _validate_settings(settings: AppSettings) -> None:
    sim = settings.simulator
    bounds = sim.scene.marker_bounds
    if bounds.x_min >= bounds.x_max:
        raise ValueError("MARKER_X_MIN must be less than MARKER_X_MAX")
    if bounds.y_min >= bounds.y_max:
        raise ValueError("MARKER_Y_MIN must be less than MARKER_Y_MAX")
    _validate_xy(sim.scene.default_pickup_xy, bounds, "PICKUP_DEFAULT")
    _validate_xy(sim.scene.default_target_xy, bounds, "TARGET_DEFAULT")
    if sim.gripper.closed >= sim.gripper.open:
        raise ValueError("GRIPPER_CLOSED must be less than GRIPPER_OPEN")
    if sim.gripper.request_min > sim.gripper.open:
        raise ValueError("GRIPPER_REQUEST_MIN must be less than or equal to GRIPPER_OPEN")
    if sim.view.zoom_min >= sim.view.zoom_max:
        raise ValueError("VIEW_ZOOM_MIN must be less than VIEW_ZOOM_MAX")
    for name, preset in sim.view.presets.items():
        if not sim.view.zoom_min <= preset.distance <= sim.view.zoom_max:
            raise ValueError(f"{name} view distance must be inside VIEW_ZOOM_MIN and VIEW_ZOOM_MAX")


def _validate_xy(value: tuple[float, float], bounds: MarkerBounds, label: str) -> None:
    x, y = value
    if not bounds.x_min <= x <= bounds.x_max:
        raise ValueError(f"{label}_X must be inside marker X bounds")
    if not bounds.y_min <= y <= bounds.y_max:
        raise ValueError(f"{label}_Y must be inside marker Y bounds")
