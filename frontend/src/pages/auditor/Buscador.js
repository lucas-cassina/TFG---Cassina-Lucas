import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { auditorAPI } from '../../api/client';
import Sidebar from '../../components/Sidebar';
import Card from '../../components/Card';
import Badge from '../../components/Badge';
import './Auditor.css';

export default function Buscador() {
  const [dni, setDni] = useState('');
  const [poliza, setPoliza] = useState('');
  const [result, setResult] = useState(null);
  const [recientes, setRecientes] = useState(() => {
    try { return JSON.parse(localStorage.getItem('cias_auditor_recientes')) || []; } catch { return []; }
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const buscar = async (e) => {
    e.preventDefault();
    if (!dni && !poliza) { setError('Ingresá DNI o número de póliza'); return; }
    setError(''); setLoading(true); setResult(null);
    try {
      const r = await auditorAPI.buscarAsegurado({ dni: dni || undefined, numero_poliza: poliza || undefined });
      const perfil = await auditorAPI.perfilRiesgo(r.data.conductor_id);
      const enriched = { ...r.data, ...perfil.data };
      setResult(enriched);
      const nextRecientes = [
        enriched,
        ...recientes.filter(item => item.conductor_id !== enriched.conductor_id),
      ].slice(0, 3);
      setRecientes(nextRecientes);
      localStorage.setItem('cias_auditor_recientes', JSON.stringify(nextRecientes));
    } catch (err) {
      setError(err.response?.data?.detail || 'No encontrado');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auditor-layout">
      <Sidebar />
      <main className="auditor-main">
        <div className="auditor-topbar">
          <span>Auditoría / Buscar asegurado</span>
          <div><strong>● Sesión activa</strong><span>Auditor CIAS</span></div>
        </div>

        <section className="auditor-hero">
          <h1 className="auditor-page-title">Buscar asegurado</h1>
          <p>Ingresá el DNI o número de póliza del asegurado para consultar su perfil de riesgo telemétrico.</p>
        </section>

        <Card className="buscador-card">
          <form onSubmit={buscar} className="buscador-form">
            <div className="form-group">
              <label>DNI del asegurado</label>
              <input value={dni} onChange={e => setDni(e.target.value)} placeholder="30123456" />
            </div>
            <div className="buscador-sep">o</div>
            <div className="form-group">
              <label>Número de póliza</label>
              <input value={poliza} onChange={e => setPoliza(e.target.value)} placeholder="POL-00001" />
            </div>
            {error && <p className="form-error">{error}</p>}
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Buscando…' : '🔍 Buscar'}
            </button>
          </form>
        </Card>

        {result && (
          <Card className="result-card">
            <div className="result-profile">
              <span className="result-avatar">{initials(result)}</span>
              <div>
                <h2>{result.nombre} {result.apellido}</h2>
                <p>DNI {result.dni}</p>
                <p>{result.email}</p>
                <p>{result.numero_poliza || 'Sin póliza cargada'}</p>
                <small>{result.marca_vehiculo ? `${result.marca_vehiculo} ${result.modelo_vehiculo}` : 'Vehículo no informado'}</small>
              </div>
            </div>
            <div className="result-risk">
              <span>Índice de riesgo actual</span>
              <strong>{result.indice_actual ?? '—'}</strong>
              <small>{result.nivel_actual ? `Riesgo ${result.nivel_actual.toLowerCase()}` : 'Sin datos'}</small>
              <em>{result.indice_promedio_6m != null ? `Promedio 6 meses: ${result.indice_promedio_6m}` : 'Sin historial suficiente'}</em>
            </div>
            <div className="result-actions">
              <button
                className="btn-primary"
                onClick={() => navigate(`/auditor/perfil/${result.conductor_id}`)}
              >
                Ver perfil completo →
              </button>
              <button
                className="btn-outline"
                onClick={() => navigate(`/auditor/reporte/${result.conductor_id}`)}
              >
                ⇩ Generar reporte PDF
              </button>
            </div>
          </Card>
        )}

        <section className="auditor-recents">
          <p className="section-title">Consultas recientes</p>
          {recientes.length === 0 ? (
            <p className="empty-msg">Todavía no hiciste consultas en esta sesión.</p>
          ) : recientes.map((item) => (
            <button key={item.conductor_id} className="recent-card" onClick={() => navigate(`/auditor/perfil/${item.conductor_id}`)}>
              <strong>{item.nombre} {item.apellido}</strong>
              <span>DNI {item.dni}</span>
              <Badge label={item.nivel_actual || 'Sin datos'} />
              <small>→</small>
            </button>
          ))}
        </section>
      </main>
    </div>
  );
}

function initials(person) {
  return `${person?.nombre?.[0] || ''}${person?.apellido?.[0] || ''}`.toUpperCase() || 'CI';
}
