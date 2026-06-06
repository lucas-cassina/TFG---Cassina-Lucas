import { useAuth } from '../context/AuthContext';
import Card from '../components/Card';
import BottomNav from '../components/BottomNav';
import './Perfil.css';

export default function Perfil() {
  const { user, logout } = useAuth();

  return (
    <div className="perfil">
      <header className="perfil__header">
        <h1>Mi Perfil</h1>
      </header>
      <main className="perfil__main">
        <Card className="perfil__avatar-card">
          <div className="perfil__avatar">
            {user?.nombre?.[0]}{user?.apellido?.[0]}
          </div>
          <div className="perfil__nombre">{user?.nombre} {user?.apellido}</div>
          <div className="perfil__rol">Asegurado</div>
        </Card>

        <Card>
          <h2 className="section-title">Datos de cuenta</h2>
          <div className="perfil__datos">
            <div className="dato-row">
              <span className="dato-label">Email</span>
              <span className="dato-val">{user?.email || '—'}</span>
            </div>
            <div className="dato-row">
              <span className="dato-label">ID de usuario</span>
              <span className="dato-val">#{user?.user_id}</span>
            </div>
            <div className="dato-row">
              <span className="dato-label">Rol</span>
              <span className="dato-val">{user?.role}</span>
            </div>
          </div>
        </Card>

        <button className="btn-danger" onClick={logout}>Cerrar sesión</button>
      </main>
      <BottomNav />
    </div>
  );
}
