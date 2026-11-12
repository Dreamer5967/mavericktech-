import React, { useState } from 'react';
import { VideoOff, Info } from 'lucide-react';
import { JunctionData } from '../../types/api';
import { Badge } from '../common/Badge';

interface CameraViewerProps {
  junctions?: JunctionData[];
}

export const CameraViewer: React.FC<CameraViewerProps> = ({ junctions = [] }) => {
  const [selectedJunctionId, setSelectedJunctionId] = useState<string>('J1');

  const selectedJunction = junctions.find((j) => j.junction_id === selectedJunctionId);
  const isCameraMissing = selectedJunction?.camera_status === 'MISSING';

  return (
    <section className="bg-[#111A1D] border border-white/10 rounded-lg p-4 sm:p-5 space-y-4 shadow-sm">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-white/10">
        <div>
          <h2 className="text-sm font-display font-semibold tracking-tight text-white">
            Camera Inspection
          </h2>
          <p className="text-xs text-white/50 mt-0.5">
            Roadside sensor feeds and ingress frame monitoring.
          </p>
        </div>

        {/* Junction Selector */}
        <div className="flex items-center gap-1.5 font-mono text-xs">
          <span className="text-white/40 mr-1 font-sans">Intersection:</span>
          <div className="inline-flex rounded border border-white/10 bg-[#080D10] p-0.5">
            {['J1', 'J2', 'J3', 'J4'].map((id) => {
              const jData = junctions.find((item) => item.junction_id === id);
              const isMissing = jData?.camera_status === 'MISSING';
              const isSelected = selectedJunctionId === id;
              return (
                <button
                  key={id}
                  onClick={() => setSelectedJunctionId(id)}
                  className={`px-3 py-1 rounded text-xs font-mono font-medium transition-colors flex items-center gap-1.5 cursor-pointer ${
                    isSelected
                      ? 'bg-white/15 text-white shadow-sm font-bold border border-white/20'
                      : 'text-white/60 hover:text-white'
                  }`}
                >
                  <span>{id}</span>
                  {isMissing && <span className="w-1.5 h-1.5 rounded-full bg-[#E9A23B]" />}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Frame Container & Placeholder */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Visual Frame Area */}
        <div className="lg:col-span-3 rounded-lg border border-dashed border-white/15 bg-[#080D10] min-h-[260px] flex flex-col items-center justify-center p-6 text-center relative overflow-hidden">
          {/* Subtle radar / grid background pattern */}
          <div className="absolute inset-0 bg-[radial-gradient(#45C982_1px,transparent_1px)] [background-size:24px_24px] opacity-10 pointer-events-none" />

          <div className="relative z-10 w-12 h-12 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-white/60 mb-3 shadow-inner">
            <VideoOff className="w-6 h-6" />
          </div>
          <h3 className="relative z-10 text-xs font-mono font-semibold text-white uppercase tracking-wider">
            Real-Time Frame Stream Pending (P2 Integration)
          </h3>
          <p className="relative z-10 text-xs text-white/50 max-w-md mt-1.5 leading-relaxed">
            The local mock server does not publish live CARLA RGB frame buffers.
            In accordance with AEGIS engineering principles, synthetic feeds or stock footage are withheld to prevent false live representations.
          </p>
        </div>

        {/* Selected Camera Metadata Column */}
        <div className="rounded-lg border border-white/10 bg-[#080D10] p-4 flex flex-col justify-between text-xs space-y-3 font-mono">
          <div className="space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-white/10">
              <span className="text-white/50 font-sans">Camera Target</span>
              <span className="font-semibold text-white">
                cam_{selectedJunctionId.toLowerCase()}_roadside
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-white/50 font-sans">Perception State</span>
              <Badge variant={isCameraMissing ? 'warning' : 'success'}>
                {selectedJunction?.camera_status ?? 'Unknown'}
              </Badge>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-white/50 font-sans">Target Resolution</span>
              <span className="text-white/80">1920 × 1080</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-white/50 font-sans">Capture Rate</span>
              <span className="text-white/80">1 FPS RGB</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-white/50 font-sans">Endpoint Hook</span>
              <span className="text-[11px] text-[#45C982]">
                /api/v1/frames/{selectedJunctionId}
              </span>
            </div>
          </div>

          <div className="pt-2 border-t border-white/10 flex items-start gap-1.5 text-[11px] text-white/40 font-sans">
            <Info className="w-3.5 h-3.5 text-[#45C982] shrink-0 mt-0.5" />
            <span>Telemetry reflects active roadside contract state.</span>
          </div>
        </div>
      </div>
    </section>
  );
};
