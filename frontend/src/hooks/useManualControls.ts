import { useCallback, useEffect, useRef, useState } from "react";

import { config } from "../config/env";
import type { SimulatorState } from "../types/simulator";
import { useDebouncedCallback } from "./useDebouncedCallback";

export function useManualControls(
  state: SimulatorState | null,
  onApply: (joints: number[], gripper: number) => void | Promise<void>,
) {
  const editingRef = useRef(false);
  const [joints, setJoints] = useState<number[]>([]);
  const [gripper, setGripper] = useState(config.gripper.max);
  const scheduleApply = useDebouncedCallback(onApply, config.manualDebounceMs);

  useEffect(() => {
    if (!state || editingRef.current) {
      return;
    }
    setJoints(state.manual_targets);
    setGripper(state.gripper);
  }, [state]);

  const updateJoint = useCallback(
    (index: number, value: number) => {
      editingRef.current = true;
      setJoints((current) => {
        const next = current.length ? [...current] : [...(state?.manual_targets ?? [])];
        next[index] = value;
        scheduleApply(next, gripper);
        return next;
      });
    },
    [gripper, scheduleApply, state],
  );

  const updateGripper = useCallback(
    (value: number) => {
      editingRef.current = true;
      setGripper(value);
      const currentJoints = joints.length ? joints : (state?.manual_targets ?? []);
      if (currentJoints.length) {
        scheduleApply(currentJoints, value);
      }
    },
    [joints, scheduleApply, state],
  );

  const endEditing = useCallback(() => {
    editingRef.current = false;
  }, []);

  return { joints, gripper, updateJoint, updateGripper, endEditing };
}
