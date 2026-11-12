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
  const [lowerInterval, upperInterval] = junction.queue_interval;

  return (
    <article
      className={`bg-[#111A1D] border rounded-lg p-4 flex flex-col justify-between transition-colors shadow-sm ${
        isStale
          ? 'border-white/10 opacity-75'
          : isCameraMissing
          ? 'border-[#E9A23B]/40 bg-[#161C1D]'
          : 'border-white/10'
      }`}
    >
      {/* Top Header: ID & Camera Status */}
      <div>
        <div className="flex items-start justify-between gap-2 pb-3 border-b border-white/10">
          <div>
            <div className="flex items-baseline gap-2">
              <span className="text-base font-display font-bold text-white tracking-tight">
                Intersection {junction.junction_id}
              </span>
            </div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="text-xs text-white/50">Phase:</span>
              <span className="text-xs font-mono font-medium text-[#45C982]">
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

        {/* Telemetry Metrics List */}
        <div className="py-3 space-y-2.5 text-xs">
          {/* Observed Count */}
          <div className="flex items-center justify-between">
            <span className="text-white/50">Observed Vehicles</span>
            <div>
              {junction.observed_count === null ? (
                <span className="text-[#E9A23B] font-medium font-mono">
                  null <span className="font-sans text-[11px] text-white/40">(missing)</span>
                </span>
              ) : (
                <span className="font-semibold text-white font-mono">
                  {junction.observed_count}{' '}
                  <span className="font-sans font-normal text-white/40">veh</span>
                </span>
              )}
            </div>
          </div>

          {/* Estimated Queue */}
          <div className="flex items-center justify-between">
            <span className="text-white/50">Estimated Queue</span>
            <span className="font-semibold text-white font-mono">
              {junction.estimated_queue.toFixed(1)}{' '}
              <span className="font-sans font-normal text-white/40">veh</span>
            </span>
          </div>

          {/* Uncertainty Interval */}
          <div className="flex items-center justify-between">
            <span className="text-white/50">Queue Interval (CI)</span>
            <div className="flex items-center gap-1 font-mono">
              <span className={`font-medium ${isCameraMissing ? 'text-[#E9A23B]' : 'text-[#45C982]'}`}>
                [{lowerInterval.toFixed(0)}, {upperInterval.toFixed(0)}]
              </span>
              <span className="text-white/40 font-sans">veh</span>
            </div>
          </div>
        </div>
      </div>

      {/* Footer / Quality Meta */}
      <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[11px] font-mono text-white/30">
        <span>Source: {junction.source}</span>
        <span>Quality: {junction.data_quality}</span>
      </div>
    </article>
  );
};
