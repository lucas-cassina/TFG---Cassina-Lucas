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
  const [descargando, setDescargando] = useState(false);

  useEffect(() => {
    auditorAPI.perfilRiesgo(id)
      .then(r => setPerfil(r.data))
      .catch(() => navigate('/auditor/buscador'))
      .finally(() => setLoading(false));
  }, [id]);

  const descargarPDF = async () => {
    setDescargando(true);
    try {
      const resp = await auditorAPI.reportePDF(id);
      const url = URL.createObjectURL(new Blob([resp.data], { type: 'application/pdf' }));
      const a = document.createElement('a');
      a.href = url;
      a.download = `reporte_riesgo_${perfil?.dni}_${new Date().toISOString().slice(0,10)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert('Error al generar el reporte PDF.');
    } finally {
      setDescargando(false);
    }
  };

  if (loading) return <div className="auditor-layout"><Sidebar /><main className="auditor-main"><Spinner /></main></div>;

  return (
    <div className="auditor-layout">
      <Sidebar />
      <main className="auditor-main">
        <div className="perfil-riesgo-header">
          <button className="btn-back" onClick={() => navigate('/auditor/buscador')}>← Volver</button>
          <h1 className="auditor-page-title">
            {perfil?.nombre} {perfil?.apellido}
          </h1>
          <button className="btn-pdf" onClick={descargarPDF} disabled={descargando}>
            {descargando ? 'Generando…' : '📄 Descargar PDF'}
          </button>
        </div>

        <div className="perfil-riesgo-grid">
          {/* Gauge */}
          <Card className="gauge-card-auditor">
            <h2 className="section-title">Índice de riesgo actual</h2>
            <Gauge value={perfil?.indice_actual ?? 0} nivel={perfil?.nivel_actual ?? 'Bajo'} />
            {perfil?.indice_promedio_6m != null && (
              <p className="promedio-6m">Promedio 6 meses: <strong>{perfil.indice_promedio_6m}</strong></p>
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
