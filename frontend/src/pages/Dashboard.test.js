import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import Dashboard from './Dashboard';

// Mock del módulo de API
jest.mock('../api/client', () => ({
  indiceAPI: {
    actual: jest.fn(),
    estadisticasMes: jest.fn(),
  },
  telemetriaAPI: {
    alertas: jest.fn(),
  },
}));

const { indiceAPI, telemetriaAPI } = require('../api/client');

jest.mock('../hooks/useSesionStream', () => ({
  useSesionStream: () => ({ sesionActiva: false, sesionInfo: null, alertasLive: [] }),
}));

const mockUser = { nombre: 'Lucas', apellido: 'Cassina' };

const renderDashboard = () =>
  render(
    <MemoryRouter>
      <AuthContext.Provider value={{ user: mockUser }}>
        <Dashboard />
      </AuthContext.Provider>
    </MemoryRouter>
  );

describe('Dashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    indiceAPI.actual.mockResolvedValue({ data: { indice: 62, nivel: 'Bajo', puntaje_velocidad: 40, puntaje_frenadas: 30, puntaje_aceleraciones: 25, puntaje_horario: 10, puntaje_distancia: 20 } });
    indiceAPI.estadisticasMes.mockResolvedValue({ data: { total_sesiones: 5, total_km: 320, alertas_totales: 2, nivel_predominante: 'Bajo' } });
    telemetriaAPI.alertas.mockResolvedValue({ data: [] });
  });

  test('muestra saludo con el nombre del conductor', async () => {
    renderDashboard();
    await waitFor(() => expect(screen.getByText(/Lucas/)).toBeInTheDocument());
  });

  test('muestra el índice de riesgo cuando la API responde', async () => {
    renderDashboard();
    await waitFor(() => expect(screen.getByText('62.0')).toBeInTheDocument());
  });

  test('muestra estadísticas del mes: sesiones y km', async () => {
    renderDashboard();
    await waitFor(() => {
      expect(screen.getByText(/5 sesiones/i)).toBeInTheDocument();
    });
  });

  test('muestra mensaje sin alertas cuando la lista está vacía', async () => {
    renderDashboard();
    await waitFor(() =>
      expect(screen.getByText(/Sin alertas recientes/i)).toBeInTheDocument()
    );
  });

  test('muestra sección de desglose de variables', async () => {
    renderDashboard();
    await waitFor(() => {
      expect(screen.getByText(/¿Qué compone tu índice?/i)).toBeInTheDocument();
      expect(screen.getByText('Velocidad')).toBeInTheDocument();
      expect(screen.getByText('Frenadas bruscas')).toBeInTheDocument();
    });
  });

  test('muestra error cuando la API falla', async () => {
    indiceAPI.actual.mockRejectedValue(new Error('Network Error'));
    indiceAPI.estadisticasMes.mockRejectedValue(new Error('Network Error'));
    telemetriaAPI.alertas.mockRejectedValue(new Error('Network Error'));
    renderDashboard();
    await waitFor(() =>
      expect(screen.getByText(/No pudimos cargar/i)).toBeInTheDocument()
    );
  });
});
