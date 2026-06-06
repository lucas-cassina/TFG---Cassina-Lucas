import { NavLink } from 'react-router-dom';
import './BottomNav.css';

const LINKS = [
  { to: '/dashboard',  label: 'Inicio',     icon: '🏠' },
  { to: '/historial',  label: 'Historial',  icon: '📊' },
  { to: '/incentivos', label: 'Incentivos', icon: '🏆' },
  { to: '/perfil',     label: 'Perfil',     icon: '👤' },
];

export default function BottomNav() {
  return (
    <nav className="bottom-nav">
      {LINKS.map(({ to, label, icon }) => (
        <NavLink key={to} to={to} className={({ isActive }) => `bottom-nav__item${isActive ? ' active' : ''}`}>
          <span className="bottom-nav__icon">{icon}</span>
          <span className="bottom-nav__label">{label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
