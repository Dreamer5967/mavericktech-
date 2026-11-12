import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

// Register ScrollTrigger once globally in browser environments
if (typeof window !== 'undefined' && gsap && ScrollTrigger) {
  try {
    gsap.registerPlugin(ScrollTrigger);
  } catch (err) {
    console.warn('[useCinematicScroll] ScrollTrigger registration:', err);
  }
}

export interface CinematicScrollOptions {
  scopeRef?: React.RefObject<HTMLElement>;
  enabled?: boolean;
}

/**
 * Reusable GSAP + ScrollTrigger animation foundation for the AEGIS Experience.
 *
 * Guarantees:
 * 1. Strict React lifecycle cleanup via gsap.context().revert()
 * 2. Complete prevention of duplicate ScrollTrigger instances
 * 3. Native browser scrolling preservation (zero hijacked scroll / zero virtual scroll)
 * 4. Respects reduced-motion user preferences
 * 5. Handles window resizes smoothly with ScrollTrigger.refresh()
 * 6. Resilient exception handling — animation failures never crash the React render tree
 */
export function useCinematicScroll(
  animationSetup: (ctx: gsap.Context, prefersReducedMotion: boolean) => void,
  dependencies: React.DependencyList = []
) {
  const scopeRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    let ctx: gsap.Context | null = null;
    let resizeTimer: number | undefined;

    try {
      const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

      // Create a scoped GSAP context bounded to this DOM subtree
      ctx = gsap.context(() => {
        try {
          animationSetup(ctx!, prefersReducedMotion);
        } catch (animErr) {
          console.warn('[useCinematicScroll] Animation setup error caught gracefully:', animErr);
        }
      }, scopeRef.current || scopeRef);

      // Debounced refresh on window resize for responsive layout changes
      const handleResize = () => {
        window.clearTimeout(resizeTimer);
        resizeTimer = window.setTimeout(() => {
          try {
            ScrollTrigger.refresh();
          } catch {
            // graceful ignore
          }
        }, 200);
      };

      window.addEventListener('resize', handleResize);

      return () => {
        window.removeEventListener('resize', handleResize);
        if (resizeTimer) window.clearTimeout(resizeTimer);
        if (ctx) ctx.revert();
      };
    } catch (err) {
      console.warn('[useCinematicScroll] Lifecycle error caught:', err);
      return () => {
        if (ctx) ctx.revert();
      };
    }
  }, dependencies);

  return scopeRef;
}
