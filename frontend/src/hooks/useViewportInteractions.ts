import { RefObject, useEffect, useRef, useState } from "react";

import { config } from "../config/env";
import { clientPointToRenderPoint, pointerDistance } from "../lib/math";
import type { SceneTool, ViewMoveAction, ViewportTool } from "../types/simulator";

interface PointerState {
  x: number;
  y: number;
  lastX?: number;
  lastY?: number;
}

interface PendingPoint {
  clientX: number;
  clientY: number;
}

interface ViewMove {
  action: ViewMoveAction;
  dx: number;
  dy: number;
}

interface UseViewportInteractionsOptions {
  viewportRef: RefObject<HTMLDivElement>;
  tool: ViewportTool;
  renderSize: [number, number];
  onMoveView: (action: ViewMoveAction, dx: number, dy: number) => Promise<void>;
  onProjectMarker: (tool: SceneTool, screenX: number, screenY: number, width: number, height: number) => Promise<void>;
  onError: (message: string) => void;
}

export function useViewportInteractions({
  viewportRef,
  tool,
  renderSize,
  onMoveView,
  onProjectMarker,
  onError,
}: UseViewportInteractionsOptions) {
  const [grabbing, setGrabbing] = useState(false);
  const latest = useRef({ tool, renderSize, onMoveView, onProjectMarker, onError });
  const pointers = useRef(new Map<number, PointerState>());
  const pointerMode = useRef<ViewMoveAction | "marker" | "pinch" | null>(null);
  const pinchDistance = useRef<number | null>(null);
  const viewBusy = useRef(false);
  const pendingViewMove = useRef<ViewMove | null>(null);
  const markerBusy = useRef(false);
  const pendingMarkerPoint = useRef<PendingPoint | null>(null);

  latest.current = { tool, renderSize, onMoveView, onProjectMarker, onError };

  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport) {
      return;
    }
    const element = viewport;

    function enqueueViewMove(action: ViewMoveAction, dx: number, dy: number) {
      if (viewBusy.current) {
        pendingViewMove.current = pendingViewMove.current
          ? {
              action,
              dx: pendingViewMove.current.dx + dx,
              dy: pendingViewMove.current.dy + dy,
            }
          : { action, dx, dy };
        return;
      }

      viewBusy.current = true;
      latest.current
        .onMoveView(action, dx, dy)
        .catch(() => latest.current.onError("View error"))
        .finally(() => {
          viewBusy.current = false;
          if (pendingViewMove.current) {
            const pending = pendingViewMove.current;
            pendingViewMove.current = null;
            enqueueViewMove(pending.action, pending.dx, pending.dy);
          }
        });
    }

    function enqueueMarkerProjection(point: PendingPoint) {
      pendingMarkerPoint.current = point;
      if (markerBusy.current) {
        return;
      }
      markerBusy.current = true;
      window.setTimeout(() => {
        const pending = pendingMarkerPoint.current;
        pendingMarkerPoint.current = null;
        if (!pending || !viewportRef.current) {
          markerBusy.current = false;
          return;
        }
        const renderPoint = clientPointToRenderPoint(
          pending.clientX,
          pending.clientY,
          viewportRef.current,
          latest.current.renderSize,
        );
        const activeTool = latest.current.tool;
        if (activeTool === "orbit") {
          markerBusy.current = false;
          return;
        }
        latest.current
          .onProjectMarker(activeTool, renderPoint.x, renderPoint.y, renderPoint.width, renderPoint.height)
          .catch(() => latest.current.onError("Marker error"))
          .finally(() => {
            markerBusy.current = false;
            if (pendingMarkerPoint.current) {
              enqueueMarkerProjection(pendingMarkerPoint.current);
            }
          });
      }, config.markerDebounceMs);
    }

    function onContextMenu(event: MouseEvent) {
      event.preventDefault();
    }

    function onPointerDown(event: PointerEvent) {
      event.preventDefault();
      element.setPointerCapture(event.pointerId);
      pointers.current.set(event.pointerId, { x: event.clientX, y: event.clientY });
      setGrabbing(true);

      if (pointers.current.size === 2) {
        pointerMode.current = "pinch";
        pinchDistance.current = pointerDistance(Array.from(pointers.current.values()));
        return;
      }

      if (latest.current.tool !== "orbit" && event.button === 0 && !event.shiftKey) {
        pointerMode.current = "marker";
        enqueueMarkerProjection({ clientX: event.clientX, clientY: event.clientY });
        return;
      }

      pointerMode.current = event.shiftKey || event.button === 1 || event.button === 2 ? "pan" : "orbit";
      pointers.current.set(event.pointerId, {
        x: event.clientX,
        y: event.clientY,
        lastX: event.clientX,
        lastY: event.clientY,
      });
    }

    function onPointerMove(event: PointerEvent) {
      const pointer = pointers.current.get(event.pointerId);
      if (!pointer) {
        return;
      }
      event.preventDefault();
      pointer.x = event.clientX;
      pointer.y = event.clientY;
      pointers.current.set(event.pointerId, pointer);

      if (pointerMode.current === "pinch") {
        const currentDistance = pointerDistance(Array.from(pointers.current.values()));
        if (currentDistance && pinchDistance.current) {
          const delta = (currentDistance - pinchDistance.current) / config.pinchSensitivity;
          enqueueViewMove("zoom", 0, delta);
          pinchDistance.current = currentDistance;
        }
        return;
      }

      if (pointerMode.current === "marker") {
        enqueueMarkerProjection({ clientX: event.clientX, clientY: event.clientY });
        return;
      }

      const rect = element.getBoundingClientRect();
      const dx = (event.clientX - (pointer.lastX ?? event.clientX)) / rect.width;
      const dy = (event.clientY - (pointer.lastY ?? event.clientY)) / rect.height;
      pointer.lastX = event.clientX;
      pointer.lastY = event.clientY;
      enqueueViewMove(pointerMode.current === "pan" ? "pan" : "orbit", dx, dy);
    }

    function endPointer(event: PointerEvent) {
      pointers.current.delete(event.pointerId);
      if (!pointers.current.size) {
        pointerMode.current = null;
        pinchDistance.current = null;
        setGrabbing(false);
      }
    }

    function onPointerLeave(event: PointerEvent) {
      if (event.buttons === 0) {
        endPointer(event);
      }
    }

    function onWheel(event: WheelEvent) {
      event.preventDefault();
      enqueueViewMove("zoom", 0, -event.deltaY / config.wheelZoomSensitivity);
    }

    element.addEventListener("contextmenu", onContextMenu);
    element.addEventListener("pointerdown", onPointerDown);
    element.addEventListener("pointermove", onPointerMove);
    element.addEventListener("pointerup", endPointer);
    element.addEventListener("pointercancel", endPointer);
    element.addEventListener("pointerleave", onPointerLeave);
    element.addEventListener("wheel", onWheel, { passive: false });

    return () => {
      element.removeEventListener("contextmenu", onContextMenu);
      element.removeEventListener("pointerdown", onPointerDown);
      element.removeEventListener("pointermove", onPointerMove);
      element.removeEventListener("pointerup", endPointer);
      element.removeEventListener("pointercancel", endPointer);
      element.removeEventListener("pointerleave", onPointerLeave);
      element.removeEventListener("wheel", onWheel);
    };
  }, [viewportRef]);

  return { grabbing };
}
