import React from 'react';
import { Camera, CameraOff } from 'lucide-react';
import { JunctionData } from '../../types/api';
import { Badge } from '../common/Badge';

interface JunctionCardProps {
  junction: JunctionData;
  isStale?: boolean;
}

export const JunctionCard: React.FC<JunctionCardProps> = ({
  junction,
  isStale = false,
}) => {
  const isCameraMissing = junction.camera_status === 'MISSING';
  const queueAvailable = junction.estimated_queue !== null && junction.queue_interval !== null;
  const [lowerInterval, upperInterval] = junction.queue_interval ?? [0, 0];

  return (
    <article
      className={`bg-white border rounded p-4 flex flex-col justify-between transition-colors ${
        isStale
          ? 'border-[#E5E5E5] opacity-75'
          : isCameraMissing
          ? 'border-[#FDE68A] bg-[#FFFEFA]'
          : 'border-[#E5E5E5]'
      }`}
    >
      {/* Top Header: ID & Camera Status */}
      <div>
        <div className="flex items-start justify-between gap-2 pb-3 border-b border-[#E5E5E5]">
          <div>
            <div className="flex items-baseline gap-2">
              <span className="text-base font-bold text-[#171717] tracking-tight">
                Intersection {junction.junction_id}
              </span>
            </div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="text-xs text-[#737373]">Signal Phase:</span>
              <span className="text-xs font-mono font-medium text-[#23865A]">
                {junction.phase}
              </span>
            </div>
          </div>

          <div>
            {isCameraMissing ? (
              <Badge variant="warning" className="gap-1">
                <CameraOff className="w-3 h-3" />
                <span>Dropout</span>
              </Badge>
            ) : (
              <Badge variant="success" className="gap-1">
                <Camera className="w-3 h-3" />
                <span>Available</span>
              </Badge>
            )}
          </div>
        </div>

        {/* Telemetry Metrics List (Clean whitespace & typography, no mini-boxes) */}
        <div className="py-3 space-y-2.5 text-xs">
          {/* Observed Count */}
          <div className="flex items-center justify-between">
            <span className="text-[#737373]">Observed Vehicle Count</span>
            <div>
              {junction.observed_count === null ? (
                <span className="text-[#B7791F] font-medium font-mono">
                  null <span className="font-sans text-[11px] text-[#737373]">(missing)</span>
                </span>
              ) : (
                <span className="font-semibold text-[#171717] font-mono">
                  {junction.observed_count}{' '}
                  <span className="font-sans font-normal text-[#737373]">veh</span>
                </span>
              )}
            </div>
          </div>

          {/* Estimated Queue */}
          <div className="flex items-center justify-between">
            <span className="text-[#737373]">Estimated Queue</span>
            <span className="font-semibold text-[#737373] font-mono">
              {queueAvailable ? `${junction.estimated_queue!.toFixed(1)} veh` : 'not published'}
            </span>
          </div>

          {/* Uncertainty Interval */}
          <div className="flex items-center justify-between">
            <span className="text-[#737373]">Queue Interval (CI)</span>
            <div className="flex items-center gap-1">
              <span className={`font-mono font-medium ${isCameraMissing ? 'text-[#B7791F]' : 'text-[#171717]'}`}>
                {queueAvailable ? `[${lowerInterval.toFixed(0)}, ${upperInterval.toFixed(0)}] veh` : 'not published'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Footer: Provenance & Data Quality */}
      <div className="pt-2.5 border-t border-[#E5E5E5] flex items-center justify-between text-[11px] text-[#737373]">
        <span>Source: {junction.source}</span>
        <span className="capitalize">{junction.data_quality}</span>
      </div>
    </article>
  );
};
