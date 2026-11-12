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
        <div className="h-4 w-40 bg-[#F5F5F5] rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="h-48 rounded border border-[#E5E5E5] bg-[#F5F5F5] p-4 animate-pulse"
            />
          ))}
        </div>
      </section>
    );
  }

  if (junctions.length === 0) {
    return (
      <section className="rounded border border-[#E5E5E5] bg-[#F5F5F5] p-8 text-center text-xs text-[#737373]">
        <p className="font-medium text-[#171717]">No active intersections found.</p>
        <p className="mt-1">Waiting for observation snapshot from the backend.</p>
      </section>
    );
  }

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold tracking-tight text-[#171717]">
          Intersection Monitoring ({junctions.length})
        </h2>
        {isStale && (
          <span className="text-xs text-[#B7791F] bg-[#FFFBEB] border border-[#FDE68A] px-2 py-0.5 rounded">
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
