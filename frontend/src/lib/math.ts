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
  return {
    x: ((clientX - rect.left) / rect.width) * renderSize[0],
    y: ((clientY - rect.top) / rect.height) * renderSize[1],
    width: renderSize[0],
    height: renderSize[1],
  };
}

export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}
