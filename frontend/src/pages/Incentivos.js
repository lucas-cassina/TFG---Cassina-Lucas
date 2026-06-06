import { useState, useEffect } from 'react';
import { incentivosAPI } from '../api/client';
import Card from '../components/Card';
import Badge from '../components/Badge';
import Spinner from '../components/Spinner';
import BottomNav from '../components/BottomNav';
import './Incentivos.css';

const NIVEL_ICONO = { Bronce: '🥉', Plata: '🥈', Oro: '🥇', 'Sin nivel': '⬜' };
const NIVEL_ORDEN = ['Sin nivel', 'Bronce', 'Plata', 'Oro'];

export default function Incentivos() {
  const [nivel, setNivel] = useState(null);
  const [disponibles, setDisponibles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    incentivosAPI.disponibles()
      .then(r => {
        setNivel(r.data.nivel_actual);
        setDisponibles(r.data.incentivos || []);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <><Spinner /><BottomNav /></>;

  const idxActual = NIVEL_ORDEN.indexOf(nivel);

  return (
    <div className="incentivos">
      <header className="incentivos__header">
        <h1>Mis Incentivos</h1>
      </header>

      <main className="incentivos__main">
        {/* Nivel actual */}
        <Card className="nivel-card">
          <div className="nivel-icon">{NIVEL_ICONO[nivel] || '⬜'}</div>
          <div className="nivel-info">
            <h2 className="nivel-nombre">{nivel}</h2>
            <p className="nivel-desc">
              {nivel === 'Sin nivel' && 'Completá 1 mes con índice Bajo para alcanzar Bronce.'}
              {nivel === 'Bronce' && 'Mantené índice Bajo por 3 meses para alcanzar Plata.'}
              {nivel === 'Plata' && 'Mantené índice Bajo por 6 meses para alcanzar Oro.'}
              {nivel === 'Oro' && '¡Nivel máximo alcanzado! Seguí conduciendo de forma responsable.'}
            </p>
          </div>
        </Card>

        {/* Progresión de niveles */}
        <Card>
          <h2 className="section-title">Progresión</h2>
          <div className="progresion">
            {NIVEL_ORDEN.slice(1).map((n, i) => (
              <div key={n} className={`prog-step ${i < idxActual ? 'alcanzado' : i === idxActual - 1 ? 'actual' : ''}`}>
                <div className="prog-icono">{NIVEL_ICONO[n]}</div>
                <span className="prog-label">{n}</span>
                {i < NIVEL_ORDEN.slice(1).length - 1 && <div className="prog-linea" />}
              </div>
            ))}
          </div>
        </Card>

        {/* Lista de incentivos */}
        <Card>
          <h2 className="section-title">Beneficios disponibles</h2>
          {disponibles.length === 0
            ? <p className="empty-msg">No hay beneficios configurados aún.</p>
            : (
              <div className="incentivos-list">
                {disponibles.map(inc => (
                  <div key={inc.id} className={`incentivo-item ${inc.accesible ? '' : 'bloqueado'}`}>
                    <div className="incentivo-header">
                      <span className="incentivo-nombre">{inc.nombre}</span>
                      <Badge label={inc.nivel_requerido} />
                    </div>
                    <p className="incentivo-desc">{inc.descripcion}</p>
                    {!inc.accesible && (
                      <p className="incentivo-lock">🔒 Requiere nivel {inc.nivel_requerido}</p>
                    )}
                  </div>
                ))}
              </div>
            )
          }
        </Card>
      </main>
      <BottomNav />
    </div>
  );
}
