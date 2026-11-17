import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { auditorAPI } from '../../api/client';
import Sidebar from '../../components/Sidebar';
import Card from '../../components/Card';
import Badge from '../../components/Badge';
import Spinner from '../../components/Spinner';
import './Auditor.css';

export default function Reporte() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [perfil, setPerfil] = useState(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    auditorAPI.perfilRiesgo(id)
      .then(r => setPerfil(r.data))
      .catch(() => setError('No pudimos cargar los datos del asegurado.'))
      .finally(() => setLoading(false));
  }, [id]);

  const descargarPdf = async () => {
    setDownloading(true);
    setError('');
    try {
      const response = await auditorAPI.reportePDF(id);
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = `reporte_riesgo_${perfil?.dni || id}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.response?.data?.detail || 'No pudimos generar el PDF.');
    } finally {
      setDownloading(false);
    }
  };

  if (loading) return <div className="auditor-layout"><Sidebar /><main className="auditor-main"><Spinner /></main></div>;

  return (
    <div className="auditor-layout">
      <Sidebar />
      <main className="auditor-main">
        <div className="auditor-topbar auditor-topbar--report">
          <button onClick={() => navigate(`/auditor/perfil/${id}`)}>← Volver al perfil</button>
          <span>Auditoría / {perfil?.nombre} {perfil?.apellido} / Generar reporte</span>
        </div>

        <section className="auditor-hero auditor-hero--report">
          <h1 className="auditor-page-title">Generar reporte individual</h1>
          <p>El reporte se genera en formato PDF con los datos actuales del backend.</p>
        </section>

        <div className="report-layout">
          <Card className="report-config">
            <h2>Contenido del reporte</h2>
            <label>Asegurado</label>
            <div className="report-insured"><span>{initials(perfil)}</span> {perfil?.nombre} {perfil?.apellido} · DNI {perfil?.dni}</div>
            <label>Período</label>
            <select>
              <option>Últimos 180 días</option>
            </select>
            <label>Incluir en el reporte</label>
            {[
              'Índice de riesgo y nivel asignado',
              'Evolución histórica del índice',
              'Desglose de variables de conducción',
              'Listado de alertas detectadas',
              'Datos del vehículo y póliza',
            ].map(item => (
              <label key={item} className="report-check"><input type="checkbox" checked disabled readOnly /> {item}</label>
            ))}

            {error && <p className="form-error">{error}</p>}
            <button className="btn btn-primary btn-block" onClick={descargarPdf} disabled={downloading || (!!error && !perfil)}>
              {downloading ? 'Generando…' : '⇩ Generar y descargar PDF'}
            </button>
          </Card>

          <Card className={`report-preview${expanded ? ' expanded' : ''}`}>
            <div className="report-preview-bar">
              <span>Resumen del contenido del reporte <Badge label="PDF" /></span>
              <button onClick={() => setExpanded(v => !v)}>{expanded ? 'Vista normal' : 'Pantalla completa'}</button>
            </div>
            <article className="report-page">
              <header>
                <div><span className="report-logo">C</span><strong>CIAS</strong><small>Ciudadano Asegurado</small></div>
                <b>Reporte de Riesgo Telemétrico</b>
              </header>
              <div className="report-line" />
              <section className="report-meta">
                <p>Asegurado: {perfil?.nombre} {perfil?.apellido}<br />DNI: {perfil?.dni}<br />Generado: {new Date().toLocaleDateString('es-AR')}</p>
                <p>Período: Últimos 180 días<br />Póliza: {perfil?.numero_poliza || 'Sin póliza'}</p>
              </section>
              <h3>Índice de Riesgo</h3>
              <div className="report-score"><strong>{perfil?.indice_actual ?? '—'}</strong><Badge label={perfil?.nivel_actual ? `Riesgo ${perfil.nivel_actual.toLowerCase()}` : 'Sin datos'} /></div>
              <p>El índice de riesgo promedio de los últimos 180 días fue de {perfil?.indice_promedio_6m ?? '—'} puntos.</p>
              <h3>Desglose de Variables</h3>
              <table>
                <tbody>
                  {['Velocidad', 'Frenadas bruscas', 'Aceleraciones', 'Horario', 'Distancia'].map((row, i) => (
                    <tr key={row}><td>{row}</td><td>{[25,25,20,15,15][i]}%</td><td>Incluido en PDF</td><td>Según motor de riesgo</td></tr>
                  ))}
                </tbody>
              </table>
            </article>
          </Card>
        </div>
      </main>
    </div>
  );
}

function initials(person) {
  return `${person?.nombre?.[0] || ''}${person?.apellido?.[0] || ''}`.toUpperCase() || 'CI';
}
