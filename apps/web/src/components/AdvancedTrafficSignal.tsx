import React, { useState } from 'react';
import { ShieldCheck, CheckCircle2 } from 'lucide-react';

interface SystemTelemetryProps {
  scrollProgress?: number;
}

export const AdvancedTrafficSignal: React.FC<SystemTelemetryProps> = () => {
  const [activeTab, setActiveTab] = useState<'junctions' | 'mappo' | 'guard'>('junctions');

  const junctions = [
    { id: 'J1', name: 'Downtown North', lanes: 6, phase: 'Phase 0 (Green)', status: 'Flowing', queue: 14, wait: '11.8s', color: 'emerald' },
    { id: 'J2', name: 'Commercial Hub', lanes: 6, phase: 'Phase 3 (Yellow)', status: 'Clearing', queue: 8, wait: '16.4s', color: 'amber' },
    { id: 'J3', name: 'East Corridor', lanes: 8, phase: 'Phase 6 (Red)', status: 'Holding', queue: 24, wait: '32.1s', color: 'rose' },
    { id: 'J4', name: 'Tech Boulevard', lanes: 4, phase: 'Phase 0 (Green)', status: 'Flowing', queue: 5, wait: '7.9s', color: 'emerald' },
  ];

  return (
    <div className="w-full max-w-xl mx-auto rounded-xl bg-white border border-slate-200 shadow-xl shadow-slate-200/50 p-6 relative">
      {/* Top Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-orange-500 animate-pulse" />
          <span className="font-mono text-xs font-semibold text-slate-800 uppercase tracking-wider">
            Controller Telemetry · MAPPO v2
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-[11px] font-mono px-2 py-0.5 rounded bg-slate-50 text-slate-600 border border-slate-200">
          <span>Inference: 14ms</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 my-4">
        {(['junctions', 'mappo', 'guard'] as const).map((tab) => {
          const labels = {
            junctions: 'Junction Grid',
            mappo: 'MAPPO Policy',
            guard: 'Phase Guard Safety',
          };
          return (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`
                px-3 py-1.5 rounded-lg text-xs font-medium transition-all
                ${
                  activeTab === tab
                    ? 'bg-orange-500 text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }
              `}
            >
              {labels[tab]}
            </button>
          );
        })}
      </div>

      {/* Tab 1: Junctions */}
      {activeTab === 'junctions' && (
        <div className="grid grid-cols-2 gap-3">
          {junctions.map((j) => {
            const isGreen = j.color === 'emerald';
            const isYellow = j.color === 'amber';
            const isRed = j.color === 'rose';

            return (
              <div
                key={j.id}
                className="p-3.5 rounded-lg bg-slate-50/80 border border-slate-200 hover:border-orange-300 transition"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-1.5">
                    <span className="font-mono text-xs font-bold text-slate-900">{j.id}</span>
                    <span className="text-[10px] text-slate-400 font-mono">({j.lanes} lanes)</span>
                  </div>
                  <span
                    className={`
                      text-[10px] font-medium font-mono px-1.5 py-0.5 rounded border
                      ${
                        isGreen
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : isYellow
                          ? 'bg-amber-50 text-amber-700 border-amber-200'
                          : 'bg-rose-50 text-rose-700 border-rose-200'
                      }
                    `}
                  >
                    {j.status}
                  </span>
                </div>

                <div className="text-[11px] text-slate-500 mb-2 truncate">{j.name}</div>

                {/* Status Indicator */}
                <div className="flex items-center justify-between bg-white px-2.5 py-1.5 rounded border border-slate-200 mb-2">
                  <div className="flex items-center gap-1.5">
                    <span
                      className={`w-2.5 h-2.5 rounded-full ${
                        isRed ? 'bg-rose-500 shadow-sm shadow-rose-500/50' : 'bg-slate-200'
                      }`}
                    />
                    <span
                      className={`w-2.5 h-2.5 rounded-full ${
                        isYellow ? 'bg-amber-400 shadow-sm shadow-amber-400/50' : 'bg-slate-200'
                      }`}
                    />
                    <span
                      className={`w-2.5 h-2.5 rounded-full ${
                        isGreen ? 'bg-emerald-500 shadow-sm shadow-emerald-500/50' : 'bg-slate-200'
                      }`}
                    />
                  </div>
                  <span className="font-mono text-[11px] font-medium text-slate-700">{j.phase}</span>
                </div>

                <div className="flex items-center justify-between text-[11px] font-mono text-slate-500">
                  <span>Q: {j.queue} veh</span>
                  <span>Wait: {j.wait}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Tab 2: MAPPO Specs */}
      {activeTab === 'mappo' && (
        <div className="space-y-2.5 font-mono text-xs text-slate-700">
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex justify-between items-center">
            <span className="text-slate-500">Topology:</span>
            <span className="font-semibold text-slate-900">Decentralized Actors / Centralized Critic</span>
          </div>
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex justify-between items-center">
            <span className="text-slate-500">Action Space:</span>
            <span className="font-semibold text-orange-600">Discrete SUMO Phases [0, 3, 6]</span>
          </div>
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex justify-between items-center">
            <span className="text-slate-500">Dropout Resilience:</span>
            <span className="font-semibold text-emerald-700">0% – 40% Frame Loss Verified</span>
          </div>
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex justify-between items-center">
            <span className="text-slate-500">Belief Estimation:</span>
            <span className="font-semibold text-slate-900">Kalman Queue Uncertainty Mask</span>
          </div>
        </div>
      )}

      {/* Tab 3: Phase Guard */}
      {activeTab === 'guard' && (
        <div className="space-y-2.5 font-mono text-xs text-slate-700">
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex justify-between items-center">
            <span className="text-slate-500 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              Hardware Actuation Gate:
            </span>
            <span className="font-semibold text-emerald-700">ACTIVE &amp; ENFORCED</span>
          </div>
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex justify-between items-center">
            <span className="text-slate-500">Min-Green Floor:</span>
            <span className="font-semibold text-slate-900">10.0s (Cannot be truncated)</span>
          </div>
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex justify-between items-center">
            <span className="text-slate-500">Yellow Transition:</span>
            <span className="font-semibold text-slate-900">3.0s Clearance Enforced</span>
          </div>
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex justify-between items-center">
            <span className="text-slate-500">All-Red Safety Buffer:</span>
            <span className="font-semibold text-slate-900">2.0s Clearance Interlock</span>
          </div>
        </div>
      )}

      {/* Footer System Hash */}
      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] font-mono text-slate-400">
        <span className="flex items-center gap-1.5">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
          <span>Network SHA: 3ef9501d...</span>
        </span>
        <span className="text-orange-600 font-medium">Phase Guard Verified</span>
      </div>
    </div>
  );
};
