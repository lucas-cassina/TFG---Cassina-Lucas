import { NavLink } from 'react-router-dom';
import './BottomNav.css';

const HomeIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 9.5L12 3l9 6.5V20a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9.5z"/>
    <path d="M9 21V12h6v9"/>
  </svg>
);

const HistorialIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="18" height="18" rx="2"/>
    <path d="M7 8h10M7 12h10M7 16h6"/>
  </svg>
);

const IncentivosIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="8" r="5"/>
    <path d="M8.21 13.89L7 23l5-3 5 3-1.21-9.12"/>
  </svg>
);

const PerfilIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="8" r="4"/>
    <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
  </svg>
);

const LINKS = [
  { to: '/dashboard',  label: 'Inicio',     Icon: HomeIcon },
  { to: '/historial',  label: 'Historial',  Icon: HistorialIcon },
  { to: '/incentivos', label: 'Incentivos', Icon: IncentivosIcon },
  { to: '/perfil',     label: 'Perfil',     Icon: PerfilIcon },
];

export default function BottomNav() {
  return (
    <nav className="bottom-nav">
      {LINKS.map(({ to, label, Icon }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) => `bottom-nav__item${isActive ? ' active' : ''}`}
        >
          <span className="bottom-nav__icon"><Icon /></span>
          <span className="bottom-nav__label">{label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
