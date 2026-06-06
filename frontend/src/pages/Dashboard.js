import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { indiceAPI, telemetriaAPI } from '../api/client';
import Gauge from '../components/Gauge';
import Card from '../components/Card';
import Badge from '../components/Badge';
import ProgressBar from '../components/ProgressBar';
import Spinner from '../components/Spinner';
import BottomNav from '../components/BottomNav';
import './Dashboard.css';

export default function Dashboard() {
  const { user, logout } = useAuth();
  const [indice, setIndice] = useState(null);
  const [stats, setStats] = useState(null);
  const [alertas, setAlertas] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      indiceAPI.actual(),
      indiceAPI.estadisticasMes(),
      telemetriaAPI.alertas(),
    ]).then(([idx, st, al]) => {
      setIndice(idx.data);
      setStats(st.data);
      setAlertas(al.data?.slice(0, 3) || []);
    }).catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <><Spinner /><BottomNav /></>;

  const valor = indice?.indice ?? 0;
  const nivel = indice?.nivel ?? 'Bajo';

  return (
    <div className="dashboard">
      <header className="dashboard__header">
        <div>
          <h1>Hola, {user?.nombre} 👋</h1>
          <p className="dashboard__subtitle">Tu índice de riesgo actual</p>
        </div>
        <button className="dashboard__logout" onClick={logout}>Salir</button>
      </header>

      <main className="dashboard__main">
        {/* Gauge principal */}
        <Card className="dashboard__gauge-card">
          <Gauge value={valor} nivel={nivel} />
          <p className="dashboard__gauge-desc">
            {nivel === 'Bajo' && '¡Excelente conducción! Seguí así.'}
            {nivel === 'Medio' && 'Conducción moderada. Podés mejorar.'}
            {nivel === 'Alto' && 'Tu conducción presenta riesgos elevados.'}
          </p>
        </Card>

        {/* Estadísticas del mes */}
        {stats && (
          <Card className="dashboard__stats">
            <h2 className="section-title">Este mes</h2>
            <div className="stats-grid">
              <div className="stat-item">
                <span className="stat-value">{stats.total_sesiones}</span>
                <span className="stat-label">Sesiones</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">{stats.total_km.toFixed(0)}</span>
                <span className="stat-label">Kilómetros</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">{stats.indice_promedio}</span>
                <span className="stat-label">Índice prom.</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">{stats.alertas_totales}</span>
                <span className="stat-label">Alertas</span>
              </div>
            </div>
          </Card>
        )}

        {/* Desglose de variables */}
        {indice && (
          <Card>
            <h2 className="section-title">Desglose de variables</h2>
            <div className="breakdown">
              <ProgressBar label="Velocidad (25%)"           value={indice.puntaje_velocidad ?? 0}       color="var(--color-riesgo-alto)" />
              <ProgressBar label="Frenadas bruscas (25%)"    value={indice.puntaje_frenadas ?? 0}        color="var(--color-riesgo-medio)" />
              <ProgressBar label="Aceleraciones (20%)"       value={indice.puntaje_aceleraciones ?? 0}   color="#8b5cf6" />
              <ProgressBar label="Horario (15%)"             value={indice.puntaje_horario ?? 0}         color="var(--color-accent)" />
              <ProgressBar label="Distancia (15%)"           value={indice.puntaje_distancia ?? 0}       color="#06b6d4" />
            </div>
          </Card>
        )}

        {/* Última alerta */}
        {alertas.length > 0 && (
          <Card>
            <h2 className="section-title">Alertas recientes</h2>
            <div className="alertas-list">
              {alertas.map(a => (
                <div key={a.id} className="alerta-item">
                  <Badge label={a.tipo_alerta === 'exceso_velocidad' ? 'Alto'
                               : a.tipo_alerta === 'frenada_brusca' ? 'Medio' : 'Medio'} />
                  <span className="alerta-desc">{a.descripcion}</span>
                </div>
              ))}
            </div>
          </Card>
        )}
      </main>

      <BottomNav />
    </div>
  );
}
