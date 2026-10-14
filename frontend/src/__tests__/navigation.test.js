import { describe, it, expect } from 'vitest';
import { modules, entityRoutes } from '../modules';
describe('Mapa integrado de navegación', () => {
  it('tiene once módulos y cada vínculo abre el módulo que conserva el registro', () => {
    expect(modules).toHaveLength(11);
    expect(new Set(modules.map((m) => m.path)).size).toBe(11);
    expect(entityRoutes['task-documents']).toBe('/registro');
    expect(entityRoutes['evidence-links']).toBe('/evidencias');
    expect(entityRoutes.agreements).toBe('/reuniones');
  });
});
