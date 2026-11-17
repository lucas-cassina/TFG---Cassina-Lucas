import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import CiasLogo from './CiasLogo';

export default function AppHeader() {
  const { user } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="dashboard-header">
      <div className="dashboard-header-left">
        <CiasLogo size={40} className="dashboard-logo" />
        <div>
          <div className="dashboard-brand">CIAS</div>
          <div className="dashboard-subbrand">Ciudadano Asegurado</div>
        </div>
      </div>
      <div className="dashboard-header-actions">
        <button className="dashboard-bell-btn" aria-label="Notificaciones">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
        </button>
        <button className="dashboard-avatar" onClick={() => navigate('/perfil')} aria-label="Ir a mi perfil">
          {`${user?.nombre?.[0] || 'C'}${user?.apellido?.[0] || 'A'}`.toUpperCase()}
        </button>
      </div>
    </header>
  );
}
