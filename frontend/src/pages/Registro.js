import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import CiasLogo from '../components/CiasLogo';
import './Auth.css';

export default function Registro() {
  const [form, setForm] = useState({ nombre:'', apellido:'', dni:'', email:'', password:'', telefono:'' });
  const [error, setError]     = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = e => setForm(f => ({ ...f, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      await register(form);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al registrarse');
    } finally { setLoading(false); }
  };

  return (
    <div className="auth-page">
      <div className="auth-logo-area auth-logo-area--register">
        <CiasLogo size={72} />
        <h1 className="auth-brand">CIAS</h1>
        <p className="auth-tagline">Alta digital de asegurado</p>
      </div>

      <header className="auth-register-bar">
        <button type="button" onClick={() => navigate('/login')}>←</button>
        <h1>Registro</h1>
      </header>

      <div className="auth-card auth-card--register">
        <h2 className="auth-title">Creá tu cuenta</h2>
        <p className="auth-subtitle">Completá tus datos personales.</p>
        <p className="auth-section-label">Datos personales</p>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label>Nombre</label>
            <input name="nombre" value={form.nombre} onChange={handleChange} required placeholder="Ej: Lucas" />
          </div>
          <div className="form-group">
            <label>Apellido</label>
            <input name="apellido" value={form.apellido} onChange={handleChange} required placeholder="Ej: Cassina" />
          </div>
          <div className="form-group">
            <label>DNI</label>
            <input name="dni" value={form.dni} onChange={handleChange} required placeholder="Ej: 38421567" />
            <small>Sin puntos ni espacios.</small>
          </div>
          <div className="form-group">
            <label>Correo electrónico</label>
            <input name="email" type="email" value={form.email} onChange={handleChange} required placeholder="tu@email.com" />
          </div>
          <div className="form-group">
            <label>Contraseña</label>
            <input name="password" type="password" value={form.password} onChange={handleChange} required placeholder="Mínimo 8 caracteres" />
          </div>
          {error && <p className="auth-error">{error}</p>}
          <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
            {loading ? 'Creando cuenta…' : 'Continuar'}
          </button>
        </form>

        <p className="auth-footer">¿Ya tenés cuenta? <Link to="/login">Iniciá sesión</Link></p>
      </div>
    </div>
  );
}
