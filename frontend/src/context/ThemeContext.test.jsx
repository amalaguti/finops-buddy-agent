import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { ThemeProvider, useTheme, VALID_THEMES, STORAGE_KEY } from './ThemeContext.jsx';

function Consumer() {
  const { theme, setTheme } = useTheme();
  return (
    <div>
      <span data-testid="current-theme">{theme}</span>
      <button type="button" onClick={() => setTheme('ocean')}>
        Set Ocean
      </button>
      <button type="button" onClick={() => setTheme('neo-matrix')}>
        Set Neo-Matrix
      </button>
    </div>
  );
}

describe('ThemeContext', () => {
  const mockLocalStorage = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
  };

  beforeEach(() => {
    mockLocalStorage.getItem.mockReturnValue(null);
    mockLocalStorage.setItem.mockClear();
    Object.defineProperty(globalThis, 'localStorage', { value: mockLocalStorage, writable: true });
  });

  it('exposes VALID_THEMES with six theme ids', () => {
    expect(VALID_THEMES).toHaveLength(6);
    expect(VALID_THEMES).toContain('slate');
    expect(VALID_THEMES).toContain('ocean');
    expect(VALID_THEMES).toContain('neo-matrix');
  });

  it('uses STORAGE_KEY finops_theme', () => {
    expect(STORAGE_KEY).toBe('finops_theme');
  });

  it('defaults to slate when localStorage has no valid theme', () => {
    mockLocalStorage.getItem.mockReturnValue(null);
    render(
      <ThemeProvider>
        <Consumer />
      </ThemeProvider>
    );
    expect(screen.getByTestId('current-theme').textContent).toBe('slate');
  });

  it('restores theme from localStorage when valid', () => {
    mockLocalStorage.getItem.mockReturnValue('ocean');
    render(
      <ThemeProvider>
        <Consumer />
      </ThemeProvider>
    );
    expect(screen.getByTestId('current-theme').textContent).toBe('ocean');
  });

  it('setTheme updates state and writes to localStorage', async () => {
    mockLocalStorage.getItem.mockReturnValue('slate');
    render(
      <ThemeProvider>
        <Consumer />
      </ThemeProvider>
    );
    expect(screen.getByTestId('current-theme').textContent).toBe('slate');
    await act(async () => {
      screen.getByText('Set Ocean').click();
    });
    expect(screen.getByTestId('current-theme').textContent).toBe('ocean');
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith(STORAGE_KEY, 'ocean');
  });
});
