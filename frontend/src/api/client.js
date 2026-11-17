import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Inyectar token en cada request
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('cias_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// En 401: limpiar credenciales y notificar via evento custom (B5).
// AuthContext escucha 'cias:unauthorized' y llama setUser(null),
// lo que hace que RequireAuth redirija a /login sin full page reload.
client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('cias_token');
      localStorage.removeItem('cias_user');
      window.dispatchEvent(new CustomEvent('cias:unauthorized'));
    }
    return Promise.reject(err);
  }
);

export default client;

/* ── Auth ── */
export const authAPI = {
  login:             (data) => client.post('/auth/login', data),
  registroConductor: (data) => client.post('/auth/registro/conductor', data),
  registroAuditor:   (data) => client.post('/auth/registro/auditor', data),
  logout:            ()     => client.post('/auth/logout'),
};

/* ── Índice ── */
export const indiceAPI = {
  actual:          () => client.get('/indice/actual'),
  estadisticasMes: () => client.get('/indice/estadisticas-mes'),
  historial:       (params) => client.get('/indice/historial', { params }),
  detalleSesion:   (id) => client.get(`/indice/historial/${id}`),
};

/* ── Conductor ── */
export const conductorAPI = {
  perfil:          () => client.get('/conductor/perfil'),
  polizaPDF:       () => client.get('/conductor/poliza/pdf', { responseType: 'blob' }),
  estadisticasPDF: () => client.get('/conductor/estadisticas/pdf', { responseType: 'blob' }),
  cargarPoliza:    (data) => client.post('/conductor/poliza', data),
};

/* ── Incentivos ── */
export const incentivosAPI = {
  miNivel:     () => client.get('/incentivos/mi-nivel'),
  disponibles: () => client.get('/incentivos/disponibles'),
};

/* ── Auditor ── */
export const auditorAPI = {
  buscarAsegurado: (data) => client.post('/auditor/buscar-asegurado', data),
  perfilRiesgo:    (id)   => client.get(`/auditor/perfil-riesgo/${id}`),
  reportePDF:      (id)   => client.get(`/reportes/conductor/${id}/pdf`, { responseType: 'blob' }),
};

/* ── Telemetría ── */
export const telemetriaAPI = {
  obtenerSseToken: ()     => client.post('/telemetria/sse-token'),
  abrirSesion:     (data = {}) => client.post('/telemetria/sesion/abrir', data),
  enviarEventos:   (data) => client.post('/telemetria/eventos', data),
  cerrarSesion:    (data) => client.post('/telemetria/sesion/cerrar', data),
  alertas:         ()     => client.get('/telemetria/alertas'),
  sesionActiva:    ()     => client.get('/telemetria/sesion/activa'),
};
