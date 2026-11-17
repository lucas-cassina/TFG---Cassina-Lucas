import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { authAPI } from '../api/client';

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('cias_user')); } catch { return null; }
  });

  const login = useCallback(async (email, password) => {
    const resp = await authAPI.login({ email, password });
    const userData = resp.data;
    localStorage.setItem('cias_token', userData.access_token);
    localStorage.setItem('cias_user', JSON.stringify(userData));
    setUser(userData);
    return userData;
  }, []);

  const register = useCallback(async (formData) => {
    const resp = await authAPI.registroConductor(formData);
    const userData = resp.data;
    localStorage.setItem('cias_token', userData.access_token);
    localStorage.setItem('cias_user', JSON.stringify(userData));
    setUser(userData);
    return userData;
  }, []);

  const logout = useCallback(async () => {
    try { await authAPI.logout(); } catch {}
    localStorage.removeItem('cias_token');
    localStorage.removeItem('cias_user');
    setUser(null);
  }, []);

  // B5: el interceptor de axios despacha 'cias:unauthorized' en vez de hacer
  // window.location.href (que rompe React Router). Acá lo capturamos y ponemos
  // user en null — RequireAuth redirige a /login sin full page reload.
  useEffect(() => {
    const handleUnauthorized = () => {
      setUser(null);
    };
    window.addEventListener('cias:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('cias:unauthorized', handleUnauthorized);
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, register, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth debe usarse dentro de AuthProvider');
  return ctx;
}
