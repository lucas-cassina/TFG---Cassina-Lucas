import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { auditorAPI } from '../../api/client';
import Sidebar from '../../components/Sidebar';
import Card from '../../components/Card';
import Badge from '../../components/Badge';
import Gauge from '../../components/Gauge';
import Spinner from '../../components/Spinner';
import './Auditor.css';

export default function PerfilRiesgo() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [perfil, setPerfil] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    auditorAPI.perfilRiesgo(id)
      .then(r => setPerfil(r.data))
      .catch(() => setError('No pudimos cargar el perfil de riesgo solicitado.'))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="auditor-layout"><Sidebar /><main className="auditor-main"><Spinner /></main></div>;
  if (error) return (
    <div className="auditor-layout">
      <Sidebar />
      <main className="auditor-main">
        <Card>
          <p className="form-error">{error}</p>
          <button className="btn-back" onClick={() => navigate('/auditor/buscador')}>Volver al buscador</button>
        </Card>
      </main>
    </div>
  );

  return (
    <div className="auditor-layout">
      <Sidebar />
      <main className="auditor-main">
        <div className="auditor-topbar">
          <span>Auditoría / {perfil?.nombre} {perfil?.apellido} / Perfil de riesgo</span>
          <div><strong>● Sesión activa</strong><span>Auditor CIAS</span></div>
        </div>
        <div className="perfil-riesgo-header">
          <button className="btn-back" onClick={() => navigate('/auditor/buscador')}>← Volver</button>
          <h1 className="auditor-page-title">
            {perfil?.nombre} {perfil?.apellido}
          </h1>
          <button className="btn-pdf" onClick={() => navigate(`/auditor/reporte/${id}`)}>
            📄 Generar reporte PDF
          </button>
        </div>

        <div className="perfil-riesgo-grid">
          {/* Gauge */}
          <Card className="gauge-card-auditor">
            <h2 className="section-title">Índice de riesgo actual</h2>
            <Gauge value={perfil?.indice_actual ?? 0} nivel={perfil?.nivel_actual ?? 'Sin datos'} />
            {perfil?.indice_promedio_6m != null && (
              <p className="promedio-6m">Promedio 180 días: <strong>{perfil.indice_promedio_6m}</strong></p>
            )}
          </Card>

          {/* Datos del asegurado */}
          <Card>
            <h2 className="section-title">Datos del asegurado</h2>
            <div className="datos-tabla">
              {[
                ['DNI', perfil?.dni],
                ['Email', perfil?.email],
                ['Póliza', perfil?.numero_poliza || '—'],
                ['Vehículo', perfil?.marca_vehiculo ? `${perfil.marca_vehiculo} ${perfil.modelo_vehiculo}` : '—'],
              ].map(([k, v]) => (
                <div key={k} className="datos-row">
                  <span className="datos-key">{k}</span>
                  <span className="datos-val">{v}</span>
                </div>
              ))}
            </div>
          </Card>

          {/* Estadísticas */}
          <Card>
            <h2 className="section-title">Estadísticas</h2>
            <div className="stats-grid">
              <div className="stat-item">
                <span className="stat-value">{perfil?.total_sesiones ?? 0}</span>
                <span className="stat-label">Sesiones</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">{(perfil?.total_km ?? 0).toFixed(0)}</span>
                <span className="stat-label">Kilómetros</span>
              </div>
            </div>
          </Card>

          {/* Nivel incentivo */}
          <Card>
            <h2 className="section-title">Nivel de incentivo</h2>
            <div className="incentivo-display">
              <Badge label={perfil?.nivel_incentivo || 'Sin nivel'} />
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
}
