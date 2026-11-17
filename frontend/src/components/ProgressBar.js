import './ProgressBar.css';

export default function ProgressBar({ label, value = 0, color = 'var(--accent)', weight, icon }) {
  return (
    <div className="progress-bar">
      <div className="progress-bar__header">
        <div className="progress-bar__label-wrap">
          {icon && <span className="progress-bar__icon" aria-hidden="true">{icon}</span>}
          <span className="progress-bar__label">{label}</span>
        </div>
        {weight && <span className="progress-bar__weight">{weight}</span>}
      </div>
      <div className="progress-bar__body">
        <div className="progress-bar__track">
          <div className="progress-bar__fill"
            style={{ width: `${Math.min(value, 100)}%`, background: color }} />
        </div>
        <span className="progress-bar__value">{Math.round(value)} / 100</span>
      </div>
    </div>
  );
}
