import './Gauge.css';

const COLOR_MAP = { Bajo: '#16A34A', Medio: '#CA8A04', Alto: '#DC2626' };
const BG_MAP    = { Bajo: '#DCFCE7', Medio: '#FEF9C3', Alto: '#FEE2E2' };

export default function Gauge({ value = 0, nivel = 'Bajo' }) {
  const sinDatos = !COLOR_MAP[nivel];
  const color  = COLOR_MAP[nivel] ?? '#64748B';
  const bgPill = BG_MAP[nivel]    ?? '#F1F5F9';
  const label  = sinDatos ? 'SIN DATOS' : nivel === 'Medio' ? 'RIESGO MEDIO' : nivel === 'Alto' ? 'RIESGO ALTO' : 'RIESGO BAJO';
  const pct    = Math.max(0, Math.min(value, 100)) / 100;

  const R       = 50;
  const C       = 2 * Math.PI * R;  // ≈ 314.16
  const arcLen  = C * 0.75;         // 270° ≈ 235.6
  const fillLen = arcLen * pct;

  return (
    <div className="gauge-container">
      <div className="gauge-wrap">
        <svg width="120" height="120" viewBox="0 0 120 120" aria-hidden="true">
          {/* Gray track – 270° arc, gap centered at bottom */}
          <circle
            cx="60" cy="60" r={R}
            fill="none" stroke="#E2E8F0" strokeWidth="10" strokeLinecap="round"
            strokeDasharray={`${arcLen} ${C - arcLen}`}
            transform="rotate(-45 60 60)"
          />
          {/* Colored progress arc */}
          {fillLen > 0.5 && (
            <circle
              cx="60" cy="60" r={R}
              fill="none" stroke={color} strokeWidth="10" strokeLinecap="round"
              strokeDasharray={`${fillLen} ${C - fillLen}`}
              transform="rotate(-45 60 60)"
            />
          )}
        </svg>
        <span className="gauge-number" aria-label={sinDatos ? 'Índice de riesgo sin datos' : `Índice de riesgo ${value} de 100`}>{sinDatos ? '—' : typeof value === 'number' ? value.toFixed(1) : value}</span>
      </div>

      <div className="gauge-pill" style={{ background: bgPill, color }}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <circle cx="8" cy="8" r="6.5" stroke="currentColor" strokeWidth="1.5"/>
          <path d="M5.5 8.5l2 2 3-3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <span>{label}</span>
      </div>
    </div>
  );
}
