/**
 * Tests del módulo api/client.js (HU-001 a HU-012)
 * Verifica que cada función del cliente llama al endpoint correcto.
 */

jest.mock('axios', () => {
  const mockClient = {
    post: jest.fn(),
    get: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
  };
  return { __esModule: true, default: { create: jest.fn(() => mockClient) } };
});

// Re-importar después del mock
const axios = require('axios').default;
const mockClient = axios.create();
require('./client');

// Limpiar mock antes de importar el módulo real
beforeEach(() => {
  jest.clearAllMocks();
  mockClient.post.mockResolvedValue({ data: {} });
  mockClient.get.mockResolvedValue({ data: {} });
});

describe('authAPI', () => {
  test('login usa POST /auth/login', () => {
    const { authAPI } = require('./client');
    authAPI.login({ email: 'a@b.com', password: '123' });
    expect(mockClient.post).toHaveBeenCalledWith('/auth/login', expect.any(Object));
  });

  test('registroConductor usa POST /auth/registro/conductor', () => {
    const { authAPI } = require('./client');
    authAPI.registroConductor({ nombre: 'Lucas' });
    expect(mockClient.post).toHaveBeenCalledWith('/auth/registro/conductor', expect.any(Object));
  });

  test('logout usa POST /auth/logout', () => {
    const { authAPI } = require('./client');
    authAPI.logout();
    expect(mockClient.post).toHaveBeenCalledWith('/auth/logout');
  });
});

describe('indiceAPI', () => {
  test('actual usa GET /indice/actual', () => {
    const { indiceAPI } = require('./client');
    indiceAPI.actual();
    expect(mockClient.get).toHaveBeenCalledWith('/indice/actual');
  });

  test('historial acepta parámetros de filtro', () => {
    const { indiceAPI } = require('./client');
    const params = { desde: '2026-06-01T00:00:00Z' };
    indiceAPI.historial(params);
    expect(mockClient.get).toHaveBeenCalledWith('/indice/historial', { params });
  });
});

describe('auditorAPI', () => {
  test('buscarAsegurado usa POST /auditor/buscar-asegurado', () => {
    const { auditorAPI } = require('./client');
    auditorAPI.buscarAsegurado({ dni: '30123456' });
    expect(mockClient.post).toHaveBeenCalledWith('/auditor/buscar-asegurado', expect.any(Object));
  });

  test('perfilRiesgo usa GET /auditor/perfil-riesgo/:id', () => {
    const { auditorAPI } = require('./client');
    auditorAPI.perfilRiesgo(42);
    expect(mockClient.get).toHaveBeenCalledWith('/auditor/perfil-riesgo/42');
  });
});

describe('telemetriaAPI', () => {
  test('abrirSesion usa POST /telemetria/sesion/abrir', () => {
    const { telemetriaAPI } = require('./client');
    telemetriaAPI.abrirSesion();
    expect(mockClient.post).toHaveBeenCalledWith('/telemetria/sesion/abrir', {});
  });

  test('alertas usa GET /telemetria/alertas', () => {
    const { telemetriaAPI } = require('./client');
    telemetriaAPI.alertas();
    expect(mockClient.get).toHaveBeenCalledWith('/telemetria/alertas');
  });
});
