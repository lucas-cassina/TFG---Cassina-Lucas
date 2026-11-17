import { render, screen } from '@testing-library/react';
import Badge from './Badge';

describe('Badge', () => {
  test('renderiza el label recibido como prop', () => {
    render(<Badge label="Bronce" />);
    expect(screen.getByText('Bronce')).toBeInTheDocument();
  });

  test('renderiza con distintos niveles', () => {
    const { rerender } = render(<Badge label="Bajo" />);
    expect(screen.getByText('Bajo')).toBeInTheDocument();

    rerender(<Badge label="Alto" />);
    expect(screen.getByText('Alto')).toBeInTheDocument();
  });

  test('no rompe con label vacío', () => {
    render(<Badge label="" />);
    // No debe lanzar error
  });
});
