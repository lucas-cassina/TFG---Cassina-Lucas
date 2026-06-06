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

// Redirigir al login en 401
client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('cias_token');
      localStorage.removeItem('cias_user');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

export default client;

/* ── Auth ── */
export const authAPI = {
  loginConductor:   (data) => client.post('/auth/login', data),
  registroConductor:(data) => client.post('/auth/registro/conductor', data),
  loginAuditor:     (data) => client.post('/auth/login', data),
  registroAuditor:  (data) => client.post('/auth/registro/auditor', data),
  logout:           ()     => client.post('/auth/logout'),
};

/* ── Índice ── */
export const indiceAPI = {
  actual:          () => client.get('/indice/actual'),
  estadisticasMes: () => client.get('/indice/estadisticas-mes'),
  historial:       (params) => client.get('/indice/historial', { params }),
};

/* ── Incentivos ── */
export const incentivosAPI = {
  miNivel:      () => client.get('/incentivos/mi-nivel'),
  disponibles:  () => client.get('/incentivos/disponibles'),
};

/* ── Auditor ── */
export const auditorAPI = {
  buscarAsegurado:  (data)       => client.post('/auditor/buscar-asegurado', data),
  perfilRiesgo:     (id)         => client.get(`/auditor/perfil-riesgo/${id}`),
  reportePDF:       (id)         => client.get(`/reportes/conductor/${id}/pdf`, { responseType: 'blob' }),
};

/* ── Telemetría ── */
export const telemetriaAPI = {
  alertas: () => client.get('/telemetria/alertas'),
};
