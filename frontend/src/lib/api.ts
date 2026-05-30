import { config } from "../config/env";
import type {
  InteractionMode,
  ManualJointsRequest,
  SceneRequest,
  SceneTool,
  SimulatorState,
  ViewMoveAction,
  ViewProjectResponse,
  ViewState,
} from "../types/simulator";

export async function getState(): Promise<SimulatorState> {
  return requestJson<SimulatorState>("/api/state");
}

export function frameUrl(): string {
  return apiUrl(`/api/frame.jpg?t=${Date.now()}`);
}

export function start(): Promise<SimulatorState> {
  return postJson<SimulatorState>("/api/start");
}

export function pause(): Promise<SimulatorState> {
  return postJson<SimulatorState>("/api/pause");
}

export function step(): Promise<SimulatorState> {
  return postJson<SimulatorState>("/api/step");
}

export function reset(): Promise<SimulatorState> {
  return postJson<SimulatorState>("/api/reset");
}

export function configureScene(payload: SceneRequest): Promise<SimulatorState> {
  return postJson<SimulatorState>("/api/scene", payload);
}

export function resetView(): Promise<ViewState> {
  return postJson<ViewState>("/api/view/reset");
}

export function setViewPreset(preset: string): Promise<ViewState> {
  return postJson<ViewState>(`/api/view/preset/${preset}`);
}

export function moveView(action: ViewMoveAction, dx: number, dy: number): Promise<ViewState> {
  return postJson<ViewState>("/api/view", { action, dx, dy });
}

export function projectMarker(
  tool: SceneTool,
  screenX: number,
  screenY: number,
  width: number,
  height: number,
): Promise<ViewProjectResponse> {
  return postJson<ViewProjectResponse>("/api/view/project", {
    screen_x: screenX,
    screen_y: screenY,
    viewport_width: width,
    viewport_height: height,
    tool,
    apply: true,
  });
}

export function setManualMode(mode: InteractionMode): Promise<SimulatorState> {
  return postJson<SimulatorState>("/api/manual/mode", { mode });
}

export function setManualJoints(payload: ManualJointsRequest): Promise<SimulatorState> {
  return postJson<SimulatorState>("/api/manual/joints", payload);
}

async function postJson<T>(path: string, body?: unknown): Promise<T> {
  return requestJson<T>(path, {
    method: "POST",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), {
    cache: "no-store",
    ...init,
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

function apiUrl(path: string): string {
  if (!config.apiBaseUrl) {
    return path;
  }
  return `${config.apiBaseUrl.replace(/\/$/, "")}/${path.replace(/^\//, "")}`;
}
