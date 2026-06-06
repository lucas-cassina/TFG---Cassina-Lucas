import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { indiceAPI } from '../api/client';
import Card from '../components/Card';
import Badge from '../components/Badge';
import Spinner from '../components/Spinner';
import BottomNav from '../components/BottomNav';
import './Historial.css';

export default function Historial() {
  const [sesiones, setSesiones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [desde, setDesde] = useState('');
  const [hasta, setHasta] = useState('');

  const cargar = () => {
    setLoading(true);
    const params = {};
    if (desde) params.desde = new Date(desde).toISOString();
    if (hasta) params.hasta = new Date(hasta).toISOString();
    indiceAPI.historial(params)
      .then(r => setSesiones(r.data || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(cargar, []);

  const chartData = sesiones
    .filter(s => s.indice != null)
    .slice().reverse()
    .map(s => ({
      fecha: new Date(s.inicio).toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit' }),
      indice: s.indice,
    }));

  return (
    <div className="historial">
      <header className="historial__header">
        <h1>Historial de sesiones</h1>
      </header>

      <main className="historial__main">
        {/* Filtros */}
        <Card className="historial__filtros">
          <h2 className="section-title">Filtrar por fecha</h2>
          <div className="filtros-row">
            <div className="form-group-sm">
              <label>Desde</label>
              <input type="date" value={desde} onChange={e => setDesde(e.target.value)} />
            </div>
            <div className="form-group-sm">
              <label>Hasta</label>
              <input type="date" value={hasta} onChange={e => setHasta(e.target.value)} />
            </div>
            <button className="btn-sm" onClick={cargar}>Aplicar</button>
          </div>
        </Card>

        {/* Gráfico de evolución */}
        {chartData.length > 1 && (
          <Card>
            <h2 className="section-title">Evolución del índice</h2>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="fecha" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                <Tooltip />
                <ReferenceLine y={70} stroke="var(--color-riesgo-bajo)" strokeDasharray="4 4" />
                <ReferenceLine y={85} stroke="var(--color-riesgo-medio)" strokeDasharray="4 4" />
                <Line type="monotone" dataKey="indice" stroke="var(--color-primary-light)"
                  strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 5 }} />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        )}

        {/* Tabla de sesiones */}
        {loading ? <Spinner /> : (
          <Card>
            <h2 className="section-title">Sesiones ({sesiones.length})</h2>
            {sesiones.length === 0
              ? <p className="empty-msg">No hay sesiones en el período seleccionado.</p>
              : (
                <div className="sesiones-list">
                  {sesiones.map(s => (
                    <div key={s.sesion_id} className="sesion-row">
                      <div className="sesion-fecha">
                        {new Date(s.inicio).toLocaleDateString('es-AR', { day:'2-digit', month:'2-digit', year:'numeric' })}
                      </div>
                      <div className="sesion-info">
                        <span className="sesion-km">{(s.distancia_km ?? 0).toFixed(1)} km</span>
                        {s.nivel && <Badge label={s.nivel} />}
                      </div>
                      {s.indice != null && (
                        <div className="sesion-indice">{s.indice}</div>
                      )}
                    </div>
                  ))}
                </div>
              )
            }
          </Card>
        )}
      </main>

      <BottomNav />
    </div>
  );
}
