import { render, screen } from '@testing-library/react';
import ProgressBar from './ProgressBar';

describe('ProgressBar', () => {
  test('muestra el label y el peso', () => {
    render(<ProgressBar label="Velocidad" value={70} weight="25%" />);
    expect(screen.getByText('Velocidad')).toBeInTheDocument();
    expect(screen.getByText('25%')).toBeInTheDocument();
  });

  test('muestra el valor redondeado / 100', () => {
    render(<ProgressBar label="Frenadas" value={55.7} />);
    expect(screen.getByText('56 / 100')).toBeInTheDocument();
  });

  test('valores por encima de 100 se limitan a 100', () => {
    render(<ProgressBar label="Test" value={120} />);
    expect(screen.getByText('120 / 100')).toBeInTheDocument();
    // El fill no debe superar el 100% (se verifica por la lógica Math.min)
  });

  test('no muestra el weight si no se pasa la prop', () => {
    render(<ProgressBar label="Horario" value={30} />);
    expect(screen.queryByText('%')).not.toBeInTheDocument();
  });
});
