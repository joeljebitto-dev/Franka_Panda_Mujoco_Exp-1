import { RefObject } from "react";

import type { ViewportTool } from "../types/simulator";

interface ViewportProps {
  viewportRef: RefObject<HTMLDivElement>;
  frameSrc: string;
  grabbing: boolean;
  phase: string;
  runState: string;
  activeTool: ViewportTool;
}

export function Viewport({ viewportRef, frameSrc, grabbing, phase, runState, activeTool }: ViewportProps) {
  const toolLabel = activeTool === "orbit" ? "Orbit" : activeTool === "pickup" ? "Move Pickup" : "Move Target";

  return (
    <div
      ref={viewportRef}
      className={`viewport ${grabbing ? "grabbing" : ""} ${activeTool !== "orbit" ? "marker-tool" : ""}`}
      aria-label="Live 3D robot viewport"
    >
      {frameSrc ? (
        <img alt="Live MuJoCo render of the robot arm moving a cube" draggable={false} src={frameSrc} />
      ) : (
        <div className="viewport-empty">Waiting for renderer</div>
      )}
      <div className="viewport-hud">
        <span>{phase}</span>
        <span>{runState}</span>
        <span>{toolLabel}</span>
      </div>
    </div>
  );
}
