import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSesionStream } from '../hooks/useSesionStream';
import Spinner from '../components/Spinner';
import BottomNav from '../components/BottomNav';
import './SesionActiva.css';

/* ─── Icons ──────────────────────────────────────────────── */
const BackIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M19 12H5M12 5l-7 7 7 7"/>
  </svg>
);

const SpeedIcon = ({ size = 18 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 2a10 10 0 0 1 6.22 17.9"/><path d="M12 2a10 10 0 0 0-6.22 17.9"/>
    <path d="M12 12l-3.5-6"/><circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none"/>
  </svg>
);

const BrakeIcon = ({ size = 18 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/><path d="M8 12h8"/><path d="M12 8v4"/>
  </svg>
);

const AccelIcon = ({ size = 18 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 19V5"/><path d="M5 12l7-7 7 7"/>
  </svg>
);

const CheckCircleIcon = () => (
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/><path d="M8 12l3 3 5-6"/>
  </svg>
);

/* ─── Helpers ────────────────────────────────────────────── */
const ALERTA_META = {
  exceso_velocidad:   { label: 'Velocidad excesiva', Icon: SpeedIcon,  color: 'danger' },
  frenada_brusca:     { label: 'Frenada brusca',     Icon: BrakeIcon,  color: 'warn'   },
  aceleracion_brusca: { label: 'Aceleración brusca', Icon: AccelIcon,  color: 'accent' },
};

function formatElapsed(s) {
  const h   = Math.floor(s / 3600);
  const m   = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  const mm  = String(m).padStart(2, '0');
  const ss  = String(sec).padStart(2, '0');
  return h > 0 ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
}

function tiempoRelativo(ts) {
  if (!ts) return '';
  const mins = Math.floor((Date.now() - new Date(ts)) / 60000);
  if (mins < 1) return 'ahora';
  if (mins === 1) return 'hace 1 min';
  return `hace ${mins} min`;
}

function nivelColor(nivel) {
  if (!nivel) return 'var(--text-2)';
  if (nivel === 'Bajo')  return 'var(--ok)';
  if (nivel === 'Medio') return 'var(--warn)';
  return 'var(--danger)';
}

/* ─── Sub-components ─────────────────────────────────────── */
function SaHeader({ onBack, live = true }) {
  return (
    <header className="sa-header">
      <button className="sa-back-btn" onClick={onBack} aria-label="Volver">
        <BackIcon />
      </button>
      <div className="sa-header-title">
        {live && <span className="sa-header-dot" aria-hidden="true" />}
        <span>{live ? 'Sesión en curso' : 'Sesión finalizada'}</span>
      </div>
    </header>
  );
}

function AlertaItem({ alerta, tiempoTick }) {
  const meta = ALERTA_META[alerta.tipo_alerta] || { label: alerta.tipo_alerta, Icon: SpeedIcon, color: 'danger' };
  const { Icon, color } = meta;
  return (
    <div className={`sa-alerta-item sa-alerta-item--${color}`}>
      <span className={`sa-alerta-icon sa-alerta-icon--${color}`}>
        <Icon size={16} />
      </span>
      <div className="sa-alerta-body">
        <span className="sa-alerta-desc">{alerta.descripcion}</span>
        <span className="sa-alerta-time">{tiempoRelativo(alerta.timestamp)}</span>
      </div>
    </div>
  );
}

/* ─── Main component ─────────────────────────────────────── */
export default function SesionActiva() {
  const navigate   = useNavigate();
  const [segundos, setSegundos]   = useState(0);
  const [resultado, setResultado] = useState(null);
  const [tiempoTick, setTiempoTick] = useState(0);

  const handleCerrada = useCallback((event) => {
    setResultado(event);
  }, []);

  const { sesionActiva, sesionInfo, alertasLive, cargando } = useSesionStream(handleCerrada);

  // Elapsed timer — updates every second
  useEffect(() => {
    if (!sesionActiva || !sesionInfo?.inicio) return;
    const inicioMs = new Date(sesionInfo.inicio).getTime();
    const tick = () => setSegundos(Math.floor((Date.now() - inicioMs) / 1000));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [sesionActiva, sesionInfo?.inicio]);

  // Relative time tick — updates every 30s
  useEffect(() => {
    const id = setInterval(() => setTiempoTick((t) => t + 1), 30_000);
    return () => clearInterval(id);
  }, []);

  const inicioHora = sesionInfo?.inicio
    ? new Date(sesionInfo.inicio).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })
    : null;

  /* ── Sesión recién cerrada ── */
  if (resultado) {
    const color = nivelColor(resultado.nivel);
    return (
      <div className="sesion-activa">
        <SaHeader onBack={() => navigate('/dashboard')} live={false} />
        <div className="sa-result-card">
          <span className="sa-result-check" style={{ color }}>
            <CheckCircleIcon />
          </span>
          <h2 className="sa-result-title">Sesión finalizada</h2>
          <div className="sa-result-indice" style={{ color }}>
            {resultado.indice?.toFixed(1) ?? '--'}
          </div>
          <span className="sa-result-nivel" style={{ background: `${color}18`, color }}>
            {resultado.nivel ?? 'Sin datos'}
          </span>
          <p className="sa-result-km">
            {resultado.distancia_km ? `${resultado.distancia_km.toFixed(1)} km recorridos` : ''}
          </p>
          <button className="sa-result-btn" onClick={() => navigate('/dashboard')}>
            Volver al inicio
          </button>
          <button className="sa-result-link" onClick={() => navigate('/historial')}>
            Ver historial completo
          </button>
        </div>
        <BottomNav />
      </div>
    );
  }

  /* ── Cargando estado inicial ── */
  if (cargando) {
    return (
      <div className="sesion-activa sesion-activa--center">
        <Spinner />
      </div>
    );
  }

  /* ── Sin sesión activa ── */
  if (!sesionActiva) {
    return (
      <div className="sesion-activa">
        <SaHeader onBack={() => navigate('/dashboard')} live={false} />
        <div className="sa-empty-state">
          <span className="sa-empty-icon" aria-hidden="true">🚗</span>
          <h2>Sin sesión activa</h2>
          <p>No hay ninguna sesión en curso. El dispositivo OBD-II inicia la sesión automáticamente cuando arrancás el auto.</p>
          <button className="sa-result-btn" onClick={() => navigate('/dashboard')}>
            Volver al inicio
          </button>
        </div>
        <BottomNav />
      </div>
    );
  }

  /* ── Sesión activa ── */
  const contadores = alertasLive.reduce((acc, a) => {
    acc[a.tipo_alerta] = (acc[a.tipo_alerta] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="sesion-activa">
      <SaHeader onBack={() => navigate('/dashboard')} live />

      {/* Timer */}
      <div className="sa-timer-card">
        <div className="sa-live-row">
          <span className="sa-live-dot" aria-hidden="true" />
          <span className="sa-live-label">En curso</span>
        </div>
        <div className="sa-timer">{formatElapsed(segundos)}</div>
        {inicioHora && (
          <p className="sa-timer-sub">Iniciada a las {inicioHora}</p>
        )}
      </div>

      {/* Contadores rápidos */}
      {alertasLive.length > 0 && (
        <div className="sa-chips-row">
          {contadores.exceso_velocidad > 0 && (
            <div className="sa-chip sa-chip--danger">
              <SpeedIcon size={14} />
              <span>{contadores.exceso_velocidad}</span>
            </div>
          )}
          {contadores.frenada_brusca > 0 && (
            <div className="sa-chip sa-chip--warn">
              <BrakeIcon size={14} />
              <span>{contadores.frenada_brusca}</span>
            </div>
          )}
          {contadores.aceleracion_brusca > 0 && (
            <div className="sa-chip sa-chip--accent">
              <AccelIcon size={14} />
              <span>{contadores.aceleracion_brusca}</span>
            </div>
          )}
        </div>
      )}

      {/* Alertas */}
      <section className="sa-alertas-section">
        <div className="sa-section-header">
          <h2>Alertas en esta sesión</h2>
          {alertasLive.length > 0 && (
            <span className="sa-alertas-badge">{alertasLive.length}</span>
          )}
        </div>

        {alertasLive.length === 0 ? (
          <div className="sa-no-alertas">
            <span aria-hidden="true">✅</span>
            <p>Conducís sin alertas hasta ahora.</p>
          </div>
        ) : (
          <div className="sa-alerta-list">
            {alertasLive.map((a, i) => (
              <AlertaItem key={`${a.timestamp}-${a.tipo_alerta}-${i}`} alerta={a} tiempoTick={tiempoTick} />
            ))}
          </div>
        )}
      </section>

      <p className="sa-nota">
        El índice de riesgo se calculará automáticamente cuando finalice la sesión.
      </p>

      <BottomNav />
    </div>
  );
}
