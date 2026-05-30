export type ViewPresetName = "overview" | "side" | "wrist";
export type CameraName = ViewPresetName;
export type ViewMode = ViewPresetName | "custom";
export type ViewMoveAction = "orbit" | "pan" | "zoom";
export type InteractionMode = "auto" | "manual";
export type SceneTool = "pickup" | "target";
export type ViewportTool = "orbit" | SceneTool;
export type PanelName = "scene" | "manual" | "telemetry";

export interface ViewState {
  mode: ViewMode;
  lookat: number[];
  distance: number;
  azimuth: number;
  elevation: number;
  tracking: boolean;
  size: [number, number];
}

export interface JointLimit {
  name: string;
  min: number;
  max: number;
}

export interface SimulatorState {
  time: number;
  running: boolean;
  mode: InteractionMode;
  phase: string;
  progress: number;
  holding: boolean;
  complete: boolean;
  success: boolean;
  camera: CameraName;
  view: ViewState;
  cube: number[];
  target: number[];
  pickup: number[];
  tool: number[];
  distance: number;
  joints: number[];
  joint_limits: JointLimit[];
  manual_targets: number[];
  gripper: number;
}

export interface SceneRequest {
  pickup_x: number;
  pickup_y: number;
  target_x: number;
  target_y: number;
}

export interface ViewMoveRequest {
  action: ViewMoveAction;
  dx: number;
  dy: number;
}

export interface ViewProjectRequest {
  screen_x: number;
  screen_y: number;
  viewport_width: number;
  viewport_height: number;
  tool: SceneTool;
  apply: boolean;
}

export interface ViewProjectResponse {
  xy: number[];
  tool: SceneTool | null;
  applied: boolean;
  state: SimulatorState | null;
}

export interface ManualModeRequest {
  mode: InteractionMode;
}

export interface ManualJointsRequest {
  joints: number[];
  gripper: number;
}

export type ApiPayload = SimulatorState | ViewState | ViewProjectResponse | { state?: SimulatorState | null };
