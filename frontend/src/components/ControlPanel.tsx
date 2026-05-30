import type { PanelName, SceneRequest, SimulatorState } from "../types/simulator";
import { ManualControls } from "./ManualControls";
import { PanelTabs } from "./PanelTabs";
import { SceneControls } from "./SceneControls";
import { Telemetry } from "./Telemetry";

interface ControlPanelProps {
  activePanel: PanelName;
  state: SimulatorState | null;
  onPanelChange: (panel: PanelName) => void;
  onSceneApply: (payload: SceneRequest) => void;
  onManualApply: (joints: number[], gripper: number) => Promise<void>;
}

export function ControlPanel({
  activePanel,
  state,
  onPanelChange,
  onSceneApply,
  onManualApply,
}: ControlPanelProps) {
  return (
    <section className="panel">
      <PanelTabs activePanel={activePanel} onChange={onPanelChange} />
      {activePanel === "scene" ? <SceneControls state={state} onApply={onSceneApply} /> : null}
      {activePanel === "manual" ? <ManualControls state={state} onApply={onManualApply} /> : null}
      {activePanel === "telemetry" ? <Telemetry state={state} /> : null}
    </section>
  );
}
