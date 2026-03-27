import { useEffect, useState } from 'react';

export const CAROUSEL_INTERVAL_OPTIONS_SEC = [5, 10, 15, 30];

/** @returns {boolean} */
export function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return undefined;
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    const apply = () => setReduced(Boolean(mq.matches));
    apply();
    mq.addEventListener('change', apply);
    return () => mq.removeEventListener('change', apply);
  }, []);
  return reduced;
}

/**
 * Full-width carousel for costs dashboard slides (CSS 3D-style stack).
 * @param {{
 *   slides: Array<{ key: string, node: import('react').ReactNode }>,
 *   activeIndex: number,
 *   onPrev: () => void,
 *   onNext: () => void,
 *   intervalSec: number,
 *   onIntervalChange: (sec: number) => void,
 *   paused: boolean,
 *   onPauseToggle: () => void,
 *   prefersReducedMotion: boolean,
 * }} props
 */
export function CostsDashboardCarousel({
  slides,
  activeIndex,
  onPrev,
  onNext,
  intervalSec,
  onIntervalChange,
  paused,
  onPauseToggle,
  prefersReducedMotion,
}) {
  const count = slides.length;
  const safeIndex = count > 0 ? Math.min(activeIndex, count - 1) : 0;
  const transitionClass = prefersReducedMotion ? '' : 'transition-opacity duration-300 ease-out';

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={onPrev}
          disabled={count <= 1}
          className="rounded-lg border border-finops-border bg-finops-btn-secondary px-3 py-1.5 text-xs font-semibold text-finops-text-primary shadow-sm hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Previous slide"
        >
          Prev
        </button>
        <button
          type="button"
          onClick={onPauseToggle}
          className="rounded-lg border border-finops-border bg-finops-btn-secondary px-3 py-1.5 text-xs font-semibold text-finops-text-primary shadow-sm hover:opacity-90"
          aria-pressed={paused}
          aria-label={paused ? 'Resume auto-advance' : 'Pause auto-advance'}
        >
          {paused ? 'Resume' : 'Pause'}
        </button>
        <button
          type="button"
          onClick={onNext}
          disabled={count <= 1}
          className="rounded-lg border border-finops-border bg-finops-btn-secondary px-3 py-1.5 text-xs font-semibold text-finops-text-primary shadow-sm hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Next slide"
        >
          Next
        </button>
        <label className="flex items-center gap-1.5 text-xs font-semibold text-finops-text-secondary">
          <span className="whitespace-nowrap">Interval</span>
          <select
            value={intervalSec}
            onChange={(e) => onIntervalChange(Number(e.target.value))}
            className="rounded-lg border-2 border-finops-border bg-finops-bg-page px-2 py-1.5 text-xs font-bold text-finops-text-primary shadow-sm"
            aria-label="Carousel advance interval in seconds"
          >
            {CAROUSEL_INTERVAL_OPTIONS_SEC.map((sec) => (
              <option key={sec} value={sec}>
                {sec}s
              </option>
            ))}
          </select>
        </label>
        <span
          className="text-xs font-bold tabular-nums text-finops-text-primary"
          aria-live="polite"
        >
          Slide {count > 0 ? safeIndex + 1 : 0} / {count}
        </span>
        {prefersReducedMotion ? (
          <span className="text-[11px] text-finops-text-secondary">Reduced motion: no auto-advance</span>
        ) : null}
      </div>

      <div
        className="relative min-h-[16rem]"
        role="region"
        aria-roledescription="carousel"
        aria-label="Costs dashboard carousel"
      >
        <div className="relative min-h-[14rem] isolate">
          {slides.map((slide, i) => {
            const isActive = i === safeIndex;
            // Only the active slide is visible: inactive slides stay fully hidden so nothing
            // bleeds through the foreground card (opaque panel below).
            const style = isActive
              ? { opacity: 1, visibility: 'visible', zIndex: 20 }
              : { opacity: 0, visibility: 'hidden', zIndex: 0 };
            return (
              <div
                key={slide.key}
                className={`absolute inset-x-0 top-0 ${transitionClass} ${
                  !isActive ? 'pointer-events-none' : ''
                }`}
                style={style}
                aria-hidden={!isActive}
              >
                <div
                  className={`mx-auto max-w-4xl rounded-2xl border-2 border-finops-border bg-finops-bg-surface p-5 shadow-2xl shadow-black/20 ring-2 ring-finops-accent/25 ring-offset-2 ring-offset-finops-bg-page dark:border-finops-border dark:shadow-black/50 dark:ring-offset-finops-bg-surface ${
                    isActive
                      ? 'border-finops-accent/40 ring-finops-accent/50'
                      : ''
                  }`}
                >
                  {slide.node}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
