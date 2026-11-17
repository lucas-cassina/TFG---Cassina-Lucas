import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import CiasLogo from '../components/CiasLogo';
import './Auth.css';

export default function Login() {
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [error, setError]       = useState('');
  const [loading, setLoading]   = useState(false);
  const [mode, setMode]         = useState('conductor');
  const { login, logout } = useAuth();
  const navigate   = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      const user = await login(email, password);
      if (user.role !== mode) {
        await logout();
        setError(mode === 'auditor'
          ? 'Esta cuenta pertenece a un asegurado. Cambiá a la pestaña Asegurado.'
          : 'Esta cuenta pertenece a un auditor. Cambiá a la pestaña Auditor.');
        return;
      }
      navigate(user.role === 'auditor' ? '/auditor/buscador' : '/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Credenciales inválidas');
    } finally { setLoading(false); }
  };

  return (
    <div className="auth-page">
      <div className="auth-logo-area">
        <CiasLogo size={72} />
        <h1 className="auth-brand">CIAS</h1>
        <p className="auth-tagline">Ciudadano Asegurado</p>
      </div>

      <div className="auth-card">
        <h2 className="auth-title">Iniciá sesión</h2>
        <p className="auth-subtitle">Ingresá con tu cuenta CIAS.</p>
        <div className="auth-tabs">
          <button className={mode === 'conductor' ? 'active' : ''} onClick={() => setMode('conductor')}>
            Asegurado
          </button>
          <button className={mode === 'auditor' ? 'active' : ''} onClick={() => setMode('auditor')}>
            Auditor
          </button>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label>Correo electrónico</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)}
              placeholder="tu@email.com" required autoFocus />
          </div>
          <div className="form-group">
            <label>Contraseña</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)}
              placeholder="••••••••" required />
          </div>
          {error && <p className="auth-error">{error}</p>}
          <button
            type="button"
            className="auth-forgot"
            onClick={() => setError('La recuperación de contraseña todavía no está disponible en el backend. Contactá a soporte CIAS.')}
          >
            ¿Olvidaste tu contraseña?
          </button>
          <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
            {loading ? 'Ingresando…' : 'Iniciar sesión'}
          </button>
        </form>

        <div className="auth-or"><span>o</span></div>
        <p className="auth-footer">
          ¿No tenés cuenta? <Link to="/registro">Registrate en CIAS</Link>
        </p>
        <div className="auth-legal">
          <p>© 2026 CIAS — Ciudadano Asegurado</p>
          <p>Prototipo académico con datos simulados</p>
        </div>
      </div>
    </div>
  );
}
