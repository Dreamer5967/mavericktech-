import React, { useState, useEffect, useRef } from 'react';
import gsap from 'gsap';
import {
  Camera,
  Cpu,
  ShieldCheck,
  Radio,
  Sparkles,
  RotateCcw,
  Terminal,
  Activity,
  Zap,
} from 'lucide-react';

interface TopologyNode {
  id: string;
  tier: number;
  title: string;
  subtitle: string;
  badge: string;
  badgeColor: 'emerald' | 'amber' | 'cyan' | 'blue';
  icon: React.ReactNode;
  specs: { label: string; value: string }[];
  contract: string;
  status: 'ONLINE' | 'ACTIVE' | 'ENFORCING' | 'SYNCED';
}

export const DeploymentTopologyFlowchart: React.FC = () => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [selectedNode, setSelectedNode] = useState<string>('phase-guard');
  const [isFlowing, setIsFlowing] = useState<boolean>(true);
  const [assemblyKey, setAssemblyKey] = useState<number>(0);

  const nodes: Record<string, TopologyNode> = {
    'cam-j1': {
      id: 'cam-j1',
      tier: 1,
      title: 'CAM_J1 Ingress Sensor',
      subtitle: 'North Arterial Approach',
      badge: '1 FPS Synchronous',
      badgeColor: 'emerald',
      icon: <Camera className="w-4 h-4 text-[#45C982]" />,
      specs: [
        { label: 'Capture Mode', value: '1920×1080 RGB' },
        { label: 'Ingress Rate', value: '1 FPS Lockstep' },
        { label: 'Hardware', value: 'Edge Optical Rig' },
      ],
      contract: 'LaneObservation (raw pixels)',
      status: 'ONLINE',
    },
    'cam-j2': {
      id: 'cam-j2',
      tier: 1,
      title: 'CAM_J2 Ingress Sensor',
      subtitle: 'East Arterial Approach',
      badge: '1 FPS Synchronous',
      badgeColor: 'emerald',
      icon: <Camera className="w-4 h-4 text-[#45C982]" />,
      specs: [
        { label: 'Capture Mode', value: '1920×1080 RGB' },
        { label: 'Ingress Rate', value: '1 FPS Lockstep' },
        { label: 'Hardware', value: 'Edge Optical Rig' },
      ],
      contract: 'LaneObservation (raw pixels)',
      status: 'ONLINE',
    },
    'cam-j3': {
      id: 'cam-j3',
      tier: 1,
      title: 'CAM_J3 Ingress Sensor',
      subtitle: 'South Arterial Approach',
      badge: '1 FPS Synchronous',
      badgeColor: 'emerald',
      icon: <Camera className="w-4 h-4 text-[#45C982]" />,
      specs: [
        { label: 'Capture Mode', value: '1920×1080 RGB' },
        { label: 'Ingress Rate', value: '1 FPS Lockstep' },
        { label: 'Hardware', value: 'Edge Optical Rig' },
      ],
      contract: 'LaneObservation (raw pixels)',
      status: 'ONLINE',
    },
    'cam-j4': {
      id: 'cam-j4',
      tier: 1,
      title: 'CAM_J4 Ingress Sensor',
      subtitle: 'West Arterial Approach',
      badge: '1 FPS Synchronous',
      badgeColor: 'emerald',
      icon: <Camera className="w-4 h-4 text-[#45C982]" />,
      specs: [
        { label: 'Capture Mode', value: '1920×1080 RGB' },
        { label: 'Ingress Rate', value: '1 FPS Lockstep' },
        { label: 'Hardware', value: 'Edge Optical Rig' },
      ],
      contract: 'LaneObservation (raw pixels)',
      status: 'ONLINE',
    },
    'edge-perception': {
      id: 'edge-perception',
      tier: 2,
      title: 'Roadside Edge Perception Node',
      subtitle: 'YOLOv8 + Kalman Queue Estimator',
      badge: 'Perception Core',
      badgeColor: 'cyan',
      icon: <Cpu className="w-5 h-5 text-[#00E5FF]" />,
      specs: [
        { label: 'Model Architecture', value: 'YOLOv8 Real-Time TensorRT' },
        { label: 'Queue Interval Bound', value: '[q_lower, q_upper] (CI 95%)' },
        { label: 'Sensor Dropout Policy', value: 'Graceful Degradation' },
      ],
      contract: 'SnapshotResponse v1.0 (State Revision Monotonic)',
      status: 'ACTIVE',
    },
    'phase-guard': {
      id: 'phase-guard',
      tier: 3,
      title: 'Deterministic Phase Guard',
      subtitle: 'Formal Safety Invariant Kernel',
      badge: 'Zero-Violation Core',
      badgeColor: 'emerald',
      icon: <ShieldCheck className="w-6 h-6 text-[#45C982]" />,
      specs: [
        { label: 'Safety Guarantee', value: 'Zero Conflicting Greens' },
        { label: 'All-Red Clearance', value: 'Enforced 3.0s Minimum' },
        { label: 'State Revision', value: 'Strict Monotonic Ordering' },
      ],
      contract: 'Verified Invariant Contract (Non-bypassable)',
      status: 'ENFORCING',
    },
    'signal-actuator': {
      id: 'signal-actuator',
      tier: 4,
      title: 'Intersection Signal Controller',
      subtitle: 'Physical Phase Actuation Commit',
      badge: 'Hardware Actuator',
      badgeColor: 'amber',
      icon: <Radio className="w-4 h-4 text-[#E9A23B]" />,
      specs: [
        { label: 'Protocol', value: 'NTCIP 1202 / SUMO TraCI' },
        { label: 'Cycle Boundary', value: 'Safety Guard Signed' },
        { label: 'Commit Latency', value: '< 45ms committed' },
      ],
      contract: 'PhaseCommitCommand (Idempotent)',
      status: 'ACTIVE',
    },
    'operator-console': {
      id: 'operator-console',
      tier: 4,
      title: 'Supervisory Operator Console',
      subtitle: 'P4 Real-Time Control & Telemetry',
      badge: 'Supervisory Port 8000',
      badgeColor: 'emerald',
      icon: <Terminal className="w-4 h-4 text-[#45C982]" />,
      specs: [
        { label: 'Sync Polling', value: '3000ms Refresh Interval' },
        { label: 'Mutation Guard', value: 'UUID Request Deduplication' },
        { label: 'Operator Auth', value: 'Bearer Token Authorization' },
      ],
      contract: 'REST /api/v1/snapshot · /api/v1/faults',
      status: 'SYNCED',
    },
    'gemini-vision': {
      id: 'gemini-vision',
      tier: 4,
      title: 'Gemini Multimodal VQA Node',
      subtitle: 'Natural Language Video Telemetry',
      badge: 'Port 8001 AI Vision',
      badgeColor: 'cyan',
      icon: <Sparkles className="w-4 h-4 text-[#00E5FF]" />,
      specs: [
        { label: 'Provider', value: 'Google Gemini 1.5/2.0 API' },
        { label: 'Role Boundary', value: 'Read-Only (Zero Actuator Rights)' },
        { label: 'Ground Truth Leakage', value: 'None (Raw Frame Buffers)' },
      ],
      contract: 'POST /api/v1/questions/vqa',
      status: 'ACTIVE',
    },
  };

  // GSAP Assembly Animation: Boxes fall/slide in from different directions to assemble the flowchart!
  useEffect(() => {
    if (!containerRef.current) return;

    const ctx = gsap.context(() => {
      // 1. Initial hidden states
      gsap.set('.flow-tier-1', { x: -80, opacity: 0 });
      gsap.set('.flow-tier-2', { y: -70, opacity: 0, scale: 0.9 });
      gsap.set('.flow-tier-3', { scale: 0.7, opacity: 0, rotationY: -15 });
      gsap.set('.flow-tier-4', { x: 80, opacity: 0 });
      gsap.set('.flow-cable-svg', { opacity: 0 });

      // 2. Coordinated staggered timeline
      const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });

      tl.to('.flow-tier-1', {
        x: 0,
        opacity: 1,
        duration: 0.75,
        stagger: 0.1,
      })
        .to(
          '.flow-tier-2',
          {
            y: 0,
            opacity: 1,
            scale: 1,
            duration: 0.8,
          },
          '-=0.4'
        )
        .to(
          '.flow-tier-3',
          {
            scale: 1,
            opacity: 1,
            rotationY: 0,
            duration: 0.85,
            ease: 'back.out(1.4)',
          },
          '-=0.3'
        )
        .to(
          '.flow-tier-4',
          {
            x: 0,
            opacity: 1,
            duration: 0.75,
            stagger: 0.1,
          },
          '-=0.4'
        )
        .to(
          '.flow-cable-svg',
          {
            opacity: 1,
            duration: 0.6,
          },
          '-=0.2'
        );
    }, containerRef);

    return () => ctx.revert();
  }, [assemblyKey]);

  const active = nodes[selectedNode] || nodes['phase-guard'];

  return (
    <div
      ref={containerRef}
      className="relative w-full rounded-2xl bg-[#080D10] border border-white/10 p-4 sm:p-7 shadow-2xl overflow-hidden font-sans my-8"
    >
      {/* Subtle Background High-Tech Circuit Grid */}
      <div className="absolute inset-0 bg-[radial-gradient(#45C982_1px,transparent_1px)] [background-size:28px_28px] opacity-[0.07] pointer-events-none" />
      <div className="absolute inset-0 bg-gradient-to-b from-[#080D10]/40 via-transparent to-[#080D10]/80 pointer-events-none" />

      {/* Top Header & Interactive Toolbar */}
      <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-white/10 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2 h-2 rounded-full bg-[#45C982] animate-pulse" />
            <span className="text-[11px] font-mono uppercase tracking-[0.2em] text-[#45C982] font-semibold">
              Live Architecture Topology
            </span>
          </div>
          <h3 className="font-display text-xl sm:text-2xl font-bold tracking-tight text-white">
            AEGIS Physical Node &amp; Data Pipeline Topology
          </h3>
          <p className="text-xs text-white/50 mt-0.5">
            Synchronous 4-camera perception feeding formal safety kernels and supervisory control.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5 font-mono text-xs">
          <button
            onClick={() => setIsFlowing(!isFlowing)}
            className={`px-3 py-1.5 rounded-lg border transition-all flex items-center gap-1.5 cursor-pointer ${
              isFlowing
                ? 'bg-[#45C982]/15 text-[#45C982] border-[#45C982]/30 shadow-sm shadow-[#45C982]/20'
                : 'bg-white/5 text-white/50 border-white/10 hover:text-white'
            }`}
          >
            <Zap className={`w-3.5 h-3.5 ${isFlowing ? 'text-[#45C982]' : ''}`} />
            <span>Data Stream {isFlowing ? 'ON' : 'PAUSED'}</span>
          </button>

          <button
            onClick={() => setAssemblyKey((k) => k + 1)}
            title="Replay flowchart box assembly animation"
            className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white/70 hover:text-white border border-white/10 transition-colors flex items-center gap-1.5 cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Replay</span> Assembly
          </button>
        </div>
      </div>

      {/* Main Flowchart Multi-Tier Assembly Grid */}
      <div className="relative z-10 grid grid-cols-1 md:grid-cols-4 gap-4 lg:gap-6 items-stretch">
        {/* Tier 1: Roadside Edge Sensors (4 Ingress Cameras) */}
        <div className="space-y-3">
          <div className="flex items-center justify-between pb-1">
            <span className="text-[10px] font-mono uppercase tracking-wider text-white/40">
              Tier 01 · Ingress Sensors
            </span>
            <span className="text-[10px] font-mono text-[#45C982] bg-[#45C982]/10 px-1.5 py-0.5 rounded border border-[#45C982]/20">
              4x Roadside
            </span>
          </div>

          {(['cam-j1', 'cam-j2', 'cam-j3', 'cam-j4'] as const).map((id) => {
            const node = nodes[id];
            const isSelected = selectedNode === id;
            return (
              <div
                key={id}
                onClick={() => setSelectedNode(id)}
                className={`flow-tier-1 p-3 rounded-xl border transition-all cursor-pointer group ${
                  isSelected
                    ? 'bg-[#111A1D] border-[#45C982] shadow-lg shadow-[#45C982]/15'
                    : 'bg-[#111A1D]/70 border-white/10 hover:border-white/20 hover:bg-[#111A1D]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded bg-[#080D10] border border-white/10 flex items-center justify-center">
                      {node.icon}
                    </div>
                    <div>
                      <h4 className="font-display font-semibold text-xs text-white group-hover:text-[#45C982] transition-colors">
                        {node.id.toUpperCase().replace('-', '_')}
                      </h4>
                      <span className="text-[10px] font-mono text-white/40 block">
                        {node.subtitle}
                      </span>
                    </div>
                  </div>
                  <span className="w-1.5 h-1.5 rounded-full bg-[#45C982] animate-pulse" />
                </div>
              </div>
            );
          })}
        </div>

        {/* Tier 2: Roadside Edge Perception Core */}
        <div className="space-y-3 flex flex-col justify-center">
          <div className="flex items-center justify-between pb-1">
            <span className="text-[10px] font-mono uppercase tracking-wider text-white/40">
              Tier 02 · Edge Processing
            </span>
            <span className="text-[10px] font-mono text-[#00E5FF] bg-[#00E5FF]/10 px-1.5 py-0.5 rounded border border-[#00E5FF]/20">
              YOLOv8 + EKF
            </span>
          </div>

          <div
            onClick={() => setSelectedNode('edge-perception')}
            className={`flow-tier-2 p-5 rounded-xl border transition-all cursor-pointer h-full flex flex-col justify-between group ${
              selectedNode === 'edge-perception'
                ? 'bg-[#111A1D] border-[#00E5FF] shadow-lg shadow-[#00E5FF]/15'
                : 'bg-[#111A1D]/80 border-white/10 hover:border-white/20 hover:bg-[#111A1D]'
            }`}
          >
            <div>
              <div className="w-10 h-10 rounded-lg bg-[#080D10] border border-[#00E5FF]/30 flex items-center justify-center mb-3">
                <Cpu className="w-5 h-5 text-[#00E5FF]" />
              </div>
              <h4 className="font-display font-bold text-sm text-white group-hover:text-[#00E5FF] transition-colors">
                Roadside Edge Perception Node
              </h4>
              <p className="text-xs text-white/60 mt-1.5 leading-relaxed">
                Aggregates 4 camera feeds at 1 FPS lockstep. Computes vehicle bounding boxes and bounded queue uncertainty intervals.
              </p>
            </div>

            <div className="mt-4 pt-3 border-t border-white/10 space-y-2 text-[11px] font-mono">
              <div className="flex items-center justify-between text-white/50">
                <span>Latency</span>
                <span className="text-[#00E5FF] font-semibold">&lt; 38ms</span>
              </div>
              <div className="flex items-center justify-between text-white/50">
                <span>Contract</span>
                <span className="text-white">LaneObservation</span>
              </div>
            </div>
          </div>
        </div>

        {/* Tier 3: Deterministic Phase Guard (The Invariant Safety Core) */}
        <div className="space-y-3 flex flex-col justify-center">
          <div className="flex items-center justify-between pb-1">
            <span className="text-[10px] font-mono uppercase tracking-wider text-[#45C982] font-semibold">
              Tier 03 · Mathematical Core
            </span>
            <span className="text-[10px] font-mono text-[#45C982] bg-[#45C982]/15 px-2 py-0.5 rounded border border-[#45C982]/30 animate-pulse">
              INVARIANT
            </span>
          </div>

          <div
            onClick={() => setSelectedNode('phase-guard')}
            className={`flow-tier-3 p-5 rounded-xl border transition-all cursor-pointer h-full flex flex-col justify-between group relative overflow-hidden ${
              selectedNode === 'phase-guard'
                ? 'bg-[#111A1D] border-[#45C982] shadow-2xl shadow-[#45C982]/20'
                : 'bg-[#111A1D]/90 border-white/15 hover:border-[#45C982]/50 hover:bg-[#111A1D]'
            }`}
          >
            {/* Subtle radial emerald flare inside Phase Guard */}
            <div className="absolute inset-0 bg-radial-gradient from-[#45C982]/10 via-transparent to-transparent pointer-events-none" />

            <div className="relative z-10">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#45C982]/20 to-[#45C982]/5 border border-[#45C982]/40 flex items-center justify-center mb-3.5 shadow-sm shadow-[#45C982]/20">
                <ShieldCheck className="w-6 h-6 text-[#45C982]" />
              </div>
              <h4 className="font-display font-bold text-base text-white group-hover:text-[#45C982] transition-colors">
                Deterministic Phase Guard
              </h4>
              <p className="text-xs text-white/70 mt-1.5 leading-relaxed">
                The unbypassable invariant gatekeeper. Evaluates signal transition matrices and forbids conflicting greens mathematically.
              </p>
            </div>

            <div className="relative z-10 mt-4 pt-3 border-t border-white/10 space-y-2 text-[11px] font-mono">
              <div className="flex items-center justify-between text-white/60">
                <span>Conflicting Greens</span>
                <span className="text-[#45C982] font-bold">0.00%</span>
              </div>
              <div className="flex items-center justify-between text-white/60">
                <span>State Ordering</span>
                <span className="text-white">Strict Monotonic</span>
              </div>
            </div>
          </div>
        </div>

        {/* Tier 4: Actuation & Supervisory Control (Signal, Console, Gemini) */}
        <div className="space-y-3">
          <div className="flex items-center justify-between pb-1">
            <span className="text-[10px] font-mono uppercase tracking-wider text-white/40">
              Tier 04 · Actuation &amp; Super-Cluster
            </span>
            <span className="text-[10px] font-mono text-[#E9A23B] bg-[#E9A23B]/10 px-1.5 py-0.5 rounded border border-[#E9A23B]/20">
              Commit &amp; Supervise
            </span>
          </div>

          {(['signal-actuator', 'operator-console', 'gemini-vision'] as const).map((id) => {
            const node = nodes[id];
            const isSelected = selectedNode === id;
            return (
              <div
                key={id}
                onClick={() => setSelectedNode(id)}
                className={`flow-tier-4 p-3.5 rounded-xl border transition-all cursor-pointer group ${
                  isSelected
                    ? 'bg-[#111A1D] border-[#45C982] shadow-lg shadow-[#45C982]/15'
                    : 'bg-[#111A1D]/70 border-white/10 hover:border-white/20 hover:bg-[#111A1D]'
                }`}
              >
                <div className="flex items-start gap-2.5">
                  <div className="w-8 h-8 rounded bg-[#080D10] border border-white/10 flex items-center justify-center shrink-0 mt-0.5">
                    {node.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-display font-semibold text-xs text-white group-hover:text-[#45C982] transition-colors truncate">
                      {node.title}
                    </h4>
                    <span className="text-[10px] font-mono text-white/40 block truncate">
                      {node.subtitle}
                    </span>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-white/5 border border-white/10 text-white/60">
                        {node.badge}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Animated Flow Cable Canvas / SVG Beams */}
      <div className="relative z-10 my-6 py-2 px-4 rounded-xl bg-[#080D10] border border-white/10 flex items-center justify-between text-xs font-mono flow-cable-svg">
        <div className="flex items-center gap-2 text-white/70">
          <Activity className="w-4 h-4 text-[#45C982]" />
          <span>REAL-TIME PIPELINE ACTIVITY:</span>
        </div>

        <div className="flex items-center gap-4 text-white/50 text-[11px]">
          <span className="flex items-center gap-1.5">
            <span className={`w-1.5 h-1.5 rounded-full ${isFlowing ? 'bg-[#45C982] animate-ping' : 'bg-white/20'}`} />
            Sensors &rarr; Edge Perception (1 FPS)
          </span>
          <span className="hidden sm:inline text-white/20">&bull;</span>
          <span className="hidden sm:flex items-center gap-1.5">
            <span className={`w-1.5 h-1.5 rounded-full ${isFlowing ? 'bg-[#00E5FF] animate-ping' : 'bg-white/20'}`} />
            Perception &rarr; Phase Guard (&lt;40ms)
          </span>
          <span className="hidden sm:inline text-white/20">&bull;</span>
          <span className="flex items-center gap-1.5">
            <span className={`w-1.5 h-1.5 rounded-full ${isFlowing ? 'bg-[#E9A23B] animate-ping' : 'bg-white/20'}`} />
            Phase Guard &rarr; Actuator (Idempotent)
          </span>
        </div>
      </div>

      {/* Selected Node Detailed Contract Inspector Drawer */}
      <div className="relative z-10 rounded-xl bg-[#111A1D] border border-white/10 p-5 mt-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-white/10 gap-2 mb-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-[#080D10] border border-white/15 flex items-center justify-center text-white">
              {active.icon}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h4 className="font-display font-bold text-sm text-white">{active.title}</h4>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#45C982]/10 border border-[#45C982]/30 text-[#45C982]">
                  {active.status}
                </span>
              </div>
              <p className="text-xs text-white/50">{active.subtitle}</p>
            </div>
          </div>

          <div className="text-xs font-mono text-white/40 self-start sm:self-auto">
            Contract: <span className="text-white/80">{active.contract}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {active.specs.map((s) => (
            <div key={s.label} className="p-3 rounded-lg bg-[#080D10] border border-white/5 space-y-1">
              <span className="text-[10px] font-mono uppercase tracking-wider text-white/40 block">
                {s.label}
              </span>
              <span className="text-xs font-mono font-semibold text-white block">{s.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
