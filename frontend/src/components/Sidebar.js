import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Sidebar.css';

const LINKS = [
  { to: '/auditor/buscador',  label: 'Buscador',     icon: '🔍' },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <span className="sidebar__logo">CIAS</span>
        <span className="sidebar__subtitle">Auditor</span>
      </div>
      <div className="sidebar__user">
        <span>{user?.nombre} {user?.apellido}</span>
      </div>
      <nav className="sidebar__nav">
        {LINKS.map(({ to, label, icon }) => (
          <NavLink key={to} to={to}
            className={({ isActive }) => `sidebar__link${isActive ? ' active' : ''}`}>
            <span>{icon}</span> {label}
          </NavLink>
        ))}
      </nav>
      <button className="sidebar__logout" onClick={logout}>Cerrar sesión</button>
    </aside>
  );
}
