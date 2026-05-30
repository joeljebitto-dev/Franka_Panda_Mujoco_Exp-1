import type { InteractionMode, ViewportTool } from "../types/simulator";

interface ModeToolPanelProps {
  mode: InteractionMode;
  tool: ViewportTool;
  onModeChange: (mode: InteractionMode) => void;
  onToolChange: (tool: ViewportTool) => void;
}

export function ModeToolPanel({ mode, tool, onModeChange, onToolChange }: ModeToolPanelProps) {
  return (
    <section className="panel">
      <div className="segmented" aria-label="Interaction mode">
        {(["auto", "manual"] as const).map((nextMode) => (
          <button
            className={mode === nextMode ? "active" : ""}
            key={nextMode}
            type="button"
            onClick={() => onModeChange(nextMode)}
          >
            {nextMode === "auto" ? "Auto" : "Manual"}
          </button>
        ))}
      </div>
      <div className="segmented tool-segment" aria-label="Viewport tool">
        {(["orbit", "pickup", "target"] as const).map((nextTool) => (
          <button
            className={tool === nextTool ? "active" : ""}
            key={nextTool}
            type="button"
            onClick={() => onToolChange(nextTool)}
          >
            {nextTool === "orbit" ? "Orbit" : nextTool === "pickup" ? "Pickup" : "Target"}
          </button>
        ))}
      </div>
    </section>
  );
}
