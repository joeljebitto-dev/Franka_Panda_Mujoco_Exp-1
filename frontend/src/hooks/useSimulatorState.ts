import { useCallback, useEffect, useState } from "react";

import { config } from "../config/env";
import { getState } from "../lib/api";
import type { ApiPayload, SimulatorState, ViewProjectResponse, ViewState } from "../types/simulator";

export function useSimulatorState() {
  const [state, setState] = useState<SimulatorState | null>(null);
  const [statusOverride, setStatusOverride] = useState<string | null>(null);

  const absorb = useCallback((payload: ApiPayload | null | undefined) => {
    if (!payload) {
      return;
    }
    setStatusOverride(null);
    if (isProjectResponse(payload)) {
      if (payload.state) {
        setState(payload.state);
      }
      return;
    }
    if (isSimulatorState(payload)) {
      setState(payload);
      return;
    }
    if (isViewState(payload)) {
      setState((current) => (current ? { ...current, view: payload } : current));
    }
  }, []);

  const setError = useCallback((message: string) => {
    setStatusOverride(message);
  }, []);

  useEffect(() => {
    let alive = true;
    let timer: number | undefined;

    async function poll() {
      try {
        const payload = await getState();
        if (alive) {
          absorb(payload);
        }
      } catch {
        if (alive) {
          setStatusOverride("Offline");
        }
      } finally {
        if (alive) {
          timer = window.setTimeout(poll, config.statePollMs);
        }
      }
    }

    poll();
    return () => {
      alive = false;
      window.clearTimeout(timer);
    };
  }, [absorb]);

  return { state, absorb, statusOverride, setError };
}

function isProjectResponse(payload: ApiPayload): payload is ViewProjectResponse {
  return "applied" in payload && "xy" in payload;
}

function isSimulatorState(payload: ApiPayload): payload is SimulatorState {
  return "phase" in payload && "joint_limits" in payload;
}

function isViewState(payload: ApiPayload): payload is ViewState {
  return "lookat" in payload && "distance" in payload && "tracking" in payload;
}
