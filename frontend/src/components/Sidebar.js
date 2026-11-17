import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Sidebar.css';

const SearchIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>
  </svg>
);
const LogoutIcon = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
    <polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
  </svg>
);

const LINKS = [
  { to:'/auditor/buscador', label:'Buscador', Icon:SearchIcon },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <span className="sidebar__logo">C</span>
        <div className="sidebar__brand-text">
          <span className="sidebar__brand-name">CIAS</span>
          <span className="sidebar__brand-sub">Panel Auditor</span>
        </div>
      </div>

      <nav className="sidebar__nav">
        {LINKS.map(({ to, label, Icon }) => (
          <NavLink key={to} to={to}
            className={({ isActive }) => `sidebar__link${isActive?' active':''}`}>
            <span className="sidebar__link-icon"><Icon /></span>
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar__footer">
        <p className="sidebar__user-name">{user?.nombre} {user?.apellido}</p>
        <button className="sidebar__logout" onClick={logout}>
          <LogoutIcon /> Cerrar sesión
        </button>
      </div>
    </aside>
  );
}
