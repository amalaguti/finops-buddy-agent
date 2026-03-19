import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProfileProvider } from '../context/ProfileContext.jsx';
import { ProfileSelector } from './ProfileSelector.jsx';

// Mock getProfiles so ProfileProvider gets profiles without a real API
vi.mock('../api/client.js', () => ({
  getProfiles: vi.fn().mockResolvedValue(['profile-a', 'profile-b']),
}));

describe('ProfileSelector', () => {
  it('renders profile dropdown after profiles load', async () => {
    render(
      <ProfileProvider>
        <ProfileSelector />
      </ProfileProvider>
    );
    const select = await screen.findByRole('combobox');
    expect(select).toBeDefined();
    expect(select.value).toBe('profile-a');
    expect(screen.getByText('profile-a')).toBeDefined();
    expect(screen.getByText('profile-b')).toBeDefined();
  });
});
