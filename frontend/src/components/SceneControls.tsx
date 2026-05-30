import { useEffect, useRef, useState } from "react";

import { config } from "../config/env";
import { fixed, numberValue } from "../lib/math";
import type { SceneRequest, SimulatorState } from "../types/simulator";

interface SceneValues {
  pickupX: number;
  pickupY: number;
  targetX: number;
  targetY: number;
}

interface SceneControlsProps {
  state: SimulatorState | null;
  onApply: (payload: SceneRequest) => void;
}

export function SceneControls({ state, onApply }: SceneControlsProps) {
  const editingRef = useRef(false);
  const [values, setValues] = useState<SceneValues>({
    pickupX: config.scene.pickupDefault[0],
    pickupY: config.scene.pickupDefault[1],
    targetX: config.scene.targetDefault[0],
    targetY: config.scene.targetDefault[1],
  });

  useEffect(() => {
    if (!state || editingRef.current) {
      return;
    }
    setValues({
      pickupX: state.pickup[0],
      pickupY: state.pickup[1],
      targetX: state.target[0],
      targetY: state.target[1],
    });
  }, [state]);

  function updateValue(key: keyof SceneValues, rawValue: string) {
    editingRef.current = true;
    setValues((current) => ({ ...current, [key]: numberValue(rawValue) }));
  }

  function endEditing() {
    editingRef.current = false;
  }

  function apply() {
    onApply({
      pickup_x: values.pickupX,
      pickup_y: values.pickupY,
      target_x: values.targetX,
      target_y: values.targetY,
    });
  }

  return (
    <div className="panel-view active">
      <div className="section-heading">
        <h2>Scene Markers</h2>
        <button className="compact" type="button" onClick={apply}>
          Apply
        </button>
      </div>
      <RangeRow
        label="Pickup X"
        max={config.scene.xMax}
        min={config.scene.xMin}
        step={config.scene.step}
        value={values.pickupX}
        onBlur={endEditing}
        onChange={(value) => updateValue("pickupX", value)}
      />
      <RangeRow
        label="Pickup Y"
        max={config.scene.yMax}
        min={config.scene.yMin}
        step={config.scene.step}
        value={values.pickupY}
        onBlur={endEditing}
        onChange={(value) => updateValue("pickupY", value)}
      />
      <RangeRow
        label="Target X"
        max={config.scene.xMax}
        min={config.scene.xMin}
        step={config.scene.step}
        value={values.targetX}
        onBlur={endEditing}
        onChange={(value) => updateValue("targetX", value)}
      />
      <RangeRow
        label="Target Y"
        max={config.scene.yMax}
        min={config.scene.yMin}
        step={config.scene.step}
        value={values.targetY}
        onBlur={endEditing}
        onChange={(value) => updateValue("targetY", value)}
      />
    </div>
  );
}

interface RangeRowProps {
  label: string;
  min: number;
  max: number;
  step: number;
  value: number;
  onChange: (value: string) => void;
  onBlur: () => void;
}

function RangeRow({ label, min, max, step, value, onChange, onBlur }: RangeRowProps) {
  return (
    <label>
      {label}
      <input
        max={max}
        min={min}
        step={step}
        type="range"
        value={value}
        onBlur={onBlur}
        onPointerUp={onBlur}
        onChange={(event) => onChange(event.currentTarget.value)}
      />
      <output>{fixed(value)}</output>
    </label>
  );
}
