import { describe, expect, it } from 'vitest';
import { formatApiError } from '../format';

describe('Validación legible de acciones e importaciones', () => {
  it('traduce errores de lotes anteriores sin mostrar rutas internas', () => {
    const message = formatApiError([
      {
        loc: ['body', 'evidence', 'title'],
        type: 'missing',
        msg: 'Field required',
        input: {},
      },
      { loc: ['year'], type: 'missing', msg: 'Field required' },
    ]);
    expect(message).toBe(
      'Nombre de la evidencia: Este campo es obligatorio.\nAño: Este campo es obligatorio.',
    );
    expect(message).not.toContain('body.');
  });
  it('conserva los mensajes de negocio y las etiquetas del servidor', () => {
    expect(
      formatApiError([
        {
          loc: ['body', 'note'],
          label: 'Observación',
          msg: 'Ingresa al menos 3 caracteres.',
        },
      ]),
    ).toBe('Observación: Ingresa al menos 3 caracteres.');
    expect(formatApiError('La tarea ya está cerrada.')).toBe('La tarea ya está cerrada.');
  });
});
