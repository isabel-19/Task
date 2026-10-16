import { describe, expect, it } from 'vitest';
import { matchesSearch } from '../components/SearchSelect.vue';

describe('selección con búsqueda', () => {
  it('encuentra nombres sin distinguir mayúsculas ni tildes', () => {
    expect(matchesSearch({ label: 'Lucía · demo', value: 1 }, 'lucia')).toBe(true);
    expect(matchesSearch({ label: 'Lucía · demo', value: 1 }, 'LUCÍA')).toBe(true);
    expect(matchesSearch({ label: 'Elena · demo', value: 2 }, 'lucia')).toBe(false);
  });

  it('busca dentro de cualquier parte de la etiqueta y acepta textos sueltos', () => {
    expect(matchesSearch({ label: 'Unidad de Calidad', value: 3 }, 'calid')).toBe(true);
    expect(matchesSearch('Hoja 2', 'hoja')).toBe(true);
    expect(matchesSearch('Hoja 2', 'metas')).toBe(false);
  });

  it('usa la etiqueta indicada cuando la opción no se llama label', () => {
    expect(matchesSearch({ name: 'Mateo', value: 4 }, 'mat', 'name')).toBe(true);
    expect(matchesSearch({ name: 'Mateo', value: 4 }, 'mat')).toBe(false);
  });

  it('no rompe con valores vacíos', () => {
    expect(matchesSearch({ label: null, value: 5 }, 'x')).toBe(false);
    expect(matchesSearch({ label: 'Algo', value: 5 }, '')).toBe(true);
  });
});
