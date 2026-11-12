import React from 'react';
import { ConnectionStatus, SnapshotResponse } from '../../types/api';

interface ReadinessPanelProps {
  snapshot?: SnapshotResponse;
  connectionStatus: ConnectionStatus;
}

export const ReadinessPanel: React.FC<ReadinessPanelProps> = ({
  snapshot,
  connectionStatus,
}) => {
  const items = [
    {
      label: 'Backend Status',
      value: connectionStatus === 'CONNECTED' ? 'Operational' : connectionStatus,
      highlight: connectionStatus === 'CONNECTED' ? 'text-[#23865A]' : 'text-[#C0392B]',
    },
    {
      label: 'Operating Mode',
      value: snapshot?.mode ?? 'Offline',
      meta: snapshot?.schema_version ? `v${snapshot.schema_version}` : undefined,
    },
    {
      label: 'Simulation Time',
      value: snapshot?.sim_time_s !== undefined ? `${snapshot.sim_time_s.toFixed(1)}s` : '—',
      mono: true,
    },
    {
      label: 'State Revision',
      value: snapshot?.state_revision !== undefined ? `#${snapshot.state_revision}` : '—',
      mono: true,
    },
    {
      label: 'Run Identifier',
      value: snapshot?.run_id ?? '—',
      mono: true,
    },
    {
      label: 'Intersections',
      value: snapshot?.junctions ? `${snapshot.junctions.length} Active` : '—',
    },
  ];

  return (
    <section className="bg-[#F5F5F5] border border-[#E5E5E5] rounded p-4">
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 divide-y sm:divide-y-0 sm:divide-x divide-[#E5E5E5]">
        {items.map((item, idx) => (
          <div key={item.label} className={`flex flex-col justify-center ${idx > 0 ? 'sm:pl-4 pt-2 sm:pt-0' : ''}`}>
            <span className="text-xs text-[#737373] font-normal">{item.label}</span>
            <div className="flex items-baseline gap-1 mt-0.5">
              <span className={`text-sm font-semibold tracking-tight ${item.highlight || 'text-[#171717]'} ${item.mono ? 'font-mono' : ''}`}>
                {item.value}
              </span>
              {item.meta && (
                <span className="text-[11px] text-[#737373] font-mono">({item.meta})</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};
