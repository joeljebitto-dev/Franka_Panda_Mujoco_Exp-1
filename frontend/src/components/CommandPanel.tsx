interface CommandPanelProps {
  onRun: () => void;
  onPause: () => void;
  onStep: () => void;
  onReset: () => void;
}

export function CommandPanel({ onRun, onPause, onStep, onReset }: CommandPanelProps) {
  return (
    <section className="panel command-panel">
      <button className="primary" type="button" onClick={onRun}>
        Run Pick
      </button>
      <button type="button" onClick={onPause}>
        Pause
      </button>
      <button type="button" onClick={onStep}>
        Step
      </button>
      <button className="danger" type="button" onClick={onReset}>
        Reset
      </button>
    </section>
  );
}
