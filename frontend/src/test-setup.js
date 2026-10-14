import { vi } from 'vitest';
if (!window.matchMedia)
  window.matchMedia = vi.fn((query) => ({
    matches: false,
    media: query,
    addListener() {},
    removeListener() {},
    addEventListener() {},
    removeEventListener() {},
    dispatchEvent() {},
  }));
if (!window.ResizeObserver)
  window.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
Element.prototype.scrollIntoView = vi.fn();
window.scrollTo = vi.fn();
