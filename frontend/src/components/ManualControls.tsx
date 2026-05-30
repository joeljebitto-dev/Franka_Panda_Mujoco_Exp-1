import { config } from "../config/env";
import { fixed, numberValue } from "../lib/math";
import type { SimulatorState } from "../types/simulator";
import { useManualControls } from "../hooks/useManualControls";

interface ManualControlsProps {
  state: SimulatorState | null;
  onApply: (joints: number[], gripper: number) => Promise<void>;
}

export function ManualControls({ state, onApply }: ManualControlsProps) {
  const { joints, gripper, updateJoint, updateGripper, endEditing } = useManualControls(state, onApply);
  const limits = state?.joint_limits ?? [];

  return (
    <div className="panel-view active">
      <div className="section-heading">
        <h2>Joint Targets</h2>
        <span className="status-pill">{state?.mode === "manual" ? "Manual" : "Auto"}</span>
      </div>
      <div className="manual-joints">
        {limits.map((limit, index) => (
          <label className="manual-row" key={limit.name}>
            <span>{`J${index + 1}`}</span>
            <input
              max={limit.max}
              min={limit.min}
              step={config.jointStep}
              type="range"
              value={joints[index] ?? state?.joints[index] ?? 0}
              onBlur={endEditing}
              onPointerUp={endEditing}
              onChange={(event) => updateJoint(index, numberValue(event.currentTarget.value))}
            />
            <output>{fixed(joints[index] ?? state?.joints[index] ?? 0, 3)}</output>
          </label>
        ))}
      </div>
      <label className="manual-row">
        <span>Grip</span>
        <input
          max={config.gripper.max}
          min={config.gripper.min}
          step={config.gripper.step}
          type="range"
          value={gripper}
          onBlur={endEditing}
          onPointerUp={endEditing}
          onChange={(event) => updateGripper(numberValue(event.currentTarget.value))}
        />
        <output>{fixed(gripper, 3)}</output>
      </label>
    </div>
  );
}
