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
    <section className="bg-white border border-[#E5E5E5] rounded p-4 space-y-4">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#E5E5E5]">
        <div>
          <h2 className="text-sm font-semibold tracking-tight text-[#171717]">
            Camera Inspection
          </h2>
          <p className="text-xs text-[#737373] mt-0.5">
            Roadside sensor feeds and ingress frame monitoring.
          </p>
        </div>

        {/* Junction Selector */}
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-[#737373] mr-1">Intersection:</span>
          <div className="inline-flex rounded border border-[#E5E5E5] bg-[#F5F5F5] p-0.5">
            {['J1', 'J2', 'J3', 'J4'].map((id) => {
              const jData = junctions.find((item) => item.junction_id === id);
              const isMissing = jData?.camera_status === 'MISSING';
              const isSelected = selectedJunctionId === id;
              return (
                <button
                  key={id}
                  onClick={() => setSelectedJunctionId(id)}
                  className={`px-3 py-1 rounded text-xs font-medium transition-colors flex items-center gap-1.5 ${
                    isSelected
                      ? 'bg-white text-[#171717] shadow-sm font-semibold'
                      : 'text-[#737373] hover:text-[#171717]'
                  }`}
                >
                  <span>{id}</span>
                  {isMissing && <span className="w-1.5 h-1.5 rounded-full bg-[#B7791F]" />}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Frame Container & Placeholder */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Visual Frame Area */}
        <div className="lg:col-span-3 rounded border border-dashed border-[#E5E5E5] bg-[#F5F5F5] min-h-[260px] flex flex-col items-center justify-center p-6 text-center">
          <div className="w-10 h-10 rounded-full bg-white border border-[#E5E5E5] flex items-center justify-center text-[#737373] mb-3">
            <VideoOff className="w-5 h-5" />
          </div>
          <h3 className="text-xs font-semibold text-[#171717]">
            Real-Time Frame Stream Pending (P2 Integration)
          </h3>
          <p className="text-xs text-[#737373] max-w-md mt-1 leading-relaxed">
            The local mock server does not publish live CARLA RGB frame buffers.
            In accordance with AEGIS engineering principles, synthetic feeds or stock footage are withheld to prevent false live representations.
          </p>
        </div>

        {/* Selected Camera Metadata Column */}
        <div className="rounded border border-[#E5E5E5] bg-[#FAFAFA] p-3.5 flex flex-col justify-between text-xs space-y-3">
          <div className="space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-[#E5E5E5]">
              <span className="text-[#737373]">Camera Target</span>
              <span className="font-mono font-semibold text-[#171717]">
                cam_{selectedJunctionId.toLowerCase()}_roadside
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-[#737373]">Perception State</span>
              <Badge variant={isCameraMissing ? 'warning' : 'success'}>
                {selectedJunction?.camera_status ?? 'Unknown'}
              </Badge>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-[#737373]">Target Resolution</span>
              <span className="font-mono text-[#262626]">1920 × 1080</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-[#737373]">Capture Rate</span>
              <span className="font-mono text-[#262626]">1 FPS RGB</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-[#737373]">Endpoint Hook</span>
              <span className="font-mono text-[11px] text-[#737373]">/api/v1/frames/&#123;id&#125;</span>
            </div>
          </div>

          <div className="pt-2 border-t border-[#E5E5E5] text-[11px] text-[#737373] flex items-start gap-1.5">
            <Info className="w-3.5 h-3.5 text-[#737373] shrink-0 mt-0.5" />
            <span>Bound automatically once P2 roadside worker publishes JPEG artifacts.</span>
          </div>
        </div>
      </div>
    </section>
  );
};
