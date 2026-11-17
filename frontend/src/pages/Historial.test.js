import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import Historial from './Historial';

jest.mock('../api/client', () => ({
  indiceAPI: {
    historial: jest.fn(),
  },
}));

const { indiceAPI } = require('../api/client');

const mockSesiones = [
  { sesion_id: 1, inicio: '2026-06-01T10:00:00Z', fin: '2026-06-01T10:30:00Z', indice: 55, nivel: 'Bajo', distancia_km: 42 },
  { sesion_id: 2, inicio: '2026-06-10T22:15:00Z', fin: '2026-06-10T23:00:00Z', indice: 80, nivel: 'Medio', distancia_km: 60 },
];

const mockUser = { nombre: 'Lucas', apellido: 'Cassina' };

const renderHistorial = () =>
  render(
    <MemoryRouter>
      <AuthContext.Provider value={{ user: mockUser }}>
        <Historial />
      </AuthContext.Provider>
    </MemoryRouter>
  );

describe('Historial', () => {
  test('consulta las páginas restantes y conserva todos los viajes', async () => {
    const primeraPagina = Array.from({length: 100}, (_, i) => ({...mockSesiones[0], sesion_id: i + 10}));
    indiceAPI.historial.mockResolvedValueOnce({data: primeraPagina}).mockResolvedValueOnce({data: [mockSesiones[1]]});
    renderHistorial();
    await waitFor(() => expect(screen.getByText('80.0')).toBeInTheDocument());
    expect(screen.getAllByText('55.0')).toHaveLength(100);
    expect(indiceAPI.historial.mock.calls[1][0]).toEqual(expect.objectContaining({offset: 100, limite: 100}));
  });
  beforeEach(() => {
    jest.clearAllMocks();
    indiceAPI.historial.mockResolvedValue({ data: mockSesiones });
  });

  test('muestra los chips de filtro de período', async () => {
    renderHistorial();
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Personalizado' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Esta semana' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Este mes' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Últimos 3 meses' })).toBeInTheDocument();
    });
  });

  test('muestra las sesiones cargadas desde la API', async () => {
    renderHistorial();
    await waitFor(() => {
      expect(screen.getByText('55.0')).toBeInTheDocument();
      expect(screen.getByText('80.0')).toBeInTheDocument();
    });
  });

  test('al hacer clic en filtro llama a la API con parámetro desde', async () => {
    renderHistorial();
    await waitFor(() => screen.getByRole('button', { name: 'Esta semana' }));
    fireEvent.click(screen.getByRole('button', { name: 'Esta semana' }));
    await waitFor(() => {
      expect(indiceAPI.historial).toHaveBeenCalledTimes(2);
      const lastCall = indiceAPI.historial.mock.calls[1][0];
      expect(lastCall).toHaveProperty('desde');
      const elapsed = Date.now() - new Date(lastCall.desde).getTime();
      expect(elapsed).toBeGreaterThanOrEqual(6.99 * 86400000);
      expect(elapsed).toBeLessThan(7.01 * 86400000);
    });
  });

  test('mensaje vacío cuando no hay sesiones', async () => {
    indiceAPI.historial.mockResolvedValue({ data: [] });
    renderHistorial();
    await waitFor(() =>
      expect(screen.getByText(/No hay sesiones en este período/i)).toBeInTheDocument()
    );
  });
  test('el rango personalizado envía ambas fechas a la API', async () => {
    renderHistorial();
    await waitFor(() => expect(indiceAPI.historial).toHaveBeenCalledTimes(1));
    fireEvent.click(screen.getByRole('button', { name: 'Personalizado' }));
    fireEvent.change(screen.getByLabelText('Desde'), { target: { value: '2026-06-01' } });
    fireEvent.change(screen.getByLabelText('Hasta'), { target: { value: '2026-06-10' } });
    fireEvent.click(screen.getByRole('button', { name: 'Aplicar fechas' }));
    await waitFor(() => expect(indiceAPI.historial).toHaveBeenCalledTimes(2));
    const params = indiceAPI.historial.mock.calls[1][0];
    expect(new Date(params.desde).getTime()).toBe(new Date('2026-06-01T00:00:00').getTime());
    expect(new Date(params.hasta).getTime()).toBe(new Date('2026-06-10T23:59:59.999').getTime());
  });

  test('un rango invertido informa el error sin consultar la API', async () => {
    renderHistorial();
    await waitFor(() => expect(indiceAPI.historial).toHaveBeenCalledTimes(1));
    fireEvent.click(screen.getByRole('button', { name: 'Personalizado' }));
    fireEvent.change(screen.getByLabelText('Desde'), { target: { value: '2026-06-10' } });
    fireEvent.change(screen.getByLabelText('Hasta'), { target: { value: '2026-06-01' } });
    fireEvent.click(screen.getByRole('button', { name: 'Aplicar fechas' }));
    expect(screen.getByText(/Elegí una fecha de inicio/)).toBeInTheDocument();
    expect(indiceAPI.historial).toHaveBeenCalledTimes(1);
  });

});
