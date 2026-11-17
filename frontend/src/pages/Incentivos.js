import { useState, useEffect } from 'react';
import { indiceAPI, incentivosAPI } from '../api/client';
import { useAuth } from '../context/AuthContext';
import Spinner from '../components/Spinner';
import BottomNav from '../components/BottomNav';
import AppHeader from '../components/AppHeader';
import './Incentivos.css';

const NIVEL_ICONO = { Bronce:'🥉', Plata:'🥈', Oro:'🥇', 'Sin nivel':'⬜' };
const NIVELES = ['Bronce', 'Plata', 'Oro'];
const MESES_REQUERIDOS = { Bronce: 1, Plata: 3, Oro: 6 };
const NIVEL_BORDER = { Bronce: '#cd7f32', Plata: '#a8a9ad', Oro: '#e2e8f0' };

export default function Incentivos() {
  const { user } = useAuth();
  const [resumen, setResumen]         = useState(null);
  const [disponibles, setDisponibles] = useState([]);
  const [stats, setStats]             = useState(null);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState('');

  useEffect(() => {
    Promise.all([
      incentivosAPI.miNivel(),
      incentivosAPI.disponibles(),
      indiceAPI.estadisticasMes(),
    ])
      .then(([nivelResp, dispResp, statsResp]) => {
        setResumen(nivelResp.data);
        setDisponibles(dispResp.data?.incentivos || []);
        setStats(statsResp.data);
      })
      .catch((err) => {
        console.error(err);
        setError('No pudimos cargar tus incentivos en este momento.');
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="incentivos incentivos--loading">
      <div className="incentivos-loading"><Spinner /></div>
      <BottomNav />
    </div>
  );

  const nivel        = resumen?.nivel_incentivo || 'Sin nivel';
  const mesesBajo    = resumen?.meses_consecutivos_bajo || 0;
  const proximoNivel = siguienteNivel(nivel);
  const mesesObjetivo = proximoNivel ? MESES_REQUERIDOS[proximoNivel] : MESES_REQUERIDOS.Oro;
  const faltan       = Math.max(0, mesesObjetivo - mesesBajo);
  const progreso     = Math.min(100, Math.round((mesesBajo / mesesObjetivo) * 100));
  return (
    <div className="incentivos">

      <AppHeader />

      {/* Tarjeta de puntos */}
      <section className="points-card">
        {/* Decoración esquina superior derecha */}
        <div className="points-deco" aria-hidden="true">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M2 12h4l3 9 6-18 3 9h4"/>
          </svg>
        </div>

        <p className="points-label">Puntos acumulados</p>
        <div className="points-main">
          <span className="points-star">⭐</span>
          <strong className="points-num">{resumen?.puntos_acumulados ?? 0}</strong>
          <small className="points-unit">pts</small>
        </div>
        <p className="points-name">{user?.nombre} {user?.apellido}</p>
        <div className="points-badge">NIVEL {nivel.toUpperCase()} {NIVEL_ICONO[nivel]}</div>
        <div className="points-divider" />
        <div className="points-meta">
          <div className="points-stat">
            <span className="points-stat-icon">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
                <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
              </svg>
            </span>
            <span className="points-stat-text"><span className="points-stat-label">Sesiones</span><strong>{stats?.total_sesiones ?? 0}</strong></span>
          </div>
          <div className="points-stat-divider" />
          <div className="points-stat">
            <span className="points-stat-icon">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
              </svg>
            </span>
            <span className="points-stat-text"><span className="points-stat-label">Índice del mes</span><strong>{stats?.indice_promedio ?? 0} — {stats?.nivel_predominante || '–'}</strong></span>
          </div>
        </div>
      </section>

      {error && <p className="incentivos-error">{error}</p>}

      {/* Progreso */}
      <section className="incentivos-progress">
        <h2>{proximoNivel ? `Progreso hacia Nivel ${proximoNivel} ${NIVEL_ICONO[proximoNivel]}` : 'Nivel Oro alcanzado 🥇'}</h2>
        <div className="incentivos-track">
          <div className="incentivos-track-fill" style={{ width: `${progreso}%` }} />
          <div className="incentivos-track-thumb" style={{ left: `${progreso}%` }} />
        </div>
        <div className="incentivos-progress-row">
          <span>{mesesBajo} meses consecutivos</span>
          <strong>{proximoNivel ? `Faltan ${faltan} meses más` : 'Máximo nivel activo'}</strong>
        </div>
        <div className="incentivos-tip">
          💡 Mantené tu índice Bajo{proximoNivel
            ? ` durante ${faltan} meses más para alcanzar Nivel ${proximoNivel}.`
            : ' para conservar tu nivel.'}
          <p className="incentivos-tip-sub">Un mes con índice Medio reinicia el contador, pero conservás tu nivel actual.</p>
        </div>
      </section>

      {/* Programa de beneficios ilustrativos */}
      <div className="incentivos-content">
        <p className="section-label">Programa de beneficios ilustrativos</p>

        {NIVELES.map((n, i) => {
          const beneficios    = disponibles.filter(inc => inc.nivel_requerido === n);
          const esNivelActual = n === nivel;
          const estaAlcanzado = nivelCumple(nivel, n);
          const estaBloqueado = !estaAlcanzado;

          return (
            <div
              key={n}
              className={`benefit-card${estaBloqueado ? ' benefit-card--locked' : ''}${esNivelActual ? ' benefit-card--current' : ''}`}
              style={{ '--nivel-border': NIVEL_BORDER[n] }}
            >
              <div className="benefit-head">
                <div className="benefit-title-row">
                  <span className="benefit-emoji">{NIVEL_ICONO[n]}</span>
                  <h3 className="benefit-level-name">Nivel {n}</h3>
                </div>
                <span className={`nivel-badge nivel-badge--${esNivelActual ? 'actual' : estaAlcanzado ? 'alcanzado' : 'locked'}`}>
                  {esNivelActual ? '⭐ Nivel actual' : estaAlcanzado ? '✓ Alcanzado' : '🔒 Por desbloquear'}
                </span>
              </div>

              <p className="benefit-req">
                <strong>Requisito:</strong>{' '}
                {i === 0 ? '1 mes' : i === 1 ? '3 meses consecutivos' : '6 meses consecutivos'} con índice de riesgo Bajo
              </p>

              {beneficios.length > 0 && (
                <ul className="benefit-list">
                  {beneficios.map(inc => (
                    <li key={inc.id} className={`benefit-item${estaBloqueado ? ' benefit-item--locked' : ''}`}>
                      <span className="benefit-item-icon">{estaBloqueado ? '🔒' : '✓'}</span>
                      <span>{inc.nombre}{inc.descripcion ? `: ${inc.descripcion}` : ''}</span>
                    </li>
                  ))}
                </ul>
              )}

              {/* Footer: nivel actual */}
              {esNivelActual && (
                <div className="benefit-footer">
                  <p className="benefit-footer-title">Nivel {n} alcanzado ✓</p>
                  <p className="benefit-footer-desc">
                    {proximoNivel
                      ? `Mantené índice Bajo ${faltan} meses más para alcanzar ${proximoNivel} (actualmente ${mesesBajo}/${mesesObjetivo} meses hacia ${proximoNivel})`
                      : 'Seguí conduciendo de forma prudente para conservar Oro.'}
                  </p>
                </div>
              )}

              {/* Footer: alcanzado pero no actual */}
              {estaAlcanzado && !esNivelActual && (
                <p className="benefit-date">
                  {resumen?.fecha_nivel ? `Alcanzado el ${resumen.fecha_nivel}` : `Nivel ${n} alcanzado ✓`}
                </p>
              )}

              {/* Footer: bloqueado Oro → link */}
              {estaBloqueado && n === 'Oro' && (
                <a href="#como-funciona" className="benefit-link">¿Cómo llegar al Nivel Oro?</a>
              )}
            </div>
          );
        })}
      </div>

      {/* ¿Cómo funciona el programa? */}
      <div className="info-section" id="como-funciona">
        <div className="info-header">
          <span className="info-header-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
          </span>
          <strong>¿Cómo funciona el programa?</strong>
        </div>

        <p className="info-intro">
          El prototipo calcula el nivel con los meses que tienen sesiones registradas. El mes en curso es provisional; los beneficios son ilustrativos y no modifican tu póliza.
        </p>

        <div className="info-card">
          <p className="info-card-title">Cómo ascender de nivel:</p>
          <ul className="info-list">
            <li><strong>Bronce:</strong> 1 mes consecutivo con índice Bajo</li>
            <li><strong>Plata:</strong> 3 meses consecutivos con índice Bajo</li>
            <li><strong>Oro:</strong> 6 meses consecutivos con índice Bajo</li>
          </ul>
        </div>

        <div className="info-card">
          <p className="info-card-title">Reglas importantes:</p>
          <ul className="info-list">
            <li>Un mes con índice <strong>Medio</strong> no penaliza el nivel alcanzado, pero reinicia el contador de meses consecutivos para ascender.</li>
            <li>Un mes con índice <strong>Alto</strong>, o dos meses consecutivos con índice Medio, reducen el nivel en un escalón (Oro → Plata, Plata → Bronce, Bronce → sin nivel).</li>
          </ul>
        </div>

        <p className="info-intro">
          Los <strong>puntos</strong> se calculan por mes: 10 para nivel Bajo y 3 para Medio. En esta demostración no se realizan canjes ni se otorgan descuentos reales.
        </p>

        
      </div>

      <BottomNav />
    </div>
  );
}

function siguienteNivel(nivel) {
  if (nivel === 'Sin nivel') return 'Bronce';
  if (nivel === 'Bronce')    return 'Plata';
  if (nivel === 'Plata')     return 'Oro';
  return null;
}

function anteriorNivel(nivel) {
  if (nivel === 'Oro')   return 'Plata';
  if (nivel === 'Plata') return 'Bronce';
  return 'Sin nivel';
}

function nivelCumple(actual, requerido) {
  const orden = ['Sin nivel', 'Bronce', 'Plata', 'Oro'];
  return orden.indexOf(actual) >= orden.indexOf(requerido);
}
