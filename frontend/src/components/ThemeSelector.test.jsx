import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider } from '../context/ThemeContext.jsx';
import { ThemeSelector } from './ThemeSelector.jsx';

const mockLocalStorage = {
  getItem: vi.fn(() => null),
  setItem: vi.fn(),
  removeItem: vi.fn(),
};

describe('ThemeSelector', () => {
  beforeEach(() => {
    mockLocalStorage.getItem.mockReturnValue(null);
    mockLocalStorage.setItem.mockClear();
    Object.defineProperty(globalThis, 'localStorage', { value: mockLocalStorage, writable: true });
  });

  it('renders six themes when opened', () => {
    render(
      <ThemeProvider>
        <ThemeSelector />
      </ThemeProvider>
    );
    const button = screen.getByRole('button', { name: /select theme/i });
    fireEvent.click(button);
    const listbox = screen.getByRole('listbox', { name: /theme options/i });
    const options = screen.getAllByRole('option');
    expect(options).toHaveLength(6);
    expect(listbox).toBeDefined();
    expect(screen.getByText('Ocean')).toBeDefined();
    expect(screen.getByText('Forest')).toBeDefined();
    expect(screen.getByText('Sunset')).toBeDefined();
    expect(screen.getByText('Midnight')).toBeDefined();
    expect(screen.getByText('Neo-Matrix')).toBeDefined();
  });

  it('selection updates theme and closes dropdown', () => {
    render(
      <ThemeProvider>
        <ThemeSelector />
      </ThemeProvider>
    );
    fireEvent.click(screen.getByRole('button', { name: /select theme/i }));
    fireEvent.click(screen.getByText('Ocean'));
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith('finops_theme', 'ocean');
    expect(screen.queryByRole('listbox')).toBeNull();
  });
});
