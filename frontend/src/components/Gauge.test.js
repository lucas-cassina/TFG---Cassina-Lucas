import { render, screen } from '@testing-library/react';
import Gauge from './Gauge';

describe('Gauge', () => {
  test('sin datos no se presenta como riesgo bajo', () => {
    render(<Gauge value={0} nivel="Sin datos" />);
    expect(screen.getByText('SIN DATOS')).toBeInTheDocument();
    expect(screen.queryByText('RIESGO BAJO')).not.toBeInTheDocument();
  });
  test('muestra el valor numérico del índice', () => {
    render(<Gauge value={65} nivel="Bajo" />);
    expect(screen.getByText('65.0')).toBeInTheDocument();
  });

  test('muestra el nivel recibido', () => {
    render(<Gauge value={80} nivel="Medio" />);
    expect(screen.getByText(/RIESGO MEDIO/i)).toBeInTheDocument();
  });

  test('aria-label contiene el valor para accesibilidad', () => {
    render(<Gauge value={42} nivel="Bajo" />);
    expect(screen.getByLabelText(/Índice de riesgo 42/i)).toBeInTheDocument();
  });

  test('valor 0 por defecto no rompe el render', () => {
    render(<Gauge />);
    expect(screen.getByText('0.0')).toBeInTheDocument();
  });

  test('nivel Alto muestra texto de riesgo alto', () => {
    render(<Gauge value={90} nivel="Alto" />);
    expect(screen.getByText(/Riesgo Alto/i)).toBeInTheDocument();
  });
});
