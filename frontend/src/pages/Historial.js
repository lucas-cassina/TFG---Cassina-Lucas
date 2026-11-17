import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LineChart, Line, Tooltip, ResponsiveContainer } from 'recharts';
import { indiceAPI } from '../api/client';
import { useAuth } from '../context/AuthContext';
import Spinner from '../components/Spinner';
import BottomNav from '../components/BottomNav';
import AppHeader from '../components/AppHeader';
import './Historial.css';

const FILTROS = [
  { label: 'Esta semana',     key: 'semana' },
  { label: 'Este mes',        key: 'mes' },
  { label: 'Últimos 3 meses', key: 'trimestre' },
  { label: 'Personalizado',   key: 'custom', hasIcon: true },
];

function getDesde(key) {
  const d = new Date();
  if (key === 'semana')    { d.setDate(d.getDate() - 7); return d.toISOString(); }
  if (key === 'mes')       { d.setDate(1); d.setHours(0,0,0,0); return d.toISOString(); }
  if (key === 'trimestre') { d.setDate(d.getDate() - 90); return d.toISOString(); }
  return undefined;
}

function getNombrePeriodo(key) {
  const now = new Date();
  const MESES = ['Enero','Febrero','Marzo','Abril','Mayo','Junio',
                 'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
  if (key === 'mes')       return `${MESES[now.getMonth()]} ${now.getFullYear()}`;
  if (key === 'semana')    return 'Esta semana';
  if (key === 'trimestre') return 'Últimos 3 meses';
  return 'Personalizado';
}

function formatFecha(isoStr) {
  const d = new Date(isoStr);
  const hoy = new Date();
  const ayer = new Date(); ayer.setDate(ayer.getDate() - 1);
  const hora = d.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' });
  if (d.toDateString() === hoy.toDateString())  return `Hoy, ${hora} hs`;
  if (d.toDateString() === ayer.toDateString()) return `Ayer, ${hora} hs`;
  return `${d.toLocaleDateString('es-AR', { day:'2-digit', month:'2-digit' })}, ${hora} hs`;
}

function duracionMin(inicio, fin) {
  if (!fin) return null;
  return Math.round((new Date(fin) - new Date(inicio)) / 60000);
}

const NIVEL_CFG = {
  Bajo:  { emoji: '🟢', label: 'BAJO',  cls: 'bajo'  },
  Medio: { emoji: '🟡', label: 'MEDIO', cls: 'medio' },
  Alto:  { emoji: '🔴', label: 'ALTO',  cls: 'alto'  },
};

export default function Historial() {
  const { user } = useAuth();
  const navigate  = useNavigate();
  const [sesiones, setSesiones] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [filtro, setFiltro]     = useState('mes');
  const [error, setError]       = useState('');
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');

  const cargar = (key, rango) => {
    setLoading(true);
    setError('');
    const desde = getDesde(key);
    (async () => {
      const params = rango || (desde ? { desde } : {});
      const todas = [];
      let pagina;
      do {
        const respuesta = await indiceAPI.historial({ ...params, limite: 100, offset: todas.length });
        pagina = respuesta.data || [];
        todas.push(...pagina);
      } while (pagina.length === 100);
      return todas;
    })()
      .then(setSesiones)
      .catch(() => setError('No pudimos cargar el historial para este período.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { cargar('mes'); }, []);

  const handleFiltro = (key) => {
    if (key === 'custom') { setFiltro(key); return; }
    setFiltro(key);
    cargar(key);
  };

  const aplicarRango = (event) => {
    event.preventDefault();
    if (!fechaDesde || !fechaHasta || fechaDesde > fechaHasta) {
      setError('Elegí una fecha de inicio y una de fin posterior o igual.');
      return;
    }
    cargar('custom', {
      desde: new Date(`${fechaDesde}T00:00:00`).toISOString(),
      hasta: new Date(`${fechaHasta}T23:59:59.999`).toISOString(),
    });
  };

  /* ── Stats calculados ── */
  const promedioIndice = (() => {
    const vals = sesiones.map(s => s.indice).filter(v => v != null);
    return vals.length ? Math.round(vals.reduce((a,b) => a+b,0) / vals.length) : 0;
  })();
  const totalKm       = sesiones.reduce((acc,s) => acc + (s.distancia_km || 0), 0);
  const eventosRiesgo = sesiones.filter(s => s.nivel && s.nivel !== 'Bajo').length;

  const chartData = sesiones
    .filter(s => s.indice != null)
    .slice()
    .reverse()
    
    .map(s => ({
      f: new Date(s.inicio).toLocaleDateString('es-AR', { day:'2-digit', month:'2-digit' }),
      v: Math.round(s.indice),
    }));

  const chartMax = chartData.length ? Math.max(...chartData.map(d => d.v)) : 0;

  return (
    <div className="historial">
      <AppHeader />

      {/* Period filter */}
      <div className="historial-period-bar">
        <p className="historial-kicker">Período</p>
        <div className="historial-filters">
          {FILTROS.map(f => (
            <button
              key={f.key}
              className={`filter-chip${filtro === f.key ? ' active' : ''}`}
              onClick={() => handleFiltro(f.key)}
            >
              {f.label}
              {f.hasIcon && <svg className="filter-chip-caret" viewBox="0 0 14 14" fill="none">
                <path d="M3.5 5.25L7 8.75L10.5 5.25" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>}
            </button>
          ))}
        </div>
      </div>

      {filtro === 'custom' && (
        <form onSubmit={aplicarRango} style={{ display: 'flex', flexWrap: 'wrap', gap: 12, padding: '12px 20px' }}>
          <label>Desde <input type="date" value={fechaDesde} onChange={e => setFechaDesde(e.target.value)} required /></label>
          <label>Hasta <input type="date" value={fechaHasta} onChange={e => setFechaHasta(e.target.value)} required /></label>
          <button type="submit" className="filter-chip">Aplicar fechas</button>
        </form>
      )}

      {loading ? <Spinner /> : (
        <div className="historial-content">
          {error && <p className="empty-msg">{error}</p>}

          {/* Summary card */}
          <div className="historial-summary-card">
            <h2 className="summary-title">Resumen — {getNombrePeriodo(filtro)}</h2>

            <div className="summary-grid">
              <div className="stat-cell">
                <svg className="stat-icon" viewBox="0 0 16 16" fill="none">
                  <rect x="1" y="10" width="3" height="5" rx="1" fill="#64748B"/>
                  <rect x="6" y="6" width="3" height="9" rx="1" fill="#64748B"/>
                  <rect x="11" y="2" width="3" height="13" rx="1" fill="#64748B"/>
                </svg>
                <strong>{promedioIndice}</strong>
                <span>Promedio del período</span>
              </div>
              <div className="stat-cell">
                <svg className="stat-icon" viewBox="0 0 16 16" fill="none">
                  <path d="M2 8C2 5.8 3.8 4 6 4H10C12.2 4 14 5.8 14 8C14 10.2 12.2 12 10 12H6C3.8 12 2 10.2 2 8Z" stroke="#64748B" strokeWidth="1.4"/>
                  <path d="M6 8H10M8 6V10" stroke="#64748B" strokeWidth="1.4" strokeLinecap="round"/>
                </svg>
                <strong>{totalKm.toFixed(0)} km</strong>
                <span>Total recorrido</span>
              </div>
              <div className="stat-cell">
                <svg className="stat-icon" viewBox="0 0 16 16" fill="none">
                  <rect x="1" y="5" width="14" height="9" rx="2" stroke="#64748B" strokeWidth="1.4"/>
                  <path d="M5 5V3.5C5 2.67 5.67 2 6.5 2H9.5C10.33 2 11 2.67 11 3.5V5" stroke="#64748B" strokeWidth="1.4"/>
                  <circle cx="8" cy="9.5" r="1.5" fill="#64748B"/>
                </svg>
                <strong>{sesiones.length}</strong>
                <span>Viajes registrados</span>
              </div>
              <div className="stat-cell">
                <svg className="stat-icon" viewBox="0 0 16 16" fill="none">
                  <circle cx="8" cy="8" r="6.5" stroke="#64748B" strokeWidth="1.4"/>
                  <path d="M8 5V8.5" stroke="#64748B" strokeWidth="1.4" strokeLinecap="round"/>
                  <circle cx="8" cy="11" r="0.8" fill="#64748B"/>
                </svg>
                <strong>{eventosRiesgo}</strong>
                <span>Viajes con riesgo Medio o Alto</span>
              </div>
            </div>

            {chartData.length > 1 && (
              <>
                <div className="chart-divider" />
                <div className="chart-axis-row">
                  <span className="chart-axis-val">{chartMax}</span>
                  <span className="chart-axis-val chart-axis-cur">{promedioIndice}</span>
                </div>
                <div className="summary-sparkline">
                  <ResponsiveContainer width="100%" height={40}>
                    <LineChart data={chartData} margin={{top:2,right:0,bottom:0,left:0}}>
                      <Line
                        type="monotone"
                        dataKey="v"
                        stroke="var(--accent)"
                        strokeWidth={2}
                        dot={{ r: 3 }}
                        isAnimationActive={false}
                      />
                      <Tooltip
                        contentStyle={{ fontSize: 11, padding: '4px 8px' }}
                        formatter={(v) => [v, 'Índice']}
                        labelFormatter={(_, p) => p?.[0]?.payload?.f || ''}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </>
            )}
            <p className="chart-caption">Evolución del índice — período seleccionado</p>
          </div>

          {/* Sessions list */}
          <div className="historial-section-row">
            <span>Sesiones registradas</span>
            <small>({sesiones.length})</small>
          </div>

          {sesiones.length === 0
            ? <p className="empty-msg">No hay sesiones en este período.</p>
            : sesiones.map(s => {
                const cfg = NIVEL_CFG[s.nivel] || { emoji: '⚪', label: '—', cls: 'bajo' };
                const dur  = duracionMin(s.inicio, s.fin);
                const dist = s.distancia_km != null ? `${s.distancia_km.toFixed(1)} km` : '—';
                const meta = dur ? `${dist} · ${dur} min` : dist;
                const nAlertas = s.alertas_count ?? 0;
                const tieneAlertas = nAlertas > 0;
                const alertasTxt = nAlertas === 1
                  ? '⚠️ 1 alerta detectada'
                  : `⚠️ ${nAlertas} alertas detectadas`;
                return (
                  <div
                    key={s.sesion_id}
                    className="sesion-card sesion-card--clickable"
                    onClick={() => navigate(`/historial/${s.sesion_id}`)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={e => e.key === 'Enter' && navigate(`/historial/${s.sesion_id}`)}
                  >
                    <div className="sesion-card-inner">
                      <span className="sesion-emoji">{cfg.emoji}</span>
                      <div className="sesion-info">
                        <div className="sesion-top-row">
                          <span className={`nivel-badge nivel-${cfg.cls}`}>{cfg.label}</span>
                          <span className="sesion-fecha">{formatFecha(s.inicio)}</span>
                        </div>
                        <p className="sesion-meta">{meta}</p>
                        <p>Índice: <strong>{s.indice != null ? s.indice.toFixed(1) : 'Sin datos'}</strong> / 100</p>
                        <p className={`sesion-alertas ${tieneAlertas ? 'alertas-warn' : 'alertas-ok'}`}>
                          {tieneAlertas ? alertasTxt : 'Sin alertas'}
                        </p>
                      </div>
                      {tieneAlertas && (
                        <svg className="sesion-chevron" viewBox="0 0 20 20" fill="none">
                          <path d="M7.5 5L12.5 10L7.5 15" stroke="#94A3B8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      )}
                    </div>
                  </div>
                );
              })
          }


        </div>
      )}

      <BottomNav />
    </div>
  );
}
