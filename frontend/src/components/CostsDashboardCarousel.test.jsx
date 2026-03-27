import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { CostsDashboardCarousel, usePrefersReducedMotion } from './CostsDashboardCarousel.jsx';

describe('CostsDashboardCarousel', () => {
  it('renders carousel region, slide counter, and controls', () => {
    render(
      <CostsDashboardCarousel
        slides={[
          { key: 'a', node: <div>Slide A</div> },
          { key: 'b', node: <div>Slide B</div> },
        ]}
        activeIndex={0}
        onPrev={() => {}}
        onNext={() => {}}
        intervalSec={15}
        onIntervalChange={() => {}}
        paused={false}
        onPauseToggle={() => {}}
        prefersReducedMotion={false}
      />
    );
    expect(screen.getByRole('region', { name: /costs dashboard carousel/i })).toBeDefined();
    expect(screen.getByText(/Slide 1 \/ 2/)).toBeDefined();
    expect(screen.getByRole('button', { name: /previous slide/i })).toBeDefined();
    expect(screen.getByRole('button', { name: /next slide/i })).toBeDefined();
    expect(screen.getByRole('combobox', { name: /advance interval/i })).toBeDefined();
  });

  it('shows reduced motion notice when prefersReducedMotion is true', () => {
    render(
      <CostsDashboardCarousel
        slides={[{ key: 'a', node: <div>Slide A</div> }]}
        activeIndex={0}
        onPrev={() => {}}
        onNext={() => {}}
        intervalSec={15}
        onIntervalChange={() => {}}
        paused={false}
        onPauseToggle={() => {}}
        prefersReducedMotion
      />
    );
    expect(screen.getByText(/Reduced motion: no auto-advance/)).toBeDefined();
  });
});

describe('usePrefersReducedMotion', () => {
  const originalMatchMedia = window.matchMedia;

  beforeEach(() => {
    window.matchMedia = vi.fn().mockImplementation((query) => ({
      matches: query === '(prefers-reduced-motion: reduce)',
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }));
  });

  afterEach(() => {
    window.matchMedia = originalMatchMedia;
  });

  it('returns true when the media query matches', async () => {
    function Probe() {
      const reduced = usePrefersReducedMotion();
      return <span data-testid="reduced">{reduced ? 'yes' : 'no'}</span>;
    }
    render(<Probe />);
    await waitFor(() => {
      expect(screen.getByTestId('reduced').textContent).toBe('yes');
    });
  });
});
