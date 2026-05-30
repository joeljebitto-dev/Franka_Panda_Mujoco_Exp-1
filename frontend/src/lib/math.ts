export interface RenderPoint {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface PointerSnapshot {
  x: number;
  y: number;
}

export function numberValue(value: string | number): number {
  return Number.parseFloat(String(value));
}

export function fixed(value: string | number, digits = 2): string {
  return Number(value).toFixed(digits);
}

export function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function vectorLabel(values: number[], digits = 2): string {
  return values.map((value) => fixed(value, digits)).join(", ");
}

export function pointerDistance(points: PointerSnapshot[]): number | null {
  if (points.length < 2) {
    return null;
  }
  return Math.hypot(points[0].x - points[1].x, points[0].y - points[1].y);
}

export function clientPointToRenderPoint(
  clientX: number,
  clientY: number,
  viewport: HTMLElement,
  renderSize: [number, number],
): RenderPoint {
  const rect = viewport.getBoundingClientRect();
  const [renderWidth, renderHeight] = renderSize;
  if (rect.width <= 0 || rect.height <= 0 || renderWidth <= 0 || renderHeight <= 0) {
    return { x: 0, y: 0, width: renderWidth, height: renderHeight };
  }
  const renderAspect = renderWidth / renderHeight;
  const viewportAspect = rect.width / rect.height;
  const displayedWidth = viewportAspect > renderAspect ? rect.height * renderAspect : rect.width;
  const displayedHeight = viewportAspect > renderAspect ? rect.height : rect.width / renderAspect;
  const offsetX = (rect.width - displayedWidth) / 2;
  const offsetY = (rect.height - displayedHeight) / 2;
  const localX = clamp(clientX - rect.left - offsetX, 0, displayedWidth);
  const localY = clamp(clientY - rect.top - offsetY, 0, displayedHeight);
  return {
    x: (localX / displayedWidth) * renderWidth,
    y: (localY / displayedHeight) * renderHeight,
    width: renderWidth,
    height: renderHeight,
  };
}

export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}
