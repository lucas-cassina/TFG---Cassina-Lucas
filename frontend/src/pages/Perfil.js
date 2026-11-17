import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { conductorAPI } from '../api/client';
import { useAuth } from '../context/AuthContext';
import BottomNav from '../components/BottomNav';
import AppHeader from '../components/AppHeader';
import Spinner from '../components/Spinner';
import './Perfil.css';

const FORM_EMPTY = {
  numero_poliza: '',
  marca_vehiculo: '',
  modelo_vehiculo: '',
  anio_vehiculo: '',
  patente: '',
  zona: '',
  fecha_inicio: '',
  fecha_vencimiento: '',
};

export default function Perfil() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [perfil, setPerfil] = useState(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [descargando, setDescargando] = useState(false);
  const [descargandoStats, setDescargandoStats] = useState(false);
  const [mostrarForm, setMostrarForm] = useState(false);
  const [form, setForm] = useState(FORM_EMPTY);
  const [guardando, setGuardando] = useState(false);

  const cargarPerfil = () =>
    conductorAPI.perfil()
      .then(r => setPerfil(r.data))
      .catch(() => setMessage('No pudimos cargar tus datos de perfil.'))
      .finally(() => setLoading(false));

  useEffect(() => { cargarPerfil(); }, []);

  const poliza = perfil?.poliza;
  const conductor = perfil?.conductor;

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleDescargarEstadisticas = async () => {
    setDescargandoStats(true);
    setMessage('');
    try {
      const response = await conductorAPI.estadisticasPDF();
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = `estadisticas_cias.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setMessage(err.response?.data?.detail || 'No pudimos generar el PDF de estadísticas.');
    } finally {
      setDescargandoStats(false);
    }
  };

  const handleDescargarPoliza = async () => {
    setDescargando(true);
    setMessage('');
    try {
      const response = await conductorAPI.polizaPDF();
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = `poliza_${poliza?.numero_poliza || 'cias'}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setMessage(err.response?.data?.detail || 'No pudimos generar el PDF de la póliza.');
    } finally {
      setDescargando(false);
    }
  };

  const abrirForm = () => {
    setForm(poliza ? {
      numero_poliza:   poliza.numero_poliza,
      marca_vehiculo:  poliza.marca_vehiculo,
      modelo_vehiculo: poliza.modelo_vehiculo,
      anio_vehiculo:   String(poliza.anio_vehiculo),
      patente:         poliza.patente,
      zona:            poliza.zona || '',
      fecha_inicio:    poliza.fecha_inicio,
      fecha_vencimiento: poliza.fecha_vencimiento,
    } : FORM_EMPTY);
    setMessage('');
    setMostrarForm(true);
  };

  const handleChange = (e) =>
    setForm(f => ({ ...f, [e.target.name]: e.target.value }));

  const handleGuardar = async (e) => {
    e.preventDefault();
    setGuardando(true);
    setMessage('');
    try {
      await conductorAPI.cargarPoliza({
        ...form,
        anio_vehiculo: Number(form.anio_vehiculo),
      });
      setMostrarForm(false);
      setLoading(true);
      await cargarPerfil();
      setMessage('Póliza guardada correctamente.');
    } catch (err) {
      setMessage(err.response?.data?.detail || 'No pudimos guardar la póliza.');
    } finally {
      setGuardando(false);
    }
  };

  if (loading) return (
    <div className="perfil">
      <AppHeader />
      <div className="perfil-content"><Spinner /></div>
      <BottomNav />
    </div>
  );

  return (
    <div className="perfil">
      <AppHeader />

      <div className="perfil-content">
        <section className="perfil-section perfil-policy">
          <h2>Mi póliza</h2>
          {[
            ['Número de póliza', poliza?.numero_poliza],
            ['Vehículo', poliza ? `${poliza.marca_vehiculo} ${poliza.modelo_vehiculo} ${poliza.anio_vehiculo}` : null],
            ['Patente', poliza?.patente],
            ['Zona', poliza?.zona],
            ['Vigencia', poliza ? `${formatDate(poliza.fecha_inicio)} — ${formatDate(poliza.fecha_vencimiento)}` : null],
          ].map(([lbl, val]) => (
            <div key={lbl} className="dato-row">
              <span className="dato-lbl">{lbl}</span>
              <span className="dato-val">{val || '—'}</span>
            </div>
          ))}
          <div className="dato-row">
            <span className="dato-lbl">Estado</span>
            <span className="perfil-status">{poliza ? 'Vigente' : 'Sin póliza'}</span>
          </div>

          <div className="perfil-poliza-acciones">
            <button
              className="perfil-link"
              onClick={handleDescargarPoliza}
              disabled={descargando || !poliza}
            >
              {descargando ? 'Generando PDF…' : 'Ver póliza completa (PDF)'}
            </button>
            <button
              className="perfil-link perfil-link-carga"
              onClick={abrirForm}
            >
              {poliza ? 'Actualizar póliza' : 'Cargar mi póliza'}
            </button>
          </div>

          <div className="perfil-stats-accion">
            <button
              className="btn btn-secondary btn-block"
              onClick={handleDescargarEstadisticas}
              disabled={descargandoStats}
            >
              {descargandoStats ? 'Generando PDF…' : 'Descargar mis estadísticas (PDF)'}
            </button>
          </div>

          {mostrarForm && (
            <form className="poliza-form" onSubmit={handleGuardar}>
              <h3>{poliza ? 'Actualizar póliza' : 'Cargar póliza'}</h3>

              <div className="poliza-form-grid">
                <label>
                  <span>N° de póliza</span>
                  <input name="numero_poliza" value={form.numero_poliza}
                    onChange={handleChange} required placeholder="CIAS-2026-000001" />
                </label>
                <label>
                  <span>Marca</span>
                  <input name="marca_vehiculo" value={form.marca_vehiculo}
                    onChange={handleChange} required placeholder="Volkswagen" />
                </label>
                <label>
                  <span>Modelo</span>
                  <input name="modelo_vehiculo" value={form.modelo_vehiculo}
                    onChange={handleChange} required placeholder="Gol Trend" />
                </label>
                <label>
                  <span>Año</span>
                  <input name="anio_vehiculo" value={form.anio_vehiculo}
                    onChange={handleChange} required type="number"
                    min="1980" max="2030" placeholder="2020" />
                </label>
                <label>
                  <span>Patente</span>
                  <input name="patente" value={form.patente}
                    onChange={handleChange} required placeholder="AB 123 CD" />
                </label>
                <label>
                  <span>Zona</span>
                  <input name="zona" value={form.zona}
                    onChange={handleChange} placeholder="Córdoba Capital" />
                </label>
                <label>
                  <span>Inicio de vigencia</span>
                  <input name="fecha_inicio" value={form.fecha_inicio}
                    onChange={handleChange} required type="date" />
                </label>
                <label>
                  <span>Vencimiento</span>
                  <input name="fecha_vencimiento" value={form.fecha_vencimiento}
                    onChange={handleChange} required type="date" />
                </label>
              </div>

              <div className="poliza-form-actions">
                <button type="button" className="btn btn-ghost"
                  onClick={() => setMostrarForm(false)} disabled={guardando}>
                  Cancelar
                </button>
                <button type="submit" className="btn btn-primary" disabled={guardando}>
                  {guardando ? 'Guardando…' : 'Guardar'}
                </button>
              </div>
            </form>
          )}
        </section>

        <section className="perfil-section perfil-account">
          <h2>Mi cuenta</h2>
          {[
            ['Nombre', `${conductor?.nombre || user?.nombre || ''} ${conductor?.apellido || user?.apellido || ''}`.trim()],
            ['Email', conductor?.email],
            ['DNI', conductor?.dni],
            ['Teléfono', conductor?.telefono],
          ].map(([lbl, val]) => (
            <div key={lbl} className="dato-row">
              <span className="dato-lbl">{lbl}</span>
              <span className="dato-val">{val || '—'}</span>
            </div>
          ))}
          <div className="perfil-menu-row">
            <span>Notificaciones</span>
            <button className="perfil-switch" onClick={() => setMessage('Preferencia de notificaciones guardada solo en esta sesión.')} aria-label="Cambiar notificaciones"><span /></button>
          </div>
          <button className="perfil-menu-row" onClick={() => setMessage('La gestión de privacidad y datos requiere un endpoint backend pendiente.')}>
            <span>Privacidad y datos</span>
            <small>›</small>
          </button>
          <button className="perfil-menu-row" onClick={() => setMessage('Para soporte, contactá a soporte@cias.demo.')}>
            <span>Ayuda y soporte</span>
            <small>›</small>
          </button>
        </section>

        {message && <p className="perfil-message">{message}</p>}

        <button className="btn btn-danger btn-block" onClick={handleLogout}>Cerrar sesión</button>
      </div>

      <BottomNav />
    </div>
  );
}

function formatDate(value) {
  if (!value) return '—';
  return new Date(`${value}T00:00:00`).toLocaleDateString('es-AR');
}
