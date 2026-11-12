import React, { useState, useEffect, useRef } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Radio,
  ShieldCheck,
} from 'lucide-react';

interface StageData {
  id: string;
  stepNumber: string;
  badge: string;
  title: string;
  subtitle: string;
  description: string;
  failureMode: string;
  aegisResolution: string;
  metrics: {
    dropoutRate: string;
    observedQueue: string;
    estimatedQueue: string;
    phaseState: string;
    signalDelay: string;
    safetyInterlock: string;
  };
  junctionStates: Array<{
    id: string;
    name: string;
    feedStatus: 'ONLINE' | 'DEGRADED' | 'FAILED';
    phase: 'GREEN' | 'YELLOW' | 'RED';
    queue: number;
    uncertainty?: string;
  }>;
}

const STAGES: StageData[] = [
  {
    id: 'stage-baseline',
    stepNumber: '01',
    badge: 'STAGE 1 · NORMAL OPERATION',
    title: 'Arterial Grid Under Full Sensor Observability',
    subtitle: 'All 4 junction camera streams streaming at 1080p / 30 FPS.',
    description:
      'Under nominal conditions, decentralized MAPPO actors coordinate signal green waves along the 4-junction corridor. Continuous vehicle detections yield accurate queue counts across all 24 ingress lanes.',
    failureMode: 'None. Complete observability across all network approaches.',
    aegisResolution: 'Nominal MAPPO multi-agent coordination minimizes cumulative corridor wait times.',
    metrics: {
      dropoutRate: '0%',
      observedQueue: '14 veh',
      estimatedQueue: '14.0 ± 0.2 veh',
      phaseState: 'Phase 0 (Green Wave)',
      signalDelay: '26.1s / veh',
      safetyInterlock: 'Active (10s Min-Green)',
    },
    junctionStates: [
      { id: 'J1', name: 'Downtown North', feedStatus: 'ONLINE', phase: 'GREEN', queue: 14 },
      { id: 'J2', name: 'Commercial Hub', feedStatus: 'ONLINE', phase: 'YELLOW', queue: 8 },
      { id: 'J3', name: 'East Corridor', feedStatus: 'ONLINE', phase: 'RED', queue: 19 },
      { id: 'J4', name: 'Tech Boulevard', feedStatus: 'ONLINE', phase: 'GREEN', queue: 6 },
    ],
  },
  {
    id: 'stage-dropout',
    stepNumber: '02',
    badge: 'STAGE 2 · SENSOR LOSS INJECTED',
    title: 'Camera Packet Loss & Frame Dropout (40% Degradation)',
    subtitle: 'Adverse weather or hardware failure blinds roadside vision sensors at J3.',
    description:
      'Sudden camera packet loss drops 40% of detection frames on Junction J3. Traditional RL and SCATS controllers make the fatal error of assuming zero detected bounding boxes means zero waiting vehicles.',
    failureMode: 'Legacy controllers assume queue = 0, starve waiting traffic, and trigger arterial gridlock.',
    aegisResolution: 'AEGIS detects missing observation masks and flags input telemetry as degraded.',
    metrics: {
      dropoutRate: '40% Drop',
      observedQueue: '0 veh (Blind)',
      estimatedQueue: 'Warning: Degraded',
      phaseState: 'Threat: Starvation',
      signalDelay: '62.8s (Legacy Risk)',
      safetyInterlock: 'Intervention Required',
    },
    junctionStates: [
      { id: 'J1', name: 'Downtown North', feedStatus: 'ONLINE', phase: 'GREEN', queue: 15 },
      { id: 'J2', name: 'Commercial Hub', feedStatus: 'ONLINE', phase: 'RED', queue: 11 },
      { id: 'J3', name: 'East Corridor', feedStatus: 'FAILED', phase: 'RED', queue: 26, uncertainty: 'DROPOUT' },
      { id: 'J4', name: 'Tech Boulevard', feedStatus: 'ONLINE', phase: 'GREEN', queue: 7 },
    ],
  },
  {
    id: 'stage-estimation',
    stepNumber: '03',
    badge: 'STAGE 3 · BELIEF ESTIMATION',
    title: 'Uncertainty Interval & Queue State Recovery',
    subtitle: 'P3 state belief estimator reconstructs true lane occupancy bounds.',
    description:
      'Rather than hallucinating zero vehicles, AEGIS projects historical upstream inflow, turn probabilities, and cycle duration to maintain an explicit belief interval [24.0, 28.5] vehicles for Junction J3.',
    failureMode: 'Without uncertainty modeling, policies oscillate wildly or fail to assign green time.',
    aegisResolution: 'Belief state projects 26.2 ± 2.3 veh with 91.4% confidence score.',
    metrics: {
      dropoutRate: '40% Masked',
      observedQueue: '[UNAVAILABLE]',
      estimatedQueue: '26.2 ± 2.3 veh',
      phaseState: 'Phase 6 (Priority Queued)',
      signalDelay: '35.4s (Controlled)',
      safetyInterlock: 'Belief Bounds Validated',
    },
    junctionStates: [
      { id: 'J1', name: 'Downtown North', feedStatus: 'ONLINE', phase: 'GREEN', queue: 16 },
      { id: 'J2', name: 'Commercial Hub', feedStatus: 'ONLINE', phase: 'YELLOW', queue: 12 },
      { id: 'J3', name: 'East Corridor', feedStatus: 'DEGRADED', phase: 'RED', queue: 26, uncertainty: '± 2.3 veh' },
      { id: 'J4', name: 'Tech Boulevard', feedStatus: 'ONLINE', phase: 'GREEN', queue: 8 },
    ],
  },
  {
    id: 'stage-actuation',
    stepNumber: '04',
    badge: 'STAGE 4 · PHASE GUARD RESOLUTION',
    title: 'Deterministic Gating & Safe Signal Actuation',
    subtitle: 'Hardware constraints enforce min-green floor and clear the arterial corridor.',
    description:
      'MAPPO proposes recovery phase 0 to clear the pent-up queue at J3. The deterministic Phase Guard verifies that min-green (10.0s) and yellow clearance (3.0s) constraints are fully met before committing actions to SUMO.',
    failureMode: 'Unconstrained RL can output rapid phase toggles or cut green times below legal safety minimums.',
    aegisResolution: 'Phase Guard guarantees collision-free actuation; corridor queue clears to 5 vehicles.',
    metrics: {
      dropoutRate: '0% (Recovered)',
      observedQueue: '5 veh',
      estimatedQueue: '5.1 ± 0.4 veh',
      phaseState: 'Phase 0 (Gated Flush)',
      signalDelay: '28.9s (Normalized)',
      safetyInterlock: '100% Legal Phase Execution',
    },
    junctionStates: [
      { id: 'J1', name: 'Downtown North', feedStatus: 'ONLINE', phase: 'GREEN', queue: 8 },
      { id: 'J2', name: 'Commercial Hub', feedStatus: 'ONLINE', phase: 'GREEN', queue: 6 },
      { id: 'J3', name: 'East Corridor', feedStatus: 'ONLINE', phase: 'GREEN', queue: 5 },
      { id: 'J4', name: 'Tech Boulevard', feedStatus: 'ONLINE', phase: 'GREEN', queue: 4 },
    ],
  },
];

