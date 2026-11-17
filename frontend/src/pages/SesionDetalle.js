import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { indiceAPI } from '../api/client';
import AppHeader from '../components/AppHeader';
import Spinner from '../components/Spinner';
import './SesionDetalle.css';

const NIVEL_CFG = {
  Bajo:  { emoji: '🟢', cls: 'bajo',  label: 'BAJO'  },
  Medio: { emoji: '🟡', cls: 'medio', label: 'MEDIO' },
  Alto:  { emoji: '🔴', cls: 'alto',  label: 'ALTO'  },
};

const TIPO_LABEL = {
  exceso_velocidad:    'Exceso de velocidad',
  frenada_brusca:      'Frenada brusca',
  aceleracion_brusca:  'Aceleración brusca',
};

const ALERT_ICON = {
  exceso_velocidad: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a10 10 0 0 1 6.22 17.9"/>
      <path d="M12 2a10 10 0 0 0-6.22 17.9"/>
      <path d="M12 12l-3.5-6"/>
      <circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none"/>
    </svg>
  ),
  frenada_brusca: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <path d="M8 12h8"/>
      <path d="M12 8v4"/>
    </svg>
  ),
  aceleracion_brusca: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 19V5"/>
      <path d="M5 12l7-7 7 7"/>
    </svg>
  ),
};

/* Todos los puntajes son indicadores de RIESGO: 0 = sin riesgo (bueno), 100 = máximo riesgo (malo). */
function PuntajeBar({ label, valor, descripcion }) {
  if (valor == null) return null;
  const pct = Math.min(100, Math.max(0, valor));
  const cls = pct < 20 ? 'bar-ok' : pct < 50 ? 'bar-warn' : 'bar-danger';
  return (
    <div className="puntaje-row">
      <div className="puntaje-label-row">
        <span className="puntaje-label">{label}</span>
        <span className="puntaje-val">{Math.round(pct)}</span>
      </div>
      {descripcion && <p className="puntaje-desc">{descripcion}</p>}
      <div className="puntaje-track">
        <div className={`puntaje-fill ${cls}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function SesionDetalle() {
  const { sesionId } = useParams();
  const navigate     = useNavigate();
  const [sesion, setSesion] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState('');

  useEffect(() => {
    indiceAPI.detalleSesion(sesionId)
      .then(r  => setSesion(r.data))
      .catch(() => setError('No pudimos cargar el detalle de esta sesión.'))
      .finally(() => setLoading(false));
  }, [sesionId]);

  if (loading) return <div className="sesion-detalle"><Spinner /></div>;
  if (error)   return <div className="sesion-detalle"><p className="empty-msg">{error}</p></div>;
  if (!sesion) return null;

  const cfg = NIVEL_CFG[sesion.nivel] || { emoji: '⚪', cls: 'bajo', label: '—' };
  const inicio = new Date(sesion.inicio);
  const fin    = sesion.fin ? new Date(sesion.fin) : null;
  const durMin = fin ? Math.round((fin - inicio) / 60000) : null;

  const fechaLarga = inicio.toLocaleDateString('es-AR', {
    weekday: 'long', day: '2-digit', month: 'long', year: 'numeric',
  });
  const hora = inicio.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' });

  return (
    <div className="sesion-detalle">
      <AppHeader />
      <div className="detalle-subnav">
        <button className="detalle-back" onClick={() => navigate(-1)} aria-label="Volver">
          <svg viewBox="0 0 24 24" fill="none">
            <path d="M15 19L8 12L15 5" stroke="currentColor" strokeWidth="2"
              strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
        <span className="detalle-title">Detalle de sesión</span>
      </div>

      <div className="detalle-content">
        {/* Hero card */}
        <div className="detalle-hero">
          <div className="hero-nivel">
            <span className="hero-emoji">{cfg.emoji}</span>
            <div>
              <span className={`nivel-badge nivel-${cfg.cls}`}>{cfg.label}</span>
              <p className="hero-fecha">{fechaLarga}</p>
              <p className="hero-hora">{hora} hs</p>
            </div>
          </div>

          <div className="hero-stats">
            <div className="hero-stat">
              <strong>{sesion.indice != null ? sesion.indice.toFixed(1) : '—'}</strong>
              <span>Índice de riesgo</span>
            </div>
            <div className="hero-stat-divider" />
            <div className="hero-stat">
              <strong>{sesion.distancia_km != null ? `${sesion.distancia_km.toFixed(1)} km` : '—'}</strong>
              <span>Distancia</span>
            </div>
            <div className="hero-stat-divider" />
            <div className="hero-stat">
              <strong>{durMin != null ? `${durMin} min` : '—'}</strong>
              <span>Duración</span>
            </div>
          </div>
        </div>

        {/* Puntajes */}
        {(sesion.puntaje_velocidad != null || sesion.puntaje_frenadas != null) && (
          <div className="detalle-card">
            <h2 className="detalle-section-title">Factores de riesgo</h2>
            <p className="detalle-section-sub">Menor barra = menor riesgo en esa categoría</p>
            <div className="puntajes-list">
              <PuntajeBar
                label="Velocidad excesiva"
                valor={sesion.puntaje_velocidad}
                descripcion="% de eventos sobre 90 km/h"
              />
              <PuntajeBar
                label="Frenadas bruscas"
                valor={sesion.puntaje_frenadas}
                descripcion="% de eventos con desaceleración brusca"
              />
              <PuntajeBar
                label="Aceleraciones bruscas"
                valor={sesion.puntaje_aceleraciones}
                descripcion="% de eventos con aceleración brusca"
              />
              <PuntajeBar
                label="Conducción nocturna"
                valor={sesion.puntaje_horario}
                descripcion="% del viaje entre las 22:00 y las 06:00"
              />
              <PuntajeBar
                label="Kilometraje"
                valor={sesion.puntaje_distancia}
                descripcion={`Exposición por distancia (ref. 50 km)`}
              />
            </div>
          </div>
        )}

        {/* Alertas */}
        <div className="detalle-card">
          <h2 className="detalle-section-title">
            Alertas detectadas
            <span className="alertas-badge">{sesion.alertas.length}</span>
          </h2>

          {sesion.alertas.length === 0 ? (
            <p className="alertas-empty">✅ Sin alertas en esta sesión</p>
          ) : (
            <ul className="alertas-list">
              {sesion.alertas.map((a, i) => (
                <li key={i} className={`alerta-item alerta-item--${a.tipo_alerta}`}>
                  <span className="alerta-icon">
                    {ALERT_ICON[a.tipo_alerta] ?? (
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/>
                      </svg>
                    )}
                  </span>
                  <div className="alerta-info">
                    <p className="alerta-tipo">{TIPO_LABEL[a.tipo_alerta] || a.tipo_alerta}</p>
                    {a.descripcion && <p className="alerta-desc">{a.descripcion}</p>}
                    <p className="alerta-time">
                      {new Date(a.timestamp).toLocaleTimeString('es-AR', {
                        hour: '2-digit', minute: '2-digit', second: '2-digit',
                      })} hs
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
