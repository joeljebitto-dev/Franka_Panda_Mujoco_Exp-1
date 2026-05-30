interface FrontendConfig {
  apiBaseUrl: string;
  statePollMs: number;
  frameRefreshMs: number;
  frameRetryMs: number;
  manualDebounceMs: number;
  markerDebounceMs: number;
  fallbackRenderSize: [number, number];
  pinchSensitivity: number;
  wheelZoomSensitivity: number;
  scene: {
    pickupDefault: [number, number];
    targetDefault: [number, number];
    xMin: number;
    xMax: number;
    yMin: number;
    yMax: number;
    step: number;
  };
  gripper: {
    min: number;
    max: number;
    step: number;
  };
  jointStep: number;
}

const env = import.meta.env;

export const config: FrontendConfig = {
  apiBaseUrl: env.VITE_API_BASE_URL || "",
  statePollMs: positiveNumber("VITE_STATE_POLL_MS", 500),
  frameRefreshMs: positiveNumber("VITE_FRAME_REFRESH_MS", 45),
  frameRetryMs: positiveNumber("VITE_FRAME_RETRY_MS", 650),
  manualDebounceMs: positiveNumber("VITE_MANUAL_DEBOUNCE_MS", 90),
  markerDebounceMs: positiveNumber("VITE_MARKER_DEBOUNCE_MS", 65),
  fallbackRenderSize: [
    positiveNumber("VITE_FALLBACK_RENDER_WIDTH", 640),
    positiveNumber("VITE_FALLBACK_RENDER_HEIGHT", 426),
  ],
  pinchSensitivity: positiveNumber("VITE_PINCH_SENSITIVITY", 240),
  wheelZoomSensitivity: positiveNumber("VITE_WHEEL_ZOOM_SENSITIVITY", 650),
  scene: {
    pickupDefault: [numberEnv("VITE_PICKUP_DEFAULT_X", 0.5), numberEnv("VITE_PICKUP_DEFAULT_Y", -0.22)],
    targetDefault: [numberEnv("VITE_TARGET_DEFAULT_X", 0.5), numberEnv("VITE_TARGET_DEFAULT_Y", 0.22)],
    xMin: numberEnv("VITE_SCENE_X_MIN", 0.32),
    xMax: numberEnv("VITE_SCENE_X_MAX", 0.68),
    yMin: numberEnv("VITE_SCENE_Y_MIN", -0.34),
    yMax: numberEnv("VITE_SCENE_Y_MAX", 0.34),
    step: positiveNumber("VITE_SCENE_STEP", 0.01),
  },
  gripper: {
    min: positiveNumber("VITE_GRIPPER_MIN", 0.012),
    max: positiveNumber("VITE_GRIPPER_MAX", 0.04),
    step: positiveNumber("VITE_GRIPPER_STEP", 0.001),
  },
  jointStep: positiveNumber("VITE_JOINT_STEP", 0.001),
};

validateConfig(config);

function numberEnv(key: string, fallback: number): number {
  const raw = env[key];
  if (raw === undefined || raw === "") {
    return fallback;
  }
  const value = Number(raw);
  if (!Number.isFinite(value)) {
    throw new Error(`${key} must be a number`);
  }
  return value;
}

function positiveNumber(key: string, fallback: number): number {
  const value = numberEnv(key, fallback);
  if (value <= 0) {
    throw new Error(`${key} must be greater than 0`);
  }
  return value;
}

function validateConfig(value: FrontendConfig): void {
  if (value.scene.xMin >= value.scene.xMax) {
    throw new Error("VITE_SCENE_X_MIN must be less than VITE_SCENE_X_MAX");
  }
  if (value.scene.yMin >= value.scene.yMax) {
    throw new Error("VITE_SCENE_Y_MIN must be less than VITE_SCENE_Y_MAX");
  }
  if (value.gripper.min >= value.gripper.max) {
    throw new Error("VITE_GRIPPER_MIN must be less than VITE_GRIPPER_MAX");
  }
}
