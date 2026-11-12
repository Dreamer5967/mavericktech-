import React from 'react';
import { JunctionData } from '../../types/api';
import { JunctionCard } from './JunctionCard';

interface JunctionGridProps {
  junctions?: JunctionData[];
  isLoading?: boolean;
  isStale?: boolean;
}

export const JunctionGrid: React.FC<JunctionGridProps> = ({
  junctions = [],
  isLoading = false,
  isStale = false,
}) => {
  if (isLoading) {
    return (
      <section className="space-y-3">
        <div className="h-4 w-40 bg-white/5 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="h-48 rounded-lg border border-white/10 bg-[#111A1D] p-4 animate-pulse"
            />
          ))}
        </div>
      </section>
    );
  }

  if (junctions.length === 0) {
    return (
      <section className="rounded-lg border border-white/10 bg-[#111A1D] p-8 text-center text-xs text-white/50">
        <p className="font-medium text-white font-mono">No active intersections found.</p>
        <p className="mt-1">Waiting for observation snapshot from the backend.</p>
      </section>
    );
  }

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-display font-semibold tracking-tight text-white">
          Intersection Telemetry ({junctions.length})
        </h2>
        {isStale && (
          <span className="text-xs font-mono text-[#E9A23B] bg-[#E9A23B]/10 border border-[#E9A23B]/25 px-2 py-0.5 rounded">
            Displaying cached state
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {junctions.map((junction) => (
          <JunctionCard
            key={junction.junction_id}
            junction={junction}
            isStale={isStale}
          />
        ))}
      </div>
    </section>
  );
};
