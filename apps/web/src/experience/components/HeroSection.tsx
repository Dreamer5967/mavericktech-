import React from 'react';
import gsap from 'gsap';
import { ArrowRight } from 'lucide-react';
import { useNavigation } from '../../routes/Router';
import { useAegisSnapshot } from '../../hooks/useAegisSnapshot';
import { useCinematicScroll } from '../hooks/useCinematicScroll';
import { UrbanIntersectionVisual } from './UrbanIntersectionVisual';
import { ScrollIndicator } from './ScrollIndicator';

export const HeroSection: React.FC = () => {
  const { navigate } = useNavigation();
  const { data: snapshot, connectionStatus } = useAegisSnapshot();
  const isConnected = connectionStatus === 'CONNECTED';

  const heroContainerRef = useCinematicScroll((_, prefersReducedMotion) => {
    if (prefersReducedMotion) return;

    // Timeline for initial hero entrance
    const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });

    tl.from('.hero-badge', {
      opacity: 0,
      y: -15,
      duration: 0.7,
    })
      .from(
        '.hero-headline-line',
        {
          opacity: 0,
          y: 45,
          duration: 0.9,
          stagger: 0.15,
        },
        '-=0.4'
      )
      .from(
        '.hero-description',
        {
          opacity: 0,
          y: 25,
          duration: 0.8,
        },
        '-=0.5'
      )
      .from(
        '.hero-telemetry-item',
        {
          opacity: 0,
          y: 20,
          duration: 0.6,
          stagger: 0.1,
        },
        '-=0.4'
      )
      .from(
        '.hero-cta',
        {
          opacity: 0,
          y: 20,
          duration: 0.6,
        },
        '-=0.3'
      )
      .from(
        '.hero-scroll-indicator',
        {
          opacity: 0,
          duration: 0.8,
        },
        '-=0.2'
      );

    // Subtle scroll-driven parallax for the hero content
    try {
      gsap.to('.hero-content-wrapper', {
        scrollTrigger: {
          trigger: heroContainerRef.current || '#overview',
          start: 'top top',
          end: 'bottom top',
          scrub: 1,
        },
        y: 80,
        opacity: 0.35,
        ease: 'none',
      });
    } catch (e) {
      console.warn('ScrollTrigger parallax warning:', e);
    }
  });

  return (
    <section
      id="overview"
      ref={heroContainerRef}
      className="relative min-h-screen bg-[#080D10] text-white flex flex-col justify-between overflow-hidden pt-24 pb-12"
    >
      {/* 1. Cinematic Urban Intersection Canvas Visual (Background Layer) */}
      <UrbanIntersectionVisual />

      {/* 2. Precision Ambient Grid Overlay & Radial Glow */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-[#45C982]/[0.07] via-transparent to-transparent pointer-events-none" />

      {/* 3. Main Hero Content Container */}
      <div className="relative z-10 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 my-auto hero-content-wrapper">
        <div className="max-w-4xl space-y-8">
          {/* Engineering Category Badge */}
          <div className="hero-badge inline-flex items-center gap-2.5 px-3 py-1 rounded-full border border-[#45C982]/30 bg-[#45C982]/10 backdrop-blur-sm">
            <span className="w-2 h-2 rounded-full bg-[#45C982] animate-pulse" />
            <span className="text-xs font-mono font-medium tracking-wider text-[#45C982] uppercase">
              Next-Gen Autonomous Traffic Coordination
            </span>
            <span className="text-xs text-white/30">|</span>
            <span className="text-xs font-mono text-white/70">
              {isConnected
                ? `Rev #${snapshot?.state_revision ?? 0} Authoritative`
                : 'P4 Architecture Preview'}
            </span>
          </div>

          {/* Main Triple Headline (Space Grotesk) */}
          <h1 className="font-display text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-white leading-[1.08]">
            <span className="hero-headline-line block text-white">Understand the city.</span>
            <span className="hero-headline-line block text-[#45C982]">Anticipate congestion.</span>
            <span className="hero-headline-line block text-white/90">
              Coordinate every intersection.
            </span>
          </h1>

          {/* Short Project Description (Inter) */}
          <p className="hero-description text-base sm:text-lg lg:text-xl text-white/70 max-w-2xl font-normal leading-relaxed">
            AEGIS unites roadside computer vision, physics-informed queue estimation, and
            safety-critical phase enforcement into a synchronized, self-adapting urban traffic
            backbone.
          </p>

          {/* Restrained Engineering Telemetry Strip (IBM Plex Mono) */}
          <div className="pt-2 grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-3xl">
            <div className="hero-telemetry-item border-l border-white/15 pl-3 py-1">
              <span className="text-[10px] font-mono uppercase tracking-wider text-white/40 block">
                Perception Engine
              </span>
              <span className="text-xs sm:text-sm font-mono font-semibold text-white block mt-0.5">
                Multi-Cam YOLOv8
              </span>
            </div>

            <div className="hero-telemetry-item border-l border-white/15 pl-3 py-1">
              <span className="text-[10px] font-mono uppercase tracking-wider text-white/40 block">
                Safety Guarantee
              </span>
              <span className="text-xs sm:text-sm font-mono font-semibold text-[#45C982] block mt-0.5">
                Deterministic Phase Guard
              </span>
            </div>

            <div className="hero-telemetry-item border-l border-white/15 pl-3 py-1">
              <span className="text-[10px] font-mono uppercase tracking-wider text-white/40 block">
                Co-Simulation
              </span>
              <span className="text-xs sm:text-sm font-mono font-semibold text-white block mt-0.5">
                CARLA + SUMO
              </span>
            </div>

            <div className="hero-telemetry-item border-l border-white/15 pl-3 py-1">
              <span className="text-[10px] font-mono uppercase tracking-wider text-white/40 block">
                Visual Intelligence
              </span>
              <span className="text-xs sm:text-sm font-mono font-semibold text-white block mt-0.5">
                Gemini Vision API
              </span>
            </div>
          </div>

          {/* Actions & Live Dashboard Links */}
          <div className="hero-cta pt-4 flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
            <button
              onClick={() => {
                const el = document.getElementById('approach');
                el?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="px-6 py-3.5 rounded bg-[#45C982] hover:bg-[#3db874] text-[#080D10] text-sm font-mono font-semibold tracking-wide transition-all shadow-lg shadow-[#45C982]/20 text-center cursor-pointer"
            >
              Explore Architecture ↓
            </button>

            <button
              onClick={() => navigate('/dashboard')}
              className="px-6 py-3.5 rounded border border-white/20 bg-white/[0.05] hover:bg-white/10 text-white text-sm font-mono font-medium tracking-wide transition-all flex items-center justify-center gap-2 text-center group"
            >
              <span>Launch Operator Console</span>
              <ArrowRight className="w-4 h-4 text-[#45C982] group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>
      </div>

      {/* 4. Bottom Scroll Indicator */}
      <div className="relative z-10 w-full flex justify-center hero-scroll-indicator mt-8">
        <ScrollIndicator targetId="approach" />
      </div>
    </section>
  );
};
