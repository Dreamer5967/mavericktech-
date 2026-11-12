import React, { useEffect, useState, useRef } from 'react';

interface PageTurnTransitionProps {
  children: (activePath: string) => React.ReactNode;
  currentPath: string;
}

export const PageTurnTransition: React.FC<PageTurnTransitionProps> = ({ children, currentPath }) => {
  const [displayPath, setDisplayPath] = useState(currentPath);
  const [transitioning, setTransitioning] = useState(false);
  const [direction, setDirection] = useState<'to-dashboard' | 'to-experience'>('to-dashboard');
  const [turnProgress, setTurnProgress] = useState(0); // 0 to 1
  const prevPathRef = useRef(currentPath);

  useEffect(() => {
    if (currentPath !== prevPathRef.current) {
      const isGoingToDashboard = currentPath.includes('dashboard') || currentPath === '/';
      setDirection(isGoingToDashboard ? 'to-dashboard' : 'to-experience');
      setTransitioning(true);
      setTurnProgress(0);

      // Check for prefers-reduced-motion
      const prefersReducedMotion =
        typeof window !== 'undefined' &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches;

      if (prefersReducedMotion) {
        setDisplayPath(currentPath);
        prevPathRef.current = currentPath;
        setTransitioning(false);
        return;
      }

      const startTime = performance.now();
      const duration = 750; // 750ms for ultra-smooth cinematic 3D page turn

      let switchedView = false;

      const animate = (currentTime: number) => {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        setTurnProgress(progress);

        // Switch the underlying content at the apex of the turn (around 45% progress)
        if (progress >= 0.45 && !switchedView) {
          setDisplayPath(currentPath);
          prevPathRef.current = currentPath;
          switchedView = true;
          window.scrollTo(0, 0);
        }

        if (progress < 1) {
          requestAnimationFrame(animate);
        } else {
          setTransitioning(false);
          setTurnProgress(0);
        }
      };

      const animId = requestAnimationFrame(animate);
      return () => cancelAnimationFrame(animId);
    }
  }, [currentPath]);

  // Cubic bezier easing for physical page turn feel
  // Accelerates as the page is lifted, swings smoothly over the spine, and settles softly
  const easeInOutCubic = (t: number) =>
    t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

  const eased = easeInOutCubic(turnProgress);

  // Rotation angles for 3D page turn
  // If to-dashboard (turning forward): page curls from right to left (0deg to -180deg)
  // If to-experience (turning backward): page curls from left to right (0deg to 180deg)
  const rotationAngle =
    direction === 'to-dashboard' ? -eased * 180 : eased * 180;

  // Dynamic shadow intensity peaking at midpoint
  const shadowOpacity = Math.sin(eased * Math.PI) * 0.85;

  return (
    <div className="relative w-full min-h-screen overflow-x-hidden bg-[#080D10]">
      {/* Underlying Active Content rendered with displayPath */}
      <div
        className="w-full transition-opacity duration-300"
        style={{
          opacity: transitioning && turnProgress < 0.45 ? 0.9 : 1,
        }}
      >
        {children(displayPath)}
      </div>

      {/* 3D Holographic Page Turn Overlay */}
      {transitioning && (
        <div
          className="fixed inset-0 pointer-events-none z-[9999] flex items-center justify-center overflow-hidden"
          style={{
            perspective: '2400px',
            perspectiveOrigin: direction === 'to-dashboard' ? '40% 50%' : '60% 50%',
            background: `radial-gradient(ellipse at center, rgba(8,13,16,${0.35 + shadowOpacity * 0.3}) 0%, rgba(8,13,16,0.85) 100%)`,
          }}
        >
          {/* Ambient Cyber Grid during turn */}
          <div
            className="absolute inset-0 opacity-20 pointer-events-none"
            style={{
              backgroundImage: `linear-gradient(to right, rgba(69,201,130,0.15) 1px, transparent 1px), linear-gradient(to bottom, rgba(69,201,130,0.15) 1px, transparent 1px)`,
              backgroundSize: '40px 40px',
              transform: `scale(${1 + eased * 0.08})`,
            }}
          />

          {/* Central 3D Turning Page Leaf */}
          <div
            className="relative w-full h-full max-w-[100vw] max-h-[100vh] preserve-3d"
            style={{
              transformStyle: 'preserve-3d',
              transformOrigin: direction === 'to-dashboard' ? '0% 50%' : '100% 50%',
              transform: `rotateY(${rotationAngle}deg) scale(${1 - Math.sin(eased * Math.PI) * 0.05})`,
              transition: 'none',
              boxShadow:
                direction === 'to-dashboard'
                  ? `${-20 * Math.sin(eased * Math.PI)}px 0 60px rgba(0,0,0,0.9)`
                  : `${20 * Math.sin(eased * Math.PI)}px 0 60px rgba(0,0,0,0.9)`,
            }}
          >
            {/* Front of the turning page (visible for 0 <= progress <= 0.5) */}
            <div
              className="absolute inset-0 bg-[#080D10] border-y border-[#45C982]/20 backface-hidden overflow-hidden flex flex-col justify-between p-12"
              style={{
                backfaceVisibility: 'hidden',
                background: 'linear-gradient(135deg, #0d161a 0%, #080D10 70%, #05080a 100%)',
              }}
            >
              {/* Dynamic Page Curving Shadow Gradient */}
              <div
                className="absolute inset-0 pointer-events-none"
                style={{
                  background:
                    direction === 'to-dashboard'
                      ? `linear-gradient(to right, rgba(0,0,0,${shadowOpacity}) 0%, transparent 40%, rgba(69,201,130,${shadowOpacity * 0.15}) 85%, rgba(0,0,0,${shadowOpacity * 0.8}) 100%)`
                      : `linear-gradient(to left, rgba(0,0,0,${shadowOpacity}) 0%, transparent 40%, rgba(69,201,130,${shadowOpacity * 0.15}) 85%, rgba(0,0,0,${shadowOpacity * 0.8}) 100%)`,
                }}
              />

              {/* Glowing Page Edge Spine / Laser Seam */}
              <div
                className={`absolute top-0 bottom-0 ${
                  direction === 'to-dashboard' ? 'right-0' : 'left-0'
                } w-[3px] bg-gradient-to-b from-[#45C982]/40 via-[#45C982] to-[#45C982]/40`}
                style={{
                  boxShadow:
                    direction === 'to-dashboard'
                      ? '-4px 0 24px #45C982, -1px 0 6px #ffffff'
                      : '4px 0 24px #45C982, 1px 0 6px #ffffff',
                }}
              />

              {/* Page Turning Telemetry Watermark */}
              <div className="flex items-center justify-between text-xs font-mono text-[#45C982]/70 tracking-wider">
                <span className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-[#45C982] animate-ping" />
                  AEGIS SUBSYSTEM TRANSITION · 3D PORTAL
                </span>
                <span>SEC: {direction === 'to-dashboard' ? '02 // CONSOLE' : '01 // EXPERIENCE'}</span>
              </div>

              <div className="flex flex-col items-center justify-center space-y-4 my-auto opacity-80">
                <div className="w-16 h-16 rounded-xl border border-[#45C982]/40 flex items-center justify-center bg-[#111A1D]/80 shadow-[0_0_30px_rgba(69,201,130,0.25)]">
                  <div className="w-8 h-8 rounded border border-[#45C982] rotate-45 flex items-center justify-center">
                    <div className="w-3 h-3 bg-[#45C982] rounded-full" />
                  </div>
                </div>
                <div className="font-space font-bold text-2xl text-white tracking-widest uppercase">
                  {direction === 'to-dashboard' ? 'Entering Operator Console' : 'Returning to Experience'}
                </div>
                <div className="font-mono text-xs text-white/50 tracking-wider">
                  OPENING PLATFORM VIEW
                </div>
              </div>

              <div className="flex items-center justify-between text-[11px] font-mono text-white/40">
                <span>AEGIS TRAFFIC PLATFORM</span>
                <span>{direction === 'to-dashboard' ? 'OPERATOR CONSOLE' : 'PLATFORM TOUR'}</span>
              </div>
            </div>

            {/* Back of the turning page (visible for 0.5 <= progress <= 1) */}
            <div
              className="absolute inset-0 bg-[#080D10] border-y border-[#45C982]/20 overflow-hidden flex flex-col justify-between p-12"
              style={{
                backfaceVisibility: 'hidden',
                transform: 'rotateY(180deg)',
                background: 'linear-gradient(225deg, #0d161a 0%, #080D10 70%, #05080a 100%)',
              }}
            >
              {/* Reverse Page Shadow */}
              <div
                className="absolute inset-0 pointer-events-none"
                style={{
                  background:
                    direction === 'to-dashboard'
                      ? `linear-gradient(to left, rgba(0,0,0,${shadowOpacity}) 0%, transparent 40%, rgba(69,201,130,${shadowOpacity * 0.2}) 85%, rgba(0,0,0,${shadowOpacity * 0.9}) 100%)`
                      : `linear-gradient(to right, rgba(0,0,0,${shadowOpacity}) 0%, transparent 40%, rgba(69,201,130,${shadowOpacity * 0.2}) 85%, rgba(0,0,0,${shadowOpacity * 0.9}) 100%)`,
                }}
              />

              {/* Glowing Laser Seam on back edge */}
              <div
                className={`absolute top-0 bottom-0 ${
                  direction === 'to-dashboard' ? 'left-0' : 'right-0'
                } w-[3px] bg-gradient-to-b from-[#45C982]/40 via-[#45C982] to-[#45C982]/40`}
                style={{
                  boxShadow:
                    direction === 'to-dashboard'
                      ? '4px 0 24px #45C982, 1px 0 6px #ffffff'
                      : '-4px 0 24px #45C982, -1px 0 6px #ffffff',
                }}
              />

              <div className="flex items-center justify-between text-xs font-mono text-[#45C982]/70 tracking-wider">
                <span>SYSTEM TARGET: {direction === 'to-dashboard' ? 'OPERATOR HUD' : 'CINEMATIC HUB'}</span>
                <span>STATE: READY</span>
              </div>

              <div className="flex flex-col items-center justify-center space-y-3 my-auto opacity-90">
                <div className="text-xs font-mono text-[#45C982] tracking-widest uppercase animate-pulse">
                  &bull; AEGIS PLATFORM &bull;
                </div>
                <div className="font-space font-bold text-xl text-white tracking-wider">
                  {direction === 'to-dashboard' ? 'AEGIS COMMAND VIEWPORT' : 'AEGIS MISSION BRIEFING'}
                </div>
              </div>

              <div className="flex items-center justify-between text-[11px] font-mono text-white/40">
                <span>LIVE DATA STATUS IS SHOWN IN THE CONSOLE</span>
                <span>CAMERA AND API STATUS</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
