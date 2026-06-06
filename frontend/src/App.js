import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Registro from './pages/Registro';
import Dashboard from './pages/Dashboard';
import Historial from './pages/Historial';
import Incentivos from './pages/Incentivos';
import Perfil from './pages/Perfil';
import Buscador from './pages/auditor/Buscador';
import PerfilRiesgo from './pages/auditor/PerfilRiesgo';

function RequireAuth({ children, role }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (role && user.role !== role) return <Navigate to="/login" replace />;
  return children;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/registro" element={<Registro />} />

      {/* Conductor */}
      <Route path="/dashboard"  element={<RequireAuth role="conductor"><Dashboard /></RequireAuth>} />
      <Route path="/historial"  element={<RequireAuth role="conductor"><Historial /></RequireAuth>} />
      <Route path="/incentivos" element={<RequireAuth role="conductor"><Incentivos /></RequireAuth>} />
      <Route path="/perfil"     element={<RequireAuth role="conductor"><Perfil /></RequireAuth>} />

      {/* Auditor */}
      <Route path="/auditor/buscador"    element={<RequireAuth role="auditor"><Buscador /></RequireAuth>} />
      <Route path="/auditor/perfil/:id"  element={<RequireAuth role="auditor"><PerfilRiesgo /></RequireAuth>} />

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}
