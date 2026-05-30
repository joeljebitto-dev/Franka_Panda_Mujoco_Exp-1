import { useCallback, useMemo, useRef, useState } from "react";

import * as api from "./lib/api";
import { config } from "./config/env";
import { useFrameImage } from "./hooks/useFrameImage";
import { useSimulatorState } from "./hooks/useSimulatorState";
import { useViewportInteractions } from "./hooks/useViewportInteractions";
import type {
  InteractionMode,
  ApiPayload,
  PanelName,
  SceneRequest,
  SceneTool,
  ViewMoveAction,
  ViewportTool,
  ViewPresetName,
} from "./types/simulator";
import { CommandPanel } from "./components/CommandPanel";
import { ControlPanel } from "./components/ControlPanel";
import { ModeToolPanel } from "./components/ModeToolPanel";
import { Topbar } from "./components/Topbar";
import { Viewport } from "./components/Viewport";

export function App() {
  const viewportRef = useRef<HTMLDivElement>(null);
  const [tool, setTool] = useState<ViewportTool>("orbit");
  const [activePanel, setActivePanel] = useState<PanelName>("scene");
  const { state, absorb, statusOverride, setError } = useSimulatorState();
  const frameSrc = useFrameImage(setError);

  const renderSize = useMemo<[number, number]>(
    () => state?.view?.size ?? config.fallbackRenderSize,
    [state?.view?.size],
  );

  const runCommand = useCallback(
    async <T,>(command: () => Promise<T>, errorMessage: string) => {
      try {
        absorb((await command()) as ApiPayload);
      } catch {
        setError(errorMessage);
      }
    },
    [absorb, setError],
  );

  const handleMoveView = useCallback(
    async (action: ViewMoveAction, dx: number, dy: number) => {
      absorb(await api.moveView(action, dx, dy));
    },
    [absorb],
  );

  const handleProjectMarker = useCallback(
    async (activeTool: SceneTool, screenX: number, screenY: number, width: number, height: number) => {
      absorb(await api.projectMarker(activeTool, screenX, screenY, width, height));
    },
    [absorb],
  );

  const { grabbing } = useViewportInteractions({
    viewportRef,
    tool,
    renderSize,
    onMoveView: handleMoveView,
    onProjectMarker: handleProjectMarker,
    onError: setError,
  });

  function handleModeChange(mode: InteractionMode) {
    void runCommand(() => api.setManualMode(mode), "Mode error");
    if (mode === "manual") {
      setActivePanel("manual");
    }
  }

  function handleSceneApply(payload: SceneRequest) {
    void runCommand(() => api.configureScene(payload), "Scene error");
  }

  async function handleManualApply(joints: number[], gripper: number) {
    try {
      absorb(await api.setManualJoints({ joints, gripper }));
    } catch {
      setError("Manual error");
    }
  }

  function handlePreset(preset: ViewPresetName) {
    void runCommand(() => api.setViewPreset(preset), "View error");
  }

  const runState = statusOverride ?? (state?.running ? "Running" : state?.complete ? "Complete" : "Paused");

  return (
    <main className="workspace">
      <section className="stage" aria-label="Interactive MuJoCo viewport">
        <Topbar
          activeView={state?.view?.mode}
          onPreset={handlePreset}
          onResetView={() => void runCommand(api.resetView, "View error")}
        />
        <Viewport
          activeTool={tool}
          frameSrc={frameSrc}
          grabbing={grabbing}
          phase={state?.phase ?? "Ready"}
          runState={runState}
          viewportRef={viewportRef}
        />
      </section>

      <aside className="sidebar" aria-label="Simulator controls">
        <CommandPanel
          onPause={() => void runCommand(api.pause, "Pause error")}
          onReset={() => void runCommand(api.reset, "Reset error")}
          onRun={() => void runCommand(api.start, "Run error")}
          onStep={() => void runCommand(api.step, "Step error")}
        />
        <ModeToolPanel
          mode={state?.mode ?? "auto"}
          tool={tool}
          onModeChange={handleModeChange}
          onToolChange={setTool}
        />
        <ControlPanel
          activePanel={activePanel}
          state={state}
          onManualApply={handleManualApply}
          onPanelChange={setActivePanel}
          onSceneApply={handleSceneApply}
        />
      </aside>
    </main>
  );
}
