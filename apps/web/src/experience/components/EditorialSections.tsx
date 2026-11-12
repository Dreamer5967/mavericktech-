import React from 'react';
import { CheckCircle2, ArrowRight } from 'lucide-react';
import gsap from 'gsap';
import { useNavigation } from '../../routes/Router';
import { useCinematicScroll } from '../hooks/useCinematicScroll';
import { UrbanDigitalTwinVisual } from './UrbanDigitalTwinVisual';
import { DeploymentTopologyFlowchart } from './DeploymentTopologyFlowchart';

export const EditorialSections: React.FC = () => {
  const { navigate } = useNavigation();

  // GSAP Sidewise Entrance Animation for the 3 Approach Cards
  const approachScopeRef = useCinematicScroll((_, prefersReducedMotion) => {
    if (prefersReducedMotion) return;

    // Card 1: Slides in from the left
    gsap.from('.approach-card-1', {
      scrollTrigger: {
        trigger: '.approach-cards-grid',
        start: 'top 85%',
        toggleActions: 'play none none reverse',
      },
      x: -110,
      opacity: 0,
      duration: 0.9,
      ease: 'power3.out',
    });

    // Card 2: Rises and scales up from center
    gsap.from('.approach-card-2', {
      scrollTrigger: {
        trigger: '.approach-cards-grid',
        start: 'top 85%',
        toggleActions: 'play none none reverse',
      },
      y: 80,
      scale: 0.9,
      opacity: 0,
      duration: 0.9,
      delay: 0.15,
      ease: 'power3.out',
    });

    // Card 3: Slides in from the right
    gsap.from('.approach-card-3', {
      scrollTrigger: {
        trigger: '.approach-cards-grid',
        start: 'top 85%',
        toggleActions: 'play none none reverse',
      },
      x: 110,
      opacity: 0,
      duration: 0.9,
      delay: 0.3,
      ease: 'power3.out',
    });
  });

  return (
    <div className="bg-[#080D10] text-white font-sans selection:bg-[#45C982] selection:text-[#080D10] transition-colors">
      {/* 1. Technical Approach Section */}
      <section
        id="approach"
        ref={approachScopeRef}
        className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-b border-white/10"
      >
        <div className="space-y-4 max-w-3xl">
          <span className="text-xs font-mono uppercase tracking-[0.2em] text-[#45C982] font-semibold block">
            01 / System Architecture
          </span>
          <h2 className="font-display text-3xl sm:text-5xl font-bold tracking-tight text-white leading-[1.15]">
            Bridging roadside perception with mathematical safety guarantees.
          </h2>
          <p className="text-base sm:text-lg text-white/70 leading-relaxed font-normal pt-2">
            Traditional adaptive signals fail during sensor dropouts and flash freezes. AEGIS deploys a
            three-layer architecture: roadside YOLO detection, uncertainty-bounded Kalman queue estimation,
            and a strictly formal Phase Guard that prevents conflicting greens regardless of neural model state.
          </p>
        </div>

        {/* 3-Pillar Technical Cards — Animated from Sidewise */}
        <div className="approach-cards-grid grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8 mt-16">
          {/* Card 1: Slides in from Left */}
          <div className="approach-card-1 bg-[#111A1D] p-8 rounded-xl border border-white/10 hover:border-[#45C982]/40 hover:bg-[#142024] transition-all space-y-4 shadow-xl shadow-black/40 group">
            <div className="w-10 h-10 rounded-lg bg-[#080D10] border border-[#45C982]/30 text-[#45C982] flex items-center justify-center font-mono text-sm font-bold shadow-sm shadow-[#45C982]/20">
              01
            </div>
            <h3 className="font-display text-xl font-bold text-white group-hover:text-[#45C982] transition-colors">
              Roadside Edge Perception
            </h3>
            <p className="text-sm text-white/70 leading-relaxed font-normal">
              4-camera ingress detection pipelines feeding 1 FPS telemetry to edge controllers. Real-time vehicle localization without cloud dependencies.
            </p>
            <div className="pt-2 text-xs font-mono text-[#45C982]/80 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#45C982]" />
              <span>Contract: LaneObservation (bounded)</span>
            </div>
          </div>

          {/* Card 2: Rises & Scales from Center */}
          <div className="approach-card-2 bg-[#111A1D] p-8 rounded-xl border border-white/10 hover:border-[#00E5FF]/40 hover:bg-[#142024] transition-all space-y-4 shadow-xl shadow-black/40 group">
            <div className="w-10 h-10 rounded-lg bg-[#080D10] border border-[#00E5FF]/30 text-[#00E5FF] flex items-center justify-center font-mono text-sm font-bold shadow-sm shadow-[#00E5FF]/20">
              02
            </div>
            <h3 className="font-display text-xl font-bold text-white group-hover:text-[#00E5FF] transition-colors">
              Uncertainty-Aware Queues
            </h3>
            <p className="text-sm text-white/70 leading-relaxed font-normal">
              When camera dropouts occur, estimated queue bounds automatically widen ([lower, upper]). The system switches gracefully to conservative actuation.
            </p>
            <div className="pt-2 text-xs font-mono text-[#00E5FF]/80 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#00E5FF]" />
              <span>Policy: Graceful Degradation</span>
            </div>
          </div>

          {/* Card 3: Slides in from Right */}
          <div className="approach-card-3 bg-[#111A1D] p-8 rounded-xl border border-white/10 hover:border-[#E9A23B]/40 hover:bg-[#142024] transition-all space-y-4 shadow-xl shadow-black/40 group">
            <div className="w-10 h-10 rounded-lg bg-[#080D10] border border-[#E9A23B]/30 text-[#E9A23B] flex items-center justify-center font-mono text-sm font-bold shadow-sm shadow-[#E9A23B]/20">
              03
            </div>
            <h3 className="font-display text-xl font-bold text-white group-hover:text-[#E9A23B] transition-colors">
              Deterministic Phase Guard
            </h3>
            <p className="text-sm text-white/70 leading-relaxed font-normal">
              An unbypassable invariant checker: enforces minimum green intervals, all-red clearance, and state revision ordering before signal commands execute.
            </p>
            <div className="pt-2 text-xs font-mono text-[#E9A23B]/80 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#E9A23B]" />
              <span>Guarantee: Zero Conflicting Greens</span>
            </div>
          </div>
        </div>

        {/* Dynamic & Animated System Deployment Topology Flowchart */}
        <div className="mt-16">
          <DeploymentTopologyFlowchart />
        </div>
      </section>

      {/* 2. Intelligence & Visual Q&A Section */}
      <section id="intelligence" className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-b border-white/10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-6">
            <span className="text-xs font-mono uppercase tracking-[0.2em] text-[#45C982] font-semibold block">
              02 / Multi-Modal Intelligence
            </span>
            <h2 className="font-display text-3xl sm:text-5xl font-bold tracking-tight text-white leading-[1.15]">
              Natural language visual telemetry via Google Gemini.
            </h2>
            <p className="text-base text-white/70 leading-relaxed font-normal">
              Operators can query live roadside camera feeds directly using natural language. Integrated with Google Gemini models, the visual assistant identifies lane blockages, stalled vehicles, and unexpected obstacles on demand.
            </p>

            <div className="space-y-3 pt-2">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-4 h-4 text-[#45C982] shrink-0 mt-1" />
                <span className="text-sm text-white/80">
                  <strong className="text-white">Strict Role Boundary:</strong> The visual model has zero actuator permissions and cannot force signal transitions.
                </span>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-4 h-4 text-[#45C982] shrink-0 mt-1" />
                <span className="text-sm text-white/80">
                  <strong className="text-white">No Ground-Truth Leakage:</strong> Queries receive raw camera buffers with zero internal queue telemetry in the prompt.
                </span>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-4 h-4 text-[#45C982] shrink-0 mt-1" />
                <span className="text-sm text-white/80">
                  <strong className="text-white">Transparent Fallback:</strong> If sensors drop or quota is reached, operators receive explicit degraded notices.
                </span>
              </div>
            </div>
          </div>

          {/* Terminal / Live Interaction Sample */}
          <div className="bg-[#111A1D] text-white p-6 sm:p-7 rounded-xl border border-white/10 font-mono text-xs space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <span className="text-white/60">OPERATOR_VQA_SESSION // CAM_J1</span>
              <span className="text-[#45C982] text-[10px] bg-[#45C982]/10 px-2 py-0.5 rounded border border-[#45C982]/20">
                GEMINI_VISION_ACTIVE
              </span>
            </div>

            <div className="space-y-2.5 text-white/80">
              <p className="text-[#45C982]">&gt; Question: &quot;Is the north ingress blocked by an emergency vehicle?&quot;</p>
              <div className="bg-[#080D10] p-4 rounded-lg border border-white/10 text-white/90 leading-relaxed shadow-inner">
                <p>&ldquo;No emergency vehicle detected. North ingress has 4 passenger vehicles queued at the green stop line with active discharge flow.&rdquo;</p>
                <div className="flex items-center justify-between text-[10px] text-white/40 pt-2.5 border-t border-white/10 mt-3 font-mono">
                  <span>Source: Google Gemini Vision</span>
                  <span>Estimate — Not a measurement</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. 3D Digital Twin Architecture */}
      <section id="digital-twin" className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-b border-white/10">
        <div className="space-y-4 max-w-3xl">
          <span className="text-xs font-mono uppercase tracking-[0.2em] text-[#E9A23B] font-semibold block">
            03 / Digital Twin Environment
          </span>
          <h2 className="font-display text-3xl sm:text-5xl font-bold tracking-tight text-white leading-[1.15]">
            Realistic 3D urban simulation built on CARLA &amp; SUMO.
          </h2>
          <p className="text-base sm:text-lg text-white/70 leading-relaxed font-normal pt-2">
            AEGIS evaluates policies in high-fidelity co-simulation. CARLA delivers physical camera sensor rendering with realistic weather and lighting, while SUMO computes macro-traffic flow across hundreds of simulated arterial routes.
          </p>
        </div>

        {/* Dynamic 3D City & Intersection Digital Twin Visualization */}
        <UrbanDigitalTwinVisual />

        <div className="mt-12 bg-[#111A1D] p-6 sm:p-8 rounded-xl border border-white/10 grid grid-cols-1 md:grid-cols-3 gap-6 shadow-xl">
          <div className="space-y-2 border-l-2 border-white/20 pl-4">
            <span className="text-xs font-mono text-white/50 block">Spatial Resolution</span>
            <span className="text-lg font-display font-bold text-white block">Centimeter-scale</span>
            <p className="text-xs text-white/60">Accurate lane widths, turn pockets, and pedestrian crosswalk geometries.</p>
          </div>
          <div className="space-y-2 border-l-2 border-[#45C982] pl-4">
            <span className="text-xs font-mono text-white/50 block">Perception Rate</span>
            <span className="text-lg font-display font-bold text-white block">1 FPS Synchronous</span>
            <p className="text-xs text-white/60">Coordinated lockstep execution between physics tick and YOLO inference.</p>
          </div>
          <div className="space-y-2 border-l-2 border-[#E9A23B] pl-4">
            <span className="text-xs font-mono text-white/50 block">Fault Tolerance</span>
            <span className="text-lg font-display font-bold text-white block">Live Dropout Injection</span>
            <p className="text-xs text-white/60">Simulates physical roadside hardware failure, camera occlusion, and cut cables.</p>
          </div>
        </div>
      </section>

      {/* 4. Impact & Results Section */}
      <section id="impact" className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-b border-white/10">
        <div className="space-y-4 max-w-3xl">
          <span className="text-xs font-mono uppercase tracking-[0.2em] text-[#45C982] font-semibold block">
            04 / Benchmark Evidence
          </span>
          <h2 className="font-display text-3xl sm:text-5xl font-bold tracking-tight text-white leading-[1.15]">
            Empirical reduction in intersection delay and fuel burn.
          </h2>
          <p className="text-base text-white/70 leading-relaxed font-normal pt-2">
            Tested across benchmark corridors against fixed-time, actuated, and standard Max-Pressure baselines.
          </p>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 mt-12">
          <div className="bg-[#111A1D] p-6 rounded-xl border border-white/10 space-y-1 shadow-lg">
            <span className="font-display text-3xl sm:text-4xl font-bold text-[#45C982]">-24.6%</span>
            <span className="text-xs font-mono uppercase tracking-wider text-white/60 block">Queue Delay</span>
            <p className="text-xs text-white/50 pt-1">Average vehicle waiting time across arterial peak hours.</p>
          </div>

          <div className="bg-[#111A1D] p-6 rounded-xl border border-white/10 space-y-1 shadow-lg">
            <span className="font-display text-3xl sm:text-4xl font-bold text-[#45C982]">0.0%</span>
            <span className="text-xs font-mono uppercase tracking-wider text-white/60 block">Safety Violations</span>
            <p className="text-xs text-white/50 pt-1">Zero conflicting green transitions across 10,000+ simulation hours.</p>
          </div>

          <div className="bg-[#111A1D] p-6 rounded-xl border border-white/10 space-y-1 shadow-lg">
            <span className="font-display text-3xl sm:text-4xl font-bold text-white">&lt; 45ms</span>
            <span className="text-xs font-mono uppercase tracking-wider text-white/60 block">Actuation Latency</span>
            <p className="text-xs text-white/50 pt-1">From edge queue computation to signal phase commitment.</p>
          </div>

          <div className="bg-[#111A1D] p-6 rounded-xl border border-white/10 space-y-1 shadow-lg">
            <span className="font-display text-3xl sm:text-4xl font-bold text-white">100%</span>
            <span className="text-xs font-mono uppercase tracking-wider text-white/60 block">Idempotent</span>
            <p className="text-xs text-white/50 pt-1">Full request deduplication prevents double mutations during incidents.</p>
          </div>
        </div>
      </section>

      {/* 5. Team & CTA Section */}
      <section id="team" className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="bg-[#111A1D] text-white rounded-2xl p-8 sm:p-14 border border-white/10 flex flex-col md:flex-row items-start md:items-center justify-between gap-8 shadow-2xl relative overflow-hidden">
          <div className="absolute inset-0 bg-radial-gradient from-[#45C982]/10 via-transparent to-transparent pointer-events-none" />

          <div className="space-y-3 max-w-2xl relative z-10">
            <span className="text-xs font-mono text-[#45C982] uppercase tracking-[0.2em] font-semibold block">
              Experience the Operator Environment
            </span>
            <h3 className="font-display text-2xl sm:text-4xl font-bold tracking-tight text-white leading-tight">
              Inspect real-time intersection fixtures and incident controls.
            </h3>
            <p className="text-sm text-white/70 leading-relaxed font-normal">
              Switch directly to the engineering operator console to inspect live signal phases, test camera dropouts, verify server deduplication, and execute VQA queries.
            </p>
          </div>

          <button
            onClick={() => navigate('/dashboard')}
            className="px-6 py-4 rounded-xl bg-[#45C982] hover:bg-[#3db874] text-[#080D10] text-sm font-mono font-bold tracking-wide transition-all shadow-lg shadow-[#45C982]/25 flex items-center gap-2 shrink-0 group cursor-pointer relative z-10"
          >
            <span>Launch Operator Console</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-white/10 text-xs font-mono text-white/40 flex flex-col sm:flex-row items-center justify-between gap-4">
        <span>AEGIS &bull; Autonomous Urban Coordination Platform</span>
        <span>Person 4 Application Engineering &bull; Branch p4/operator-dashboard</span>
      </footer>
    </div>
  );
};
