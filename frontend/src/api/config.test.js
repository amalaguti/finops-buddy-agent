import { describe, it, expect } from 'vitest';
import { API_BASE } from './config.js';

describe('API config', () => {
  it('exports API_BASE as a non-empty URL string', () => {
    expect(typeof API_BASE).toBe('string');
    expect(API_BASE).toMatch(/^https?:\/\//);
    expect(API_BASE.length).toBeGreaterThan(0);
  });
});
