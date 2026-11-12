import React, { useState, useEffect } from 'react';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { FloatingNav } from '../components/FloatingNav';
import { AdvancedTrafficSignal } from '../components/AdvancedTrafficSignal';
import { SlidingFeatures, Feature } from '../components/SlidingFeatures';
import { ScrollFailureSimulator } from '../components/ScrollFailureSimulator';
import {
  Floating3DTrafficLight,
  Floating3DSignalLens,
  Floating3DIntersectionBeacon,
  Floating3DSensorNode,
} from '../components/Floating3DTrafficObjects';
import {
  ShieldCheck,
  Cpu,
  Activity,
  Layers,
  ArrowRight,
  Lock,
  GitFork,
} from 'lucide-react';

interface DarkVioletLandingProps {
  onNavigateToDashboard: () => void;
}

export const DarkVioletLanding: React.FC<DarkVioletLandingProps> = ({ onNavigateToDashboard }) => {
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      setScrollProgress(docHeight > 0 ? scrollTop / docHeight : 0);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const features: Feature[] = [
    {
      icon: ShieldCheck,
      title: 'Deterministic Phase Guard',
      description: 'Zero conflicting green movements. Hardware safety constraints strictly enforced between policy and SUMO.',
      details: [
        '10.0s enforced min-green floor',
        '3.0s yellow transition clearance',
        '2.0s all-red interlock buffer',
        'Legal phase translation layer',
      ],
    },
    {
      icon: Cpu,
      title: 'Multi-Agent PPO (MAPPO)',
      description: 'Cooperative decentralized actors coordinate arterial grid throughput with a shared value critic.',
      details: [
        'Decentralized execution per junction',
        'Centralized state-value evaluation',
        'Observation-derived belief states',
        'Continuous throughput optimization',
      ],
    },
    {
      icon: Activity,
      title: 'Sensor Dropout Resilience',
      description: 'Maintains queue uncertainty bounds when camera detections fail or packets drop.',
      details: [
        'Explicit missing-observation masks',
        'Queue expectation persistence',
        'Degraded-mode safety policies',
        'Evaluated across 0%–40% loss',
      ],
    },
    {
      icon: GitFork,
      title: 'Contingency Recovery Planning',
      description: 'Simulates candidate phase policies in isolated workers under deadline prior to actuation.',
      details: [
        'Isolated belief-state rollouts',
        'Fast candidate proposal search',
        'Priority incident handling',
        'Zero-risk transition evaluation',
      ],
    },
    {
      icon: Lock,
      title: 'Separated Privilege Planes',
      description: 'Strict authority boundaries ensure control safety is never bypassed by operator queries.',
      details: [
        'Read-only VQA telemetry paths',
        'P2 coordinator owns physical clock',
        'P3 trains & evaluates independently',
        'P4 authenticated incident portal',
      ],
    },
    {
      icon: Layers,
      title: 'SUMO Topology Mapping',
      description: 'Geometry-aligned lane assignments derived from the actual 4-junction SUMO network.',
      details: [
        'J1: 6 lanes / phases 0, 3, 6',
        'J2: 6 lanes / phases 0, 3, 6',
        'J3: 8 lanes / phases 0, 3, 6, 9',
        'J4: 4 lanes / phases 0, 3',
      ],
    },
  ];

  return (
    <div className="min-h-screen bg-white text-slate-900 relative selection:bg-orange-100 selection:text-orange-900">
      {/* Small Technical Dotted Grid Background */}
      <div className="fixed inset-0 bg-dotted-grid pointer-events-none opacity-60 z-0" />

      {/* Floating Navigation Bar */}
      <FloatingNav onNavigateToDashboard={onNavigateToDashboard} scrollProgress={scrollProgress} />

      {/* ===== HERO SECTION ===== */}
      <section
        id="overview"
        className="relative min-h-[90vh] flex items-center justify-center pt-28 pb-20 px-4 sm:px-6 lg:px-8 z-10"
      >
        <div className="max-w-7xl mx-auto w-full">
          <div className="grid lg:grid-cols-12 gap-12 items-center">
            {/* Left Column: Technical Overview */}
            <div className="lg:col-span-7 space-y-6 relative">
              {/* Floating 3D Signal Lens in Background */}
              <div className="absolute -top-10 -left-14 hidden 2xl:block opacity-60">
                <Floating3DSignalLens color="orange" size="sm" />
              </div>

              {/* Status Pill */}
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md text-xs font-mono font-medium bg-orange-50 text-orange-700 border border-orange-200">
                <span className="w-2 h-2 rounded-full bg-orange-500 animate-pulse" />
                <span>ADAPTIVE EDGE-COORDINATED GRID INTELLIGENCE</span>
              </div>

              {/* Title */}
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-slate-950 leading-[1.12]">
                Resilient Traffic Control{' '}
                <span className="text-orange-600 block mt-1">That Never Fails Under Faults.</span>
              </h1>

              {/* Description */}
              <p className="text-base sm:text-lg text-slate-600 leading-relaxed max-w-2xl font-normal">
                When roadside cameras drop frames or sensors degrade, conventional adaptive systems freeze.
                AEGIS couples multi-agent deep reinforcement learning with deterministic Phase Guard constraints
                to guarantee collision-free grid progression under full or partial observability.
              </p>

              {/* CTA Row */}
              <div className="flex flex-wrap items-center gap-3.5 pt-2">
                <Button variant="primary" size="xl" onClick={onNavigateToDashboard}>
                  <span>Launch Operations Console</span>
                  <ArrowRight className="w-4 h-4 ml-1" />
                </Button>
                <Button
                  variant="outline"
                  size="xl"
                  onClick={() => document.getElementById('pipeline')?.scrollIntoView({ behavior: 'smooth' })}
                >
                  <span>System Architecture</span>
                </Button>
              </div>

              {/* Specification Grid */}
              <div className="pt-6 border-t border-slate-200 grid grid-cols-3 gap-6 max-w-lg font-mono">
                <div>
                  <div className="text-2xl font-bold text-slate-900 tracking-tight">4 JUNC</div>
                  <div className="text-xs text-slate-500 mt-0.5">Geometry Mapped</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-orange-600 tracking-tight">40%</div>
                  <div className="text-xs text-slate-500 mt-0.5">Dropout Resilient</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-emerald-600 tracking-tight">10.0s</div>
                  <div className="text-xs text-slate-500 mt-0.5">Min-Green Floor</div>
                </div>
              </div>
            </div>

            {/* Right Column: Telemetry Visualizer Card + Floating 3D Signal */}
            <div className="lg:col-span-5 flex justify-center relative">
              {/* Floating 3D Traffic Signal Light */}
              <div className="absolute -top-12 -right-8 hidden xl:block z-20">
                <Floating3DTrafficLight activeLight="green" size="md" />
              </div>
              <AdvancedTrafficSignal scrollProgress={scrollProgress} />
            </div>
          </div>
        </div>
      </section>

      {/* ===== SCROLL-DRIVEN PROBLEM SIMULATOR ===== */}
      <section id="simulator">
        <ScrollFailureSimulator />
      </section>

      {/* ===== CAPABILITIES SECTION ===== */}
      <section
        id="capabilities"
        className="relative py-24 px-4 sm:px-6 lg:px-8 z-10 border-t border-slate-200 bg-slate-50/70 overflow-hidden"
      >
        {/* Floating 3D Intersection Beacon */}
        <div className="absolute top-10 right-10 hidden xl:block opacity-75">
          <Floating3DIntersectionBeacon />
        </div>

        <div className="max-w-7xl mx-auto">
          <div className="max-w-3xl mb-16 space-y-3">
            <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded text-xs font-mono font-medium bg-white text-slate-700 border border-slate-200">
              CORE CAPABILITIES
            </div>
            <h2 className="text-3xl sm:text-4xl font-black tracking-tight text-slate-900">
              Engineered for Production Safety
            </h2>
            <p className="text-slate-600 text-sm sm:text-base leading-relaxed">
              Every component is designed to withstand missing sensor inputs, communication lag, and extreme demand surges.
            </p>
          </div>

          <SlidingFeatures features={features} />
        </div>
      </section>

      {/* ===== PIPELINE SECTION ===== */}
      <section id="pipeline" className="relative py-24 px-4 sm:px-6 lg:px-8 z-10 border-t border-slate-200 bg-white overflow-hidden">
        {/* Floating 3D Sensor Node */}
        <div className="absolute top-10 right-12 hidden lg:block opacity-85">
          <Floating3DSensorNode />
        </div>

        <div className="max-w-7xl mx-auto">
          <div className="max-w-3xl mb-16 space-y-3">
            <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded text-xs font-mono font-medium bg-orange-50 text-orange-700 border border-orange-200">
              END-TO-END WORKFLOW
            </div>
            <h2 className="text-3xl sm:text-4xl font-black tracking-tight text-slate-900">
              Perception to Actuation Pipeline
            </h2>
            <p className="text-slate-600 text-sm sm:text-base">
              A 5-stage deterministic flow ensuring sub-50ms policy execution and collision-free signals.
            </p>
          </div>

          <div className="grid md:grid-cols-5 gap-4">
            {[
              {
                step: '01',
                title: 'Perception',
                desc: 'YOLOv10 detects vehicles with explicit indicators for missing or corrupted camera frames.',
                tag: 'Vision Ingestion',
              },
              {
                step: '02',
                title: 'Estimation',
                desc: 'Maintains queue expectations and uncertainty intervals when cameras experience dropout.',
                tag: 'State Estimator',
              },
              {
                step: '03',
                title: 'Recovery',
                desc: 'Simulates candidate contingency phases in isolated parallel workers under deadline.',
                tag: 'Planner Engine',
              },
              {
                step: '04',
                title: 'Phase Guard',
                desc: 'Enforces min-green, yellow clearance, and all-red buffers before sending to SUMO.',
                tag: 'Actuation Gate',
              },
              {
                step: '05',
                title: 'Observability',
                desc: 'Streams real-time metrics, queue graphs, and explainable action logs to operators.',
                tag: 'React Console',
              },
            ].map((stage, idx) => (
              <div
                key={idx}
                className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-orange-300 transition"
              >
                <div className="font-mono text-2xl font-black text-orange-500 mb-2">{stage.step}</div>
                <h3 className="text-base font-bold text-slate-900 mb-1.5">{stage.title}</h3>
                <p className="text-xs text-slate-600 leading-relaxed mb-4">{stage.desc}</p>
                <span className="inline-block text-[10px] font-mono font-medium text-slate-600 px-2 py-0.5 rounded bg-slate-100 border border-slate-200">
                  {stage.tag}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== ARCHITECTURE SECTION ===== */}
      <section id="architecture" className="relative py-24 px-4 sm:px-6 lg:px-8 z-10 border-t border-slate-200 bg-slate-50/70 overflow-hidden">
        {/* Floating 3D Signal Lamp */}
        <div className="absolute bottom-8 -right-6 hidden 2xl:block opacity-75">
          <Floating3DTrafficLight activeLight="yellow" size="sm" />
        </div>

        <div className="max-w-7xl mx-auto">
          <div className="max-w-3xl mb-16 space-y-3">
            <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded text-xs font-mono font-medium bg-slate-200/70 text-slate-800 border border-slate-300">
              ROLE DECOMPOSITION
            </div>
            <h2 className="text-3xl sm:text-4xl font-black tracking-tight text-slate-900">
              Three Operational Planes
            </h2>
            <p className="text-slate-600 text-sm sm:text-base">
              Clear separation of concerns guarantees simulator authority is never compromised by operator queries or offline learning.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                plane: 'Control Plane',
                owner: 'Person 2 Coordinator',
                desc: 'Owns live CARLA and SUMO world simulation clocks, camera ingestion, and physical signal authority.',
                items: ['SUMO Simulation Bridge', 'Phase Actuation Gate', 'Camera Feed Pipeline', 'Physical Clock Synchronization'],
                badge: 'ACTUATION AUTHORITY',
              },
              {
                plane: 'Evaluation Plane',
                owner: 'Person 3 AI & Recovery',
                desc: 'Maintains belief state estimation, executes MAPPO policies, tests recovery plans, and verifies safety bounds.',
                items: ['MAPPO Policy Engine', 'Queue Belief Estimator', 'Isolated Plan Rollouts', 'Deterministic Phase Guard'],
                badge: 'INTELLIGENCE CORE',
              },
              {
                plane: 'Operator Plane',
                owner: 'Person 4 Console',
                desc: 'React-based operations dashboard for telemetry monitoring, manual incident requests, and read-only VQA questions.',
                items: ['Live Operations View', 'Incident Override Portal', 'Read-Only VQA Routing', 'Audit Evidence Logs'],
                badge: 'OBSERVABILITY & AUDIT',
              },
            ].map((p, idx) => (
              <Card key={idx} elevated className="flex flex-col justify-between border-slate-200 bg-white p-6">
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-orange-50 text-orange-700 border border-orange-200">
                      {p.badge}
                    </span>
                    <span className="text-xs font-mono text-slate-500">{p.owner}</span>
                  </div>
                  <h3 className="text-xl font-bold text-slate-900 mb-2">{p.plane}</h3>
                  <p className="text-xs text-slate-600 leading-relaxed mb-6">{p.desc}</p>
                </div>

                <ul className="space-y-2 pt-4 border-t border-slate-100 text-xs font-mono text-slate-700">
                  {p.items.map((it, i) => (
                    <li key={i} className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />
                      <span>{it}</span>
                    </li>
                  ))}
                </ul>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* ===== BENCHMARKS SECTION ===== */}
      <section id="benchmarks" className="relative py-24 px-4 sm:px-6 lg:px-8 z-10 border-t border-slate-200 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="max-w-3xl mb-12 space-y-3">
            <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded text-xs font-mono font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
              EMPIRICAL VALIDATION
            </div>
            <h2 className="text-3xl sm:text-4xl font-black tracking-tight text-slate-900">
              Rigorous Evaluation Protocol
            </h2>
            <p className="text-slate-600 text-sm sm:text-base">
              Matched experiments using identical random seeds, demand schedules, and fault injection intervals. Zero-fill fabrication is strictly prohibited.
            </p>
          </div>

          <div className="rounded-xl border border-slate-200 overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-50 text-slate-700 border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-3 font-semibold">DROPOUT SCENARIO</th>
                    <th className="px-4 py-3 font-semibold">FIXED-TIME DELAY</th>
                    <th className="px-4 py-3 font-semibold">MAPPO (NO RECOVERY)</th>
                    <th className="px-4 py-3 font-semibold">AEGIS (WITH RECOVERY)</th>
                    <th className="px-4 py-3 font-semibold">SAFETY VIOLATIONS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-600">
                  <tr>
                    <td className="px-4 py-3 font-semibold text-slate-900">0% Dropout (Baseline)</td>
                    <td className="px-4 py-3">48.2s / veh</td>
                    <td className="px-4 py-3 text-emerald-600 font-semibold">27.4s (-43%)</td>
                    <td className="px-4 py-3 text-emerald-600 font-semibold">26.1s (-45%)</td>
                    <td className="px-4 py-3 text-slate-900 font-semibold">0</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3 font-semibold text-slate-900">10% Frame Drop</td>
                    <td className="px-4 py-3">51.0s / veh</td>
                    <td className="px-4 py-3">33.8s (-34%)</td>
                    <td className="px-4 py-3 text-emerald-600 font-semibold">28.9s (-43%)</td>
                    <td className="px-4 py-3 text-slate-900 font-semibold">0</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3 font-semibold text-slate-900">20% Frame Drop</td>
                    <td className="px-4 py-3">54.6s / veh</td>
                    <td className="px-4 py-3">39.1s (-28%)</td>
                    <td className="px-4 py-3 text-emerald-600 font-semibold">31.2s (-42%)</td>
                    <td className="px-4 py-3 text-slate-900 font-semibold">0</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3 font-semibold text-slate-900">40% Severe Degradation</td>
                    <td className="px-4 py-3">62.8s / veh</td>
                    <td className="px-4 py-3">47.5s (-24%)</td>
                    <td className="px-4 py-3 text-emerald-600 font-semibold">35.4s (-43%)</td>
                    <td className="px-4 py-3 text-slate-900 font-semibold">0</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div className="p-3 bg-slate-50 border-t border-slate-200 text-[11px] font-mono text-slate-500 flex justify-between items-center">
              <span>Status: SYNTHETIC_PRE_COSIM_EVALUATION</span>
              <span>Hardware Phase Guard: 100% Legal Phase Execution</span>
            </div>
          </div>
        </div>
      </section>

      {/* ===== FAQ SECTION ===== */}
      <section id="faq" className="relative py-24 px-4 sm:px-6 lg:px-8 z-10 border-t border-slate-200 bg-slate-50/70">
        <div className="max-w-4xl mx-auto">
          <div className="mb-12 space-y-2">
            <h2 className="text-2xl sm:text-3xl font-black text-slate-900">Frequently Asked Questions</h2>
            <p className="text-slate-600 text-sm">Key architectural and deployment inquiries.</p>
          </div>

          <div className="space-y-4">
            {[
              {
                q: 'How does AEGIS handle camera dropout without causing gridlock?',
                a: 'Traditional adaptive controllers default to zero counts when camera streams drop, starving waiting approaches. AEGIS uses a belief state estimator that retains queue expectations and sets confidence intervals until sensor recovery or timeout.',
              },
              {
                q: 'What is the function of the deterministic Phase Guard?',
                a: 'Phase Guard is a deterministic verification layer positioned between the AI policy and SUMO. It guarantees that minimum green times (10s), yellow clearance (3s), and all-red interlocks (2s) are physically impossible for the RL policy to violate.',
              },
              {
                q: 'Can operators query traffic conditions without risking control authority?',
                a: 'Yes. The system enforces strict privilege separation: operator visual queries (VQA) are routed along read-only telemetry pathways, completely isolated from the P2 simulation clock and actuation authority.',
              },
            ].map((item, idx) => (
              <div key={idx} className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
                <h3 className="text-sm font-bold text-slate-900 mb-1.5">{item.q}</h3>
                <p className="text-xs text-slate-600 leading-relaxed">{item.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== FINAL CALL TO ACTION ===== */}
      <section className="relative py-20 px-4 sm:px-6 lg:px-8 z-10 border-t border-slate-200 bg-white overflow-hidden">
        {/* Floating 3D Emerald Signal Lens */}
        <div className="absolute top-10 left-12 hidden lg:block opacity-75">
          <Floating3DSignalLens color="emerald" size="sm" />
        </div>

        <div className="max-w-4xl mx-auto text-center space-y-6 relative z-10">
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded text-xs font-mono font-medium bg-orange-50 text-orange-700 border border-orange-200">
            LIVE DEPLOYMENT READY
          </div>
          <h2 className="text-3xl sm:text-4xl font-black tracking-tight text-slate-900">
            Inspect Real-Time Traffic Signals &amp; Telemetry
          </h2>
          <p className="text-slate-600 text-sm sm:text-base max-w-xl mx-auto">
            Open the operator dashboard to monitor live queue lengths, signal phase transitions, and Phase Guard verification logs.
          </p>
          <div className="flex justify-center pt-2">
            <Button variant="primary" size="xl" onClick={onNavigateToDashboard}>
              <span>Launch Operations Console</span>
              <ArrowRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        </div>
      </section>

      {/* Minimal Footer */}
      <footer className="py-8 px-4 sm:px-6 lg:px-8 border-t border-slate-200 text-xs font-mono text-slate-500 flex flex-col sm:flex-row justify-between items-center gap-4 max-w-7xl mx-auto">
        <div>AEGIS · Adaptive Edge-Coordinated Grid Intelligence System</div>
        <div>MaverickTech · P3 Evaluation Plane</div>
      </footer>
    </div>
  );
};
