import './Gauge.css';

/**
 * Medidor circular SVG del índice de riesgo.
 * props: value (0-100), nivel ("Bajo"|"Medio"|"Alto")
 */
export default function Gauge({ value = 0, nivel = 'Bajo' }) {
  const R = 80;
  const cx = 100, cy = 100;
  const circunferencia = Math.PI * R;          // semicírculo
  const progreso = (value / 100) * circunferencia;

  const colorMap = { Bajo: '#27ae60', Medio: '#f39c12', Alto: '#e74c3c' };
  const color = colorMap[nivel] || '#27ae60';

  // Ángulo de la aguja (-90° a 90°, mapeado a value 0-100)
  const angulo = -90 + (value / 100) * 180;

  return (
    <div className="gauge-container">
      <svg viewBox="0 0 200 110" className="gauge-svg">
        {/* Fondo del arco */}
        <path
          d={`M ${cx - R} ${cy} A ${R} ${R} 0 0 1 ${cx + R} ${cy}`}
          fill="none" stroke="#dce3ed" strokeWidth="18" strokeLinecap="round"
        />
        {/* Arco de progreso */}
        <path
          d={`M ${cx - R} ${cy} A ${R} ${R} 0 0 1 ${cx + R} ${cy}`}
          fill="none"
          stroke={color}
          strokeWidth="18"
          strokeLinecap="round"
          strokeDasharray={`${progreso} ${circunferencia}`}
          style={{ transition: 'stroke-dasharray 0.6s ease' }}
        />
        {/* Aguja */}
        <line
          x1={cx} y1={cy}
          x2={cx + Math.cos((angulo * Math.PI) / 180) * 60}
          y2={cy + Math.sin((angulo * Math.PI) / 180) * 60}
          stroke={color} strokeWidth="3" strokeLinecap="round"
          style={{ transition: 'all 0.6s ease' }}
        />
        <circle cx={cx} cy={cy} r="6" fill={color} />
        {/* Etiquetas */}
        <text x="22" y="108" fontSize="10" fill="var(--color-text-muted)">0</text>
        <text x="96" y="22" fontSize="10" fill="var(--color-text-muted)" textAnchor="middle">50</text>
        <text x="174" y="108" fontSize="10" fill="var(--color-text-muted)">100</text>
      </svg>
      <div className="gauge-value" style={{ color }}>
        <span className="gauge-number">{value}</span>
        <span className="gauge-label">{nivel}</span>
      </div>
    </div>
  );
}
