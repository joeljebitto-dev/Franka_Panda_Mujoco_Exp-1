import type { ViewMode, ViewPresetName } from "../types/simulator";

const viewPresets: Array<{ label: string; value: ViewPresetName }> = [
  { label: "Overview", value: "overview" },
  { label: "Side", value: "side" },
  { label: "Follow Wrist", value: "wrist" },
];

interface TopbarProps {
  activeView: ViewMode | undefined;
  onPreset: (preset: ViewPresetName) => void;
  onResetView: () => void;
}

export function Topbar({ activeView, onPreset, onResetView }: TopbarProps) {
  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">MuJoCo Panda Arm</p>
        <h1>Pick-and-place simulator</h1>
      </div>

      <div className="toolbar" aria-label="View controls">
        {viewPresets.map((preset) => (
          <button
            className={activeView === preset.value ? "active" : ""}
            key={preset.value}
            type="button"
            onClick={() => onPreset(preset.value)}
          >
            {preset.label}
          </button>
        ))}
        <button type="button" onClick={onResetView}>
          Reset View
        </button>
      </div>
    </header>
  );
}
