import './ProgressBar.css';

export default function ProgressBar({ label, value = 0, max = 100, color }) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div className="progress-bar">
      <div className="progress-bar__header">
        <span className="progress-bar__label">{label}</span>
        <span className="progress-bar__value">{value}</span>
      </div>
      <div className="progress-bar__track">
        <div
          className="progress-bar__fill"
          style={{ width: `${pct}%`, background: color || 'var(--color-accent)' }}
        />
      </div>
    </div>
  );
}
