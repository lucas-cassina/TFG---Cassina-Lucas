import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import Incentivos from './Incentivos';

jest.mock('../api/client', () => ({
  incentivosAPI: {
    miNivel: jest.fn(),
    disponibles: jest.fn(),
  },
  indiceAPI: {
    estadisticasMes: jest.fn(),
  },
}));

const { incentivosAPI, indiceAPI } = require('../api/client');
const mockUser = { nombre: 'Lucas', apellido: 'Cassina' };

const renderIncentivos = () =>
  render(
    <MemoryRouter>
      <AuthContext.Provider value={{ user: mockUser }}>
        <Incentivos />
      </AuthContext.Provider>
    </MemoryRouter>
  );

describe('Incentivos', () => {
  beforeEach(() => {
    incentivosAPI.miNivel.mockResolvedValue({
      data: { nivel_incentivo: 'Bronce', meses_consecutivos_bajo: 1, puntos_acumulados: 10 },
    });
    incentivosAPI.disponibles.mockResolvedValue({
      data: { nivel_actual: 'Bronce', incentivos: [] },
    });
    indiceAPI.estadisticasMes.mockResolvedValue({
      data: { total_sesiones: 3, indice_promedio: 55, nivel_predominante: 'Bajo' },
    });
  });

  test('muestra los tres niveles del programa', async () => {
    renderIncentivos();
    await waitFor(() => {
      expect(screen.getByRole('heading', { level: 3, name: /^Nivel Bronce$/i })).toBeInTheDocument();
      expect(screen.getByRole('heading', { level: 3, name: /^Nivel Plata$/i })).toBeInTheDocument();
      expect(screen.getByRole('heading', { level: 3, name: /^Nivel Oro$/i })).toBeInTheDocument();
    });
  });

  test('muestra los puntos acumulados del conductor', async () => {
    renderIncentivos();
    await waitFor(() => expect(screen.getByText('10')).toBeInTheDocument());
  });

  test('muestra el progreso hacia el nivel Plata cuando está en Bronce', async () => {
    renderIncentivos();
    await waitFor(() =>
      expect(screen.getByText(/Progreso hacia Nivel Plata/i)).toBeInTheDocument()
    );
  });

  test('muestra error cuando la API falla', async () => {
    incentivosAPI.miNivel.mockRejectedValue(new Error('Network Error'));
    incentivosAPI.disponibles.mockRejectedValue(new Error('Network Error'));
    indiceAPI.estadisticasMes.mockRejectedValue(new Error('Network Error'));
    renderIncentivos();
    await waitFor(() =>
      expect(screen.getByText(/No pudimos cargar tus incentivos/i)).toBeInTheDocument()
    );
  });
});
