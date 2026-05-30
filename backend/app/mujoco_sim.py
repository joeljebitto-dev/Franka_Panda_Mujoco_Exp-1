from __future__ import annotations

import io
import os
import threading
from dataclasses import dataclass
from typing import Literal

os.environ.setdefault("MUJOCO_GL", "egl")

import mujoco
import numpy as np
from PIL import Image

from .config import AppSettings, get_settings
from .mjcf_parser import validate_scene_assets
from .view_controls import (
    ViewMoveAction,
    ViewPresetName,
    apply_view_preset,
    move_camera,
    project_screen_to_plane,
    serialize_camera,
)


CameraName = Literal["overview", "side", "wrist"]
InteractionMode = Literal["auto", "manual"]
SceneTool = Literal["pickup", "target"]


@dataclass
class MotionSegment:
    label: str
    qpos: np.ndarray
    grip: float
    duration: float
    on_enter: str | None = None
    on_exit: str | None = None


class PickPlaceSimulator:
    """MuJoCo-backed pick-and-place controller for a Franka Panda arm."""

    def __init__(self, settings: AppSettings | None = None) -> None:
        self.app_settings = settings or get_settings()
        self.settings = self.app_settings.simulator
        scene_path = validate_scene_assets(self.app_settings)
        self.model = mujoco.MjModel.from_xml_path(str(scene_path))
        self.data = mujoco.MjData(self.model)
        self.ik_data = mujoco.MjData(self.model)
        self.renderer = mujoco.Renderer(
            self.model,
            width=self.settings.render.width,
            height=self.settings.render.height,
        )
        self.view_camera = mujoco.MjvCamera()
        self.lock = threading.RLock()

        self.width = self.settings.render.width
        self.height = self.settings.render.height
        self.camera: CameraName = "overview"
        self.view_mode = "overview"
        self.interaction_mode: InteractionMode = "auto"
        self.running = False
        self.holding_cube = False
        self.complete = False
        self.phase = "Ready"
        self.progress = 0.0
        self.segment_index = 0
        self.segment_start_time = 0.0
        self.segment_start_qpos: np.ndarray | None = None
        self.plan: list[MotionSegment] = []

        self.home_key = self._name_id("key", "home")
        self.hand_body_id = self._name_id("body", "hand")
        self.box_body_id = self._name_id("body", "box")
        self.target_body_id = self._name_id("body", "target_marker")
        self.box_joint_id = self._name_id("joint", "box_joint")
        self.box_qpos_addr = int(self.model.jnt_qposadr[self.box_joint_id])
        self.box_qvel_addr = int(self.model.jnt_dofadr[self.box_joint_id])
        self.arm_joint_names = [f"joint{i}" for i in range(1, self.settings.arm_joint_count + 1)]
        self.arm_qpos_addr = np.array(
            [self.model.jnt_qposadr[self._name_id("joint", name)] for name in self.arm_joint_names],
            dtype=int,
        )
        self.arm_dof_addr = np.array(
            [self.model.jnt_dofadr[self._name_id("joint", name)] for name in self.arm_joint_names],
            dtype=int,
        )
        self.arm_ctrl_addr = np.array(
            [self._name_id("actuator", f"actuator{i}") for i in range(1, self.settings.arm_joint_count + 1)],
            dtype=int,
        )
        self.gripper_ctrl_addr = self._name_id("actuator", f"actuator{self.settings.arm_joint_count + 1}")
        self.joint_ranges = self.model.jnt_range[
            [self._name_id("joint", name) for name in self.arm_joint_names]
        ].copy()

        self.pickup_xy = np.array(self.settings.scene.default_pickup_xy, dtype=float)
        self.target_xy = np.array(self.settings.scene.default_target_xy, dtype=float)
        self.cube_half_size = self.settings.scene.cube_half_size
        self.tool_offset = np.array(self.settings.scene.tool_offset, dtype=float)
        self.open_grip = self.settings.gripper.open
        self.closed_grip = self.settings.gripper.closed
        self._down_orientation = self._compute_down_orientation()
        apply_view_preset(self.view_camera, self.settings.view.presets["overview"], self.hand_body_id)

        self.reset()

    def _name_id(self, kind: str, name: str) -> int:
        enum_name = f"mjOBJ_{kind.upper()}"
        object_type = getattr(mujoco.mjtObj, enum_name)
        object_id = mujoco.mj_name2id(self.model, object_type, name)
        if object_id < 0:
            raise ValueError(f"MuJoCo model is missing {kind} named {name!r}")
        return int(object_id)

    def _compute_down_orientation(self) -> np.ndarray:
        q = np.array(self.settings.ik.down_orientation_seed_qpos)
        self.ik_data.qpos[self.arm_qpos_addr] = q
        self.ik_data.qpos[self.settings.arm_joint_count : self.settings.arm_joint_count + 2] = self.open_grip
        mujoco.mj_forward(self.model, self.ik_data)
        return self.ik_data.xmat[self.hand_body_id].reshape(3, 3).copy()

    def reset(self, pickup_xy: tuple[float, float] | None = None, target_xy: tuple[float, float] | None = None) -> dict:
        with self.lock:
            if pickup_xy is not None:
                self.pickup_xy = self._clamp_xy(np.array(pickup_xy, dtype=float))
            if target_xy is not None:
                self.target_xy = self._clamp_xy(np.array(target_xy, dtype=float))

            mujoco.mj_resetDataKeyframe(self.model, self.data, self.home_key)
            self.data.ctrl[self.arm_ctrl_addr] = self.data.qpos[self.arm_qpos_addr]
            self.data.ctrl[self.gripper_ctrl_addr] = self.open_grip
            self._set_cube_position(self.pickup_xy[0], self.pickup_xy[1], self.cube_half_size)
            self._set_target_marker(self.target_xy)
            self.running = False
            self.holding_cube = False
            self.complete = False
            self.interaction_mode = "auto"
            self.phase = "Ready"
            self.progress = 0.0
            self.segment_index = 0
            self.segment_start_time = 0.0
            self.segment_start_qpos = None
            self.plan = []
            mujoco.mj_forward(self.model, self.data)
            self._settle(self.settings.steps.reset_settle)
            return self.state()

    def configure_scene(
        self,
        pickup_x: float,
        pickup_y: float,
        target_x: float,
        target_y: float,
    ) -> dict:
        return self.reset((pickup_x, pickup_y), (target_x, target_y))

    def start(self) -> dict:
        with self.lock:
            self.interaction_mode = "auto"
            if not self.plan or self.complete:
                self.plan = self._build_plan()
                self.segment_index = 0
                self.segment_start_time = float(self.data.time)
                self.segment_start_qpos = self.data.qpos[self.arm_qpos_addr].copy()
                self._enter_segment(self.plan[0])
            self.running = True
            self.complete = False
            return self.state()

    def pause(self) -> dict:
        with self.lock:
            self.running = False
            return self.state()

    def resume(self) -> dict:
        with self.lock:
            if self.plan and not self.complete:
                self.running = True
            return self.state()

    def set_camera(self, camera: CameraName) -> dict:
        with self.lock:
            self.camera = camera
            self.set_view_preset(camera)
            return self.state()

    def set_view_preset(self, preset: ViewPresetName) -> dict:
        with self.lock:
            apply_view_preset(self.view_camera, self.settings.view.presets[preset], self.hand_body_id)
            self.view_mode = preset
            self.camera = preset
            return self.view_state()

    def move_view(self, action: ViewMoveAction, dx: float = 0.0, dy: float = 0.0) -> dict:
        with self.lock:
            self._update_view_scene()
            move_camera(
                self.model,
                self.renderer.scene,
                self.view_camera,
                action,
                float(dx),
                float(dy),
                self.settings.view.zoom_min,
                self.settings.view.zoom_max,
            )
            self.view_mode = "custom"
            self.camera = "overview"
            return self.view_state()

    def reset_view(self) -> dict:
        return self.set_view_preset("overview")

    def project_view(
        self,
        screen_x: float,
        screen_y: float,
        viewport_width: float,
        viewport_height: float,
        tool: SceneTool | None = None,
        apply: bool = False,
    ) -> dict:
        with self.lock:
            self._update_view_scene()
            hit = project_screen_to_plane(
                self.model,
                self.renderer.scene,
                screen_x,
                screen_y,
                viewport_width,
                viewport_height,
                plane_z=self.settings.view.projection_plane_z,
                min_viewport_size=self.settings.view.min_viewport_size,
                frustum_epsilon=self.settings.view.frustum_epsilon,
                normalize_epsilon=self.settings.view.normalize_epsilon,
            )
            xy = self._clamp_xy(hit[:2])
            state = None
            if apply and tool is not None:
                state = self.move_marker(tool, xy[0], xy[1])
            return {
                "xy": self._vector([xy[0], xy[1]]),
                "tool": tool,
                "applied": bool(apply and tool is not None),
                "state": state,
            }

    def move_marker(self, tool: SceneTool, x: float, y: float) -> dict:
        with self.lock:
            xy = self._clamp_xy(np.array([x, y], dtype=float))
            if tool == "pickup":
                return self.reset((float(xy[0]), float(xy[1])), tuple(self.target_xy))
            return self.reset(tuple(self.pickup_xy), (float(xy[0]), float(xy[1])))

    def set_interaction_mode(self, mode: InteractionMode) -> dict:
        with self.lock:
            self.interaction_mode = mode
            if mode == "manual":
                self.running = False
                self.complete = False
                self.plan = []
                self.phase = "Manual control"
            elif not self.plan:
                self.phase = "Ready"
            return self.state()

    def set_manual_targets(self, joints: list[float], gripper: float) -> dict:
        with self.lock:
            targets = np.asarray(joints, dtype=float)
            if targets.shape != (self.settings.arm_joint_count,):
                raise ValueError(f"Manual control requires exactly {self.settings.arm_joint_count} joint targets")
            targets = self._clamp_joints(targets)
            grip = float(np.clip(gripper, self.closed_grip, self.open_grip))
            self.interaction_mode = "manual"
            self.running = False
            self.complete = False
            self.plan = []
            self.phase = "Manual control"
            self.data.ctrl[self.arm_ctrl_addr] = targets
            self.data.ctrl[self.gripper_ctrl_addr] = grip
            self._step_simulation(self.settings.steps.manual_apply)
            return self.state()

    def step_once(self) -> dict:
        with self.lock:
            self._step_simulation(self.settings.steps.single_step)
            return self.state()

    def render_jpeg(self, camera: CameraName | None = None) -> bytes:
        with self.lock:
            self._step_simulation(self.settings.steps.render)
            if camera is None:
                self.renderer.update_scene(self.data, camera=self.view_camera)
            else:
                self.renderer.update_scene(self.data, camera=camera)
            pixels = self.renderer.render()
            image = Image.fromarray(pixels)
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=self.settings.render.jpeg_quality, optimize=True)
            return buffer.getvalue()

    def state(self) -> dict:
        cube = self.data.xpos[self.box_body_id].copy()
        target = np.array([self.target_xy[0], self.target_xy[1], self.cube_half_size])
        distance = float(np.linalg.norm(cube[:2] - target[:2]))
        tool = self._tool_center(self.data)
        qpos = self.data.qpos[self.arm_qpos_addr]
        return {
            "time": round(float(self.data.time), 3),
            "running": self.running,
            "mode": self.interaction_mode,
            "phase": self.phase,
            "progress": round(float(self.progress), 3),
            "holding": self.holding_cube,
            "complete": self.complete,
            "success": bool(distance < self.settings.scene.success_distance and not self.holding_cube and self.complete),
            "camera": self.camera,
            "view": self.view_state(),
            "cube": self._vector(cube),
            "target": self._vector(target),
            "pickup": self._vector([self.pickup_xy[0], self.pickup_xy[1], self.cube_half_size]),
            "tool": self._vector(tool),
            "distance": round(distance, 3),
            "joints": [round(float(v), 3) for v in qpos],
            "joint_limits": self._joint_limits(),
            "manual_targets": [round(float(v), 3) for v in self.data.ctrl[self.arm_ctrl_addr]],
            "gripper": round(float(self.data.ctrl[self.gripper_ctrl_addr]), 3),
        }

    def view_state(self) -> dict:
        return serialize_camera(self.view_camera, self.view_mode, self.width, self.height)

    def _step_simulation(self, count: int) -> None:
        for _ in range(count):
            if self.running and self.plan and self.interaction_mode == "auto":
                self._advance_motion()
            if self.holding_cube:
                self._sync_cube_to_gripper()
            mujoco.mj_step(self.model, self.data)
            if self.holding_cube:
                self._sync_cube_to_gripper()

    def _advance_motion(self) -> None:
        if self.segment_index >= len(self.plan):
            self.running = False
            self.complete = True
            self.phase = "Complete"
            self.progress = 1.0
            return

        segment = self.plan[self.segment_index]
        if self.segment_start_qpos is None:
            self.segment_start_qpos = self.data.qpos[self.arm_qpos_addr].copy()

        elapsed = max(0.0, float(self.data.time) - self.segment_start_time)
        alpha = min(1.0, elapsed / max(segment.duration, 1e-6))
        eased = alpha * alpha * (3.0 - 2.0 * alpha)
        target_qpos = self.segment_start_qpos + (segment.qpos - self.segment_start_qpos) * eased

        self.data.ctrl[self.arm_ctrl_addr] = target_qpos
        self.data.ctrl[self.gripper_ctrl_addr] = segment.grip
        self.phase = segment.label
        overall = (self.segment_index + alpha) / max(1, len(self.plan))
        self.progress = float(np.clip(overall, 0.0, 1.0))

        if alpha >= 1.0:
            if segment.on_exit == "attach":
                self._attach_cube()
            self.segment_index += 1
            if self.segment_index >= len(self.plan):
                self.running = False
                self.complete = True
                self.phase = "Complete"
                self.progress = 1.0
                return
            next_segment = self.plan[self.segment_index]
            self.segment_start_time = float(self.data.time)
            self.segment_start_qpos = self.data.qpos[self.arm_qpos_addr].copy()
            self._enter_segment(next_segment)

    def _enter_segment(self, segment: MotionSegment) -> None:
        self.phase = segment.label
        if segment.on_enter == "release":
            self._release_cube()

    def _build_plan(self) -> list[MotionSegment]:
        seed = self.data.qpos[self.arm_qpos_addr].copy()
        motion = self.settings.motion
        pickup_low = np.array([self.pickup_xy[0], self.pickup_xy[1], motion.pickup_low_z])
        pickup_high = np.array([self.pickup_xy[0], self.pickup_xy[1], motion.pickup_high_z])
        transfer_high = np.array([self.target_xy[0], self.target_xy[1], motion.transfer_high_z])
        place_low = np.array([self.target_xy[0], self.target_xy[1], motion.place_low_z])
        retreat = np.array([self.target_xy[0] + motion.retreat_x_offset, self.target_xy[1], motion.retreat_z])

        q_pick_high = self._solve_ik(pickup_high, seed)
        q_pick_low = self._solve_ik(pickup_low, q_pick_high)
        q_transfer = self._solve_ik(transfer_high, q_pick_low)
        q_place_low = self._solve_ik(place_low, q_transfer)
        q_retreat = self._solve_ik(retreat, q_place_low)
        q_home = np.array(motion.home_qpos, dtype=float)

        return [
            MotionSegment("Approach pickup", q_pick_high, self.open_grip, motion.approach_pickup_duration),
            MotionSegment("Lower to cube", q_pick_low, self.open_grip, motion.lower_to_cube_duration),
            MotionSegment(
                "Close gripper",
                q_pick_low,
                self.closed_grip,
                motion.close_gripper_duration,
                on_exit="attach",
            ),
            MotionSegment("Lift cube", q_pick_high, self.closed_grip, motion.lift_cube_duration),
            MotionSegment("Transfer", q_transfer, self.closed_grip, motion.transfer_duration),
            MotionSegment("Lower to target", q_place_low, self.closed_grip, motion.lower_to_target_duration),
            MotionSegment(
                "Open gripper",
                q_place_low,
                self.open_grip,
                motion.open_gripper_duration,
                on_enter="release",
            ),
            MotionSegment("Retreat", q_retreat, self.open_grip, motion.retreat_duration),
            MotionSegment("Return home", q_home, self.open_grip, motion.return_home_duration),
        ]

    def _solve_ik(self, target: np.ndarray, seed: np.ndarray) -> np.ndarray:
        data = self.ik_data
        data.qpos[:] = self.data.qpos
        data.qvel[:] = 0.0
        data.qpos[self.arm_qpos_addr] = seed
        data.qpos[self.settings.arm_joint_count : self.settings.arm_joint_count + 2] = self.open_grip
        target = np.asarray(target, dtype=float)
        ik = self.settings.ik

        for _ in range(ik.max_iterations):
            mujoco.mj_forward(self.model, data)
            hand_pos = data.xpos[self.hand_body_id].copy()
            hand_mat = data.xmat[self.hand_body_id].reshape(3, 3).copy()
            desired_hand_pos = target - self._down_orientation @ self.tool_offset
            pos_error = desired_hand_pos - hand_pos
            orient_error = self._orientation_error(hand_mat, self._down_orientation)
            error = np.concatenate([pos_error * ik.position_weight, orient_error * ik.orientation_weight])
            if np.linalg.norm(pos_error) < ik.position_tolerance and np.linalg.norm(orient_error) < ik.orientation_tolerance:
                break

            jacp = np.zeros((3, self.model.nv))
            jacr = np.zeros((3, self.model.nv))
            mujoco.mj_jacBody(self.model, data, jacp, jacr, self.hand_body_id)
            jac = np.vstack([jacp[:, self.arm_dof_addr], jacr[:, self.arm_dof_addr] * ik.orientation_weight])
            lhs = jac @ jac.T + ik.damping * np.eye(6)
            dq = jac.T @ np.linalg.solve(lhs, error)
            dq = np.clip(dq, -ik.max_delta, ik.max_delta)

            current = data.qpos[self.arm_qpos_addr].copy()
            next_q = np.clip(
                current + dq,
                self.joint_ranges[:, 0] + ik.joint_margin,
                self.joint_ranges[:, 1] - ik.joint_margin,
            )
            data.qpos[self.arm_qpos_addr] = next_q
            data.qvel[self.arm_dof_addr] = 0.0

        mujoco.mj_forward(self.model, data)
        return data.qpos[self.arm_qpos_addr].copy()

    def _orientation_error(self, current: np.ndarray, desired: np.ndarray) -> np.ndarray:
        current_quat = np.zeros(4)
        desired_quat = np.zeros(4)
        inverse_current = np.zeros(4)
        error_quat = np.zeros(4)
        error_vel = np.zeros(3)
        mujoco.mju_mat2Quat(current_quat, current.ravel())
        mujoco.mju_mat2Quat(desired_quat, desired.ravel())
        mujoco.mju_negQuat(inverse_current, current_quat)
        mujoco.mju_mulQuat(error_quat, desired_quat, inverse_current)
        mujoco.mju_quat2Vel(error_vel, error_quat, self.settings.ik.orientation_timestep)
        return error_vel

    def _tool_center(self, data: mujoco.MjData) -> np.ndarray:
        hand_pos = data.xpos[self.hand_body_id]
        hand_mat = data.xmat[self.hand_body_id].reshape(3, 3)
        return hand_pos + hand_mat @ self.tool_offset

    def _attach_cube(self) -> None:
        self.holding_cube = True
        self._sync_cube_to_gripper()

    def _release_cube(self) -> None:
        if not self.holding_cube:
            return
        self.holding_cube = False
        cube_pos = self.data.qpos[self.box_qpos_addr : self.box_qpos_addr + 3].copy()
        cube_pos[2] = max(self.cube_half_size + self.settings.scene.cube_release_clearance, cube_pos[2])
        self._set_cube_position(cube_pos[0], cube_pos[1], cube_pos[2])

    def _sync_cube_to_gripper(self) -> None:
        grip = self._tool_center(self.data)
        grip[2] = max(self.cube_half_size + self.settings.scene.cube_release_clearance, grip[2])
        self._set_cube_position(grip[0], grip[1], grip[2])

    def _set_cube_position(self, x: float, y: float, z: float) -> None:
        qpos = self.data.qpos[self.box_qpos_addr : self.box_qpos_addr + 7]
        qpos[:3] = [float(x), float(y), float(z)]
        qpos[3:] = [1.0, 0.0, 0.0, 0.0]
        self.data.qvel[self.box_qvel_addr : self.box_qvel_addr + 6] = 0.0
        mujoco.mj_forward(self.model, self.data)

    def _set_target_marker(self, xy: np.ndarray) -> None:
        if self.model.nmocap:
            self.data.mocap_pos[0] = [float(xy[0]), float(xy[1]), self.settings.scene.target_marker_z]
            self.data.mocap_quat[0] = [1.0, 0.0, 0.0, 0.0]
        geom_id = self._name_id("geom", "pickup_pad")
        self.model.geom_pos[geom_id][:2] = self.pickup_xy

    def _settle(self, steps: int) -> None:
        hold_qpos = self.data.qpos[self.arm_qpos_addr].copy()
        for _ in range(steps):
            self.data.ctrl[self.arm_ctrl_addr] = hold_qpos
            self.data.ctrl[self.gripper_ctrl_addr] = self.open_grip
            mujoco.mj_step(self.model, self.data)
            self._set_cube_position(self.pickup_xy[0], self.pickup_xy[1], self.cube_half_size)

    def _clamp_xy(self, xy: np.ndarray) -> np.ndarray:
        bounds = self.settings.scene.marker_bounds
        return np.array(
            [
                float(np.clip(xy[0], bounds.x_min, bounds.x_max)),
                float(np.clip(xy[1], bounds.y_min, bounds.y_max)),
            ]
        )

    def _clamp_joints(self, joints: np.ndarray) -> np.ndarray:
        return np.clip(joints, self.joint_ranges[:, 0], self.joint_ranges[:, 1])

    def _joint_limits(self) -> list[dict]:
        return [
            {
                "name": name,
                "min": round(float(bounds[0]), 4),
                "max": round(float(bounds[1]), 4),
            }
            for name, bounds in zip(self.arm_joint_names, self.joint_ranges, strict=True)
        ]

    def _update_view_scene(self) -> None:
        self.renderer.update_scene(self.data, camera=self.view_camera)

    def _vector(self, values: np.ndarray | list[float]) -> list[float]:
        return [round(float(value), 3) for value in values]