export const ScrollFailureSimulator: React.FC = () => {
  const [activeStageIdx, setActiveStageIdx] = useState(0);
  const stageRefs = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY + window.innerHeight * 0.45;

      stageRefs.current.forEach((ref, index) => {
        if (!ref) return;
        const top = ref.offsetTop;
        const height = ref.offsetHeight;

        if (scrollPosition >= top && scrollPosition < top + height) {
          setActiveStageIdx(index);
        }
      });
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToStage = (index: number) => {
    setActiveStageIdx(index);
    const targetRef = stageRefs.current[index];
    if (targetRef) {
      targetRef.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  const currentStage = STAGES[activeStageIdx];

  return (
    <div className="relative py-20 px-4 sm:px-6 lg:px-8 border-t border-slate-200 bg-slate-50/60">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="max-w-3xl mb-16 space-y-3">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded text-xs font-mono font-medium bg-orange-50 text-orange-700 border border-orange-200">
            <Radio className="w-3.5 h-3.5 text-orange-600 animate-pulse" />
            <span>SCROLL-DRIVEN PROBLEM SIMULATOR</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-black tracking-tight text-slate-900">
            The Sensor Failure Dilemma &amp; AEGIS Recovery
          </h2>
          <p className="text-slate-600 text-sm sm:text-base leading-relaxed">
            Scroll down to watch how roadside camera packet loss cripples traditional signal controllers—and how AEGIS
            dynamically estimates missing queues, bounds uncertainty, and executes deterministic recovery.
          </p>

          {/* Interactive Step Switcher Tabs */}
          <div className="flex flex-wrap items-center gap-2 pt-4">
            {STAGES.map((s, idx) => (
              <button
                key={s.id}
                onClick={() => scrollToStage(idx)}
                className={`
                  px-3.5 py-1.5 rounded-lg text-xs font-mono font-medium transition-all
                  ${
                    activeStageIdx === idx
                      ? 'bg-orange-500 text-white shadow-sm'
                      : 'bg-white text-slate-600 border border-slate-200 hover:border-orange-300'
                  }
                `}
              >
                <span>Stage {s.stepNumber}</span>
                <span className="hidden sm:inline text-[11px] opacity-80 ml-1.5">
                  {idx === 0 ? 'Nominal' : idx === 1 ? 'Dropout' : idx === 2 ? 'Estimation' : 'Recovery'}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Side-by-Side: Scrolling Steps (Left) + Sticky Simulation Monitor (Right) */}
        <div className="grid lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Scrolling Story Cards */}
          <div className="lg:col-span-7 space-y-16 py-4">
            {STAGES.map((stage, idx) => (
              <div
                key={stage.id}
                ref={(el) => {
                  stageRefs.current[idx] = el;
                }}
                className={`
                  p-7 rounded-xl border transition-all duration-300
                  ${
                    activeStageIdx === idx
                      ? 'bg-white border-orange-400 shadow-md shadow-orange-500/5 ring-1 ring-orange-400/20'
                      : 'bg-white/70 border-slate-200 opacity-60 hover:opacity-100'
                  }
                `}
              >
                <div className="flex items-center justify-between mb-4">
                  <span className="font-mono text-xs font-bold px-2.5 py-1 rounded bg-slate-100 text-slate-700 border border-slate-200">
                    {stage.badge}
                  </span>
                  <span className="font-mono text-2xl font-black text-slate-300">
                    #{stage.stepNumber}
                  </span>
                </div>

                <h3 className="text-xl font-bold text-slate-900 mb-1.5 tracking-tight">{stage.title}</h3>
                <div className="text-xs font-medium text-orange-600 mb-3.5 font-mono">{stage.subtitle}</div>
                <p className="text-sm text-slate-600 leading-relaxed mb-5">{stage.description}</p>

                {/* Technical Comparison Block */}
                <div className="grid sm:grid-cols-2 gap-3 pt-4 border-t border-slate-100 font-mono text-xs">
                  <div className="p-3 rounded-lg bg-rose-50/60 border border-rose-200/80">
                    <div className="flex items-center gap-1.5 text-rose-700 font-bold mb-1">
                      <AlertTriangle className="w-3.5 h-3.5" />
                      <span>Conventional Vulnerability</span>
                    </div>
                    <p className="text-[11px] text-slate-600 leading-relaxed font-sans">{stage.failureMode}</p>
                  </div>

                  <div className="p-3 rounded-lg bg-emerald-50/60 border border-emerald-200/80">
                    <div className="flex items-center gap-1.5 text-emerald-700 font-bold mb-1">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>AEGIS Resilient Action</span>
                    </div>
                    <p className="text-[11px] text-slate-600 leading-relaxed font-sans">{stage.aegisResolution}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Right Column: Sticky Live State & Architecture Monitor */}
          <div className="lg:col-span-5 sticky top-24">
            <div className="rounded-xl bg-white border border-slate-200 shadow-xl shadow-slate-200/50 p-6">
              {/* Monitor Header */}
              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <span
                    className={`w-2.5 h-2.5 rounded-full ${
                      activeStageIdx === 1 ? 'bg-rose-500 animate-ping' : 'bg-orange-500 animate-pulse'
                    }`}
                  />
                  <span className="font-mono text-xs font-bold text-slate-900 tracking-wider uppercase">
                    Arterial Grid Monitor · Stage {currentStage.stepNumber}
                  </span>
                </div>
                <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                  {currentStage.metrics.dropoutRate}
                </span>
              </div>

              {/* Real-Time Metrics Strip */}
              <div className="grid grid-cols-2 gap-2.5 my-4 font-mono text-xs">
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                  <div className="text-[10px] text-slate-400 uppercase">Observed Queue</div>
                  <div className="font-bold text-slate-800 text-sm mt-0.5">
                    {currentStage.metrics.observedQueue}
                  </div>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                  <div className="text-[10px] text-slate-400 uppercase">Estimated Queue</div>
                  <div className="font-bold text-orange-600 text-sm mt-0.5">
                    {currentStage.metrics.estimatedQueue}
                  </div>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                  <div className="text-[10px] text-slate-400 uppercase">Arterial Delay</div>
                  <div className="font-bold text-slate-800 text-sm mt-0.5">
                    {currentStage.metrics.signalDelay}
                  </div>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                  <div className="text-[10px] text-slate-400 uppercase">Phase Guard Safety</div>
                  <div className="font-bold text-emerald-600 text-xs mt-0.5 truncate">
                    {currentStage.metrics.safetyInterlock}
                  </div>
                </div>
              </div>

              {/* 4-Junction Grid Visualization */}
              <div className="space-y-2 pt-2 border-t border-slate-100">
                <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 mb-1">
                  <span>Corridor Junctions (J1 – J4)</span>
                  <span>Signal Phase Status</span>
                </div>

                {currentStage.junctionStates.map((j) => {
                  const isGreen = j.phase === 'GREEN';
                  const isYellow = j.phase === 'YELLOW';
                  const isRed = j.phase === 'RED';
                  const isFailed = j.feedStatus === 'FAILED';
                  const isDegraded = j.feedStatus === 'DEGRADED';

                  return (
                    <div
                      key={j.id}
                      className={`
                        p-3 rounded-lg border transition-all duration-200 flex items-center justify-between
                        ${
                          isFailed
                            ? 'bg-rose-50/70 border-rose-300'
                            : isDegraded
                            ? 'bg-amber-50/70 border-amber-300'
                            : 'bg-slate-50 border-slate-200'
                        }
                      `}
                    >
                      <div className="flex items-center gap-3">
                        <div className="font-mono text-xs font-bold text-slate-900 w-6">{j.id}</div>
                        <div>
                          <div className="text-xs font-medium text-slate-800 flex items-center gap-1.5">
                            <span>{j.name}</span>
                            {isFailed && (
                              <span className="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded bg-rose-200 text-rose-800">
                                40% LOSS
                              </span>
                            )}
                            {isDegraded && (
                              <span className="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded bg-amber-200 text-amber-800">
                                KALMAN FILTER
                              </span>
                            )}
                          </div>
                          <div className="text-[10px] font-mono text-slate-500 mt-0.5">
                            Queue: <strong className="text-slate-800">{j.queue} veh</strong>
                            {j.uncertainty && (
                              <span className="text-orange-600 font-semibold ml-1">
                                [{j.uncertainty}]
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Signal LED Indicator */}
                      <div className="flex items-center gap-1.5 bg-white px-2 py-1 rounded border border-slate-200">
                        <span
                          className={`w-2.5 h-2.5 rounded-full transition-all ${
                            isRed ? 'bg-rose-500 shadow-sm shadow-rose-500/50' : 'bg-slate-200'
                          }`}
                        />
                        <span
                          className={`w-2.5 h-2.5 rounded-full transition-all ${
                            isYellow ? 'bg-amber-400 shadow-sm shadow-amber-400/50' : 'bg-slate-200'
                          }`}
                        />
                        <span
                          className={`w-2.5 h-2.5 rounded-full transition-all ${
                            isGreen ? 'bg-emerald-500 shadow-sm shadow-emerald-500/50' : 'bg-slate-200'
                          }`}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* System Protocol Proof */}
              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] font-mono text-slate-400">
                <span className="flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Phase Guard Gate: Locked</span>
                </span>
                <span className="text-slate-600 font-medium">Min-Green: 10.0s Floor</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
