import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { auditorAPI } from '../../api/client';
import Sidebar from '../../components/Sidebar';
import Card from '../../components/Card';
import './Auditor.css';

export default function Buscador() {
  const [dni, setDni] = useState('');
  const [poliza, setPoliza] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const buscar = async (e) => {
    e.preventDefault();
    if (!dni && !poliza) { setError('Ingresá DNI o número de póliza'); return; }
    setError(''); setLoading(true); setResult(null);
    try {
      const r = await auditorAPI.buscarAsegurado({ dni: dni || undefined, numero_poliza: poliza || undefined });
      setResult(r.data);
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
        <h1 className="auditor-page-title">Buscador de Asegurados</h1>

        <Card className="buscador-card">
          <form onSubmit={buscar} className="buscador-form">
            <div className="form-group">
              <label>DNI del asegurado</label>
              <input value={dni} onChange={e => setDni(e.target.value)} placeholder="30123456" />
            </div>
            <div className="buscador-sep">— o —</div>
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
            <h2 className="section-title">Asegurado encontrado</h2>
            <div className="result-info">
              <div className="result-row"><span>Nombre</span><strong>{result.nombre} {result.apellido}</strong></div>
              <div className="result-row"><span>DNI</span><strong>{result.dni}</strong></div>
              <div className="result-row"><span>Email</span><strong>{result.email}</strong></div>
            </div>
            <button
              className="btn-primary"
              onClick={() => navigate(`/auditor/perfil/${result.conductor_id}`)}
            >
              Ver perfil de riesgo →
            </button>
          </Card>
        )}
      </main>
    </div>
  );
}
