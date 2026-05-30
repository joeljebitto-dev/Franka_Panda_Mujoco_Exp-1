import { fixed, percent, vectorLabel } from "../lib/math";
import type { SimulatorState, ViewState } from "../types/simulator";

interface TelemetryProps {
  state: SimulatorState | null;
}

export function Telemetry({ state }: TelemetryProps) {
  return (
    <div className="panel-view active">
      <h2>Telemetry</h2>
      <div className="telemetry">
        <Metric label="Progress" value={state ? percent(state.progress) : "0%"} />
        <Metric label="Cube" value={state ? vectorLabel(state.cube) : "0.50, -0.22, 0.03"} />
        <Metric label="Target gap" value={state ? `${fixed(state.distance)} m` : "0.44 m"} />
        <Metric label="Gripper" value={gripperLabel(state)} />
        <Metric label="Camera" value={state?.view ? cameraReadout(state.view) : "Overview"} />
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function gripperLabel(state: SimulatorState | null): string {
  if (!state) {
    return "Open";
  }
  if (state.holding) {
    return "Holding";
  }
  return state.gripper < 0.02 ? "Closed" : "Open";
}

function cameraReadout(view: ViewState): string {
  const label = view.mode === "wrist" ? "Follow Wrist" : view.mode.charAt(0).toUpperCase() + view.mode.slice(1);
  return `${label} ${fixed(view.distance)} m`;
}
