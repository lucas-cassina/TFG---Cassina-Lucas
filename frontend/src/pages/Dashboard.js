import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { indiceAPI, telemetriaAPI } from '../api/client';
import { useSesionStream } from '../hooks/useSesionStream';
import Gauge from '../components/Gauge';
import ProgressBar from '../components/ProgressBar';
import Spinner from '../components/Spinner';
import BottomNav from '../components/BottomNav';
import AppHeader from '../components/AppHeader';
import './Dashboard.css';

/* ─── Stat icons ─────────────────────────────────────────── */
const RouteIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="6" cy="19" r="3"/>
    <path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15"/>
    <circle cx="18" cy="5" r="3"/>
  </svg>
);

const SessionsIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/>
    <rect x="9" y="3" width="6" height="4" rx="1"/>
    <path d="M9 12h6M9 16h4"/>
  </svg>
);

const AlertCircleIcon = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <path d="M12 8v4M12 16h.01"/>
  </svg>
);

/* ─── Risk variable icons ────────────────────────────────── */
const SpeedIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 2a10 10 0 0 1 6.22 17.9"/>
    <path d="M12 2a10 10 0 0 0-6.22 17.9"/>
    <path d="M12 12l-3.5-6"/>
    <circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none"/>
  </svg>
);

const BrakeIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <path d="M8 12h8"/>
    <path d="M12 8v4"/>
  </svg>
);

const AccelIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 19V5"/>
    <path d="M5 12l7-7 7 7"/>
  </svg>
);

const ClockIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <path d="M12 6v6l4 2"/>
  </svg>
);

const MapPinIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
    <circle cx="12" cy="10" r="3"/>
  </svg>
);

/* ─── Helpers ────────────────────────────────────────────── */
function getGreeting() {
  const h = new Date().getHours();
  if (h >= 6 && h < 13) return 'Buen día';
  if (h >= 13 && h < 20) return 'Buenas tardes';
  return 'Buenas noches';
}

function formatDateTime(value) {
  if (!value) return '';
  return new Date(value).toLocaleString('es-AR', {
    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
  });
}

function formatDuracion(inicio) {
  if (!inicio) return '';
  const ms = Date.now() - new Date(inicio);
  const mins = Math.floor(ms / 60000);
  if (mins < 1) return 'recién iniciada';
  if (mins < 60) return `${mins} min`;
  const hs = Math.floor(mins / 60);
  const rm = mins % 60;
  return rm > 0 ? `${hs}h ${rm}min` : `${hs}h`;
}

function lastTripText(stats) {
  const fecha = stats?.ultima_sesion_fecha ?? stats?.ultima_sesion;
  if (fecha) {
    const diffMs = Date.now() - new Date(fecha);
    const hours  = Math.floor(diffMs / 36e5);
    const mins   = Math.floor(diffMs / 60000);
    if (mins < 1)    return 'Tu último viaje fue hace menos de un minuto.';
    if (hours < 1)   return `Tu último viaje fue hace ${mins} minuto${mins > 1 ? 's' : ''}.`;
    if (hours < 24)  return `Tu último viaje fue hace ${hours} hora${hours > 1 ? 's' : ''}.`;
    return 'Tu último viaje fue hace más de un día.';
  }
  if (stats?.total_sesiones) return `Tenés ${stats.total_sesiones} sesiones registradas este mes.`;
  return 'Todavía no tenés sesiones registradas este mes.';
}

const ALERT_ICON = {
  exceso_velocidad:   <SpeedIcon />,
  frenada_brusca:     <BrakeIcon />,
  aceleracion_brusca: <AccelIcon />,
};

