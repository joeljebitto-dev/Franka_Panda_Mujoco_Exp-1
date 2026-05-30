import type { PanelName } from "../types/simulator";

const tabs: Array<{ label: string; value: PanelName }> = [
  { label: "Scene", value: "scene" },
  { label: "Manual", value: "manual" },
  { label: "Telemetry", value: "telemetry" },
];

interface PanelTabsProps {
  activePanel: PanelName;
  onChange: (panel: PanelName) => void;
}

export function PanelTabs({ activePanel, onChange }: PanelTabsProps) {
  return (
    <div className="panel-tabs" aria-label="Control panel tabs">
      {tabs.map((tab) => (
        <button
          className={activePanel === tab.value ? "active" : ""}
          key={tab.value}
          type="button"
          onClick={() => onChange(tab.value)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