/* ─── Component ──────────────────────────────────────────── */
export default function Dashboard() {
  const { user } = useAuth();
  const navigate  = useNavigate();
  const [indice,   setIndice]   = useState(null);
  const [stats,    setStats]    = useState(null);
  const [alertas,  setAlertas]  = useState([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState('');
  const [tick,     setTick]     = useState(0);   // para actualizar duración cada minuto

  const cargarDatos = useCallback(() => {
    return Promise.all([
      indiceAPI.actual(),
      indiceAPI.estadisticasMes(),
      telemetriaAPI.alertas(),
    ]).then(([idx, st, al]) => {
      setIndice(idx.data);
      setStats(st.data);
      setAlertas(al.data?.slice(0, 3) || []);
    });
  }, []);

  // Al cerrar sesión, recargar datos para mostrar el nuevo índice
  const handleSesionCerrada = useCallback(() => {
    cargarDatos().catch(() => {});
  }, [cargarDatos]);

  const { sesionActiva, sesionInfo, alertasLive } = useSesionStream(handleSesionCerrada);

  useEffect(() => {
    cargarDatos()
      .catch((err) => {
        console.error(err);
        setError('No pudimos cargar tus datos de conducción. Intentá nuevamente en unos minutos.');
      })
      .finally(() => setLoading(false));
  }, [cargarDatos]);

  // Actualizar el contador de duración cada 60 segundos
  useEffect(() => {
    if (!sesionActiva) return;
    const id = setInterval(() => setTick((t) => t + 1), 60_000);
    return () => clearInterval(id);
  }, [sesionActiva]);

  if (loading) return (
    <div className="dashboard">
      <div className="dashboard-loading"><Spinner /></div>
      <BottomNav />
    </div>
  );

  const valor  = indice?.indice ?? 0;
  const nivel  = indice?.nivel  ?? 'Sin datos';
  // Durante sesión activa, mostrar las alertas en vivo; si no, las históricas
  const alertasAMostrar = sesionActiva && alertasLive.length > 0 ? alertasLive : alertas;
  const alertaPrincipal = alertasAMostrar[0];

  return (
    <div className="dashboard">
      <AppHeader />

      {/* Banner de sesión activa */}
      {sesionActiva && (
        <button className="session-live-banner" onClick={() => navigate('/sesion/activa')}>
          <span className="session-live-dot" aria-hidden="true" />
          <div className="session-live-info">
            <strong>Sesión en curso</strong>
            <span>
              {sesionInfo?.inicio ? formatDuracion(sesionInfo.inicio) : 'activa'}
              {alertasLive.length > 0 && ` · ${alertasLive.length} alerta${alertasLive.length > 1 ? 's' : ''}`}
            </span>
          </div>
          <span className="session-live-cta" aria-hidden="true">
            Ver en vivo
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 18l6-6-6-6"/>
            </svg>
          </span>
        </button>
      )}

      <section className="dashboard-hello">
        <h1>{getGreeting()}, {user?.nombre || 'conductor'} 👋</h1>
        <p>{sesionActiva ? 'Estás conduciendo ahora. Tu índice se calculará al finalizar.' : lastTripText(stats)}</p>
      </section>

      {error && <p className="dashboard-error">{error}</p>}

      <div className="dashboard-score-card">
        <span className="score-label">Índice — {sesionActiva ? 'última sesión finalizada' : 'último viaje'}</span>
        <Gauge value={valor} nivel={nivel} />
        <p className="score-copy">
          {indice ? 'Mantené este nivel para sumar puntos.' : 'El índice se calcula cuando cerrás una sesión de conducción.'}
        </p>
        <div className="dashboard-score-divider" />
        <div className="score-stats">
          <div>
            <span className="score-stat-icon"><RouteIcon /></span>
            <strong>{`${(stats?.total_km ?? 0).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, '.')} km`}</strong>
            <small>Distancia total</small>
          </div>
          <div>
            <span className="score-stat-icon"><SessionsIcon /></span>
            <strong>{stats?.total_sesiones ?? 0}</strong>
            <small>Sesiones</small>
          </div>
          <div>
            <span className="score-stat-icon"><AlertCircleIcon /></span>
            <strong>{sesionActiva ? alertasLive.length : (stats?.alertas_totales ?? alertas.length)}</strong>
            <small>{sesionActiva ? 'Alertas hoy' : 'Alertas'}</small>
          </div>
        </div>
      </div>

      {/* Card de alertas: muestra las vivas durante sesión, o la última histórica */}
      <div className={`dashboard-alert-card${sesionActiva && alertasLive.length > 0 ? ' dashboard-alert-card--live' : ''}`}>
        <span className="dashboard-alert-icon" aria-hidden="true">
          {ALERT_ICON[alertaPrincipal?.tipo_alerta] ?? <AlertCircleIcon size={20} />}
        </span>
        <div>
          <strong>{alertaPrincipal?.descripcion || 'Sin alertas recientes'}</strong>
          <p>
            {alertaPrincipal
              ? formatDateTime(alertaPrincipal.timestamp)
              : sesionActiva
                ? 'Conducís sin alertas por el momento.'
                : 'Cuando el sistema detecte eventos de riesgo, los vas a ver acá.'}
          </p>
          {sesionActiva && alertasLive.length > 1 && (
            <p className="alert-live-count">+{alertasLive.length - 1} alerta{alertasLive.length > 2 ? 's' : ''} más en esta sesión</p>
          )}
          <button onClick={() => navigate('/historial')}>Ver todas las alertas</button>
        </div>
      </div>

      <div className="dashboard-content">
        {indice && (
          <div className="breakdown-card glass-card">
            <h2>¿Qué compone tu índice?</h2>
            <ProgressBar label="Velocidad"        icon={<SpeedIcon />}   value={indice.puntaje_velocidad     ?? 0} color="var(--ok)"   weight="25%" />
            <ProgressBar label="Frenadas bruscas" icon={<BrakeIcon />}   value={indice.puntaje_frenadas      ?? 0} color="var(--warn)" weight="25%" />
            <ProgressBar label="Aceleraciones"    icon={<AccelIcon />}   value={indice.puntaje_aceleraciones ?? 0} color="var(--warn)" weight="20%" />
            <ProgressBar label="Horario"          icon={<ClockIcon />}   value={indice.puntaje_horario       ?? 0} color="var(--ok)"   weight="15%" />
            <ProgressBar label="Distancia"        icon={<MapPinIcon />}  value={indice.puntaje_distancia     ?? 0} color="var(--warn)" weight="15%" />
            <p className="breakdown-note">Índice calculado al cierre de cada sesión de conducción.</p>
          </div>
        )}
      </div>

      <BottomNav />
    </div>
  );
}
