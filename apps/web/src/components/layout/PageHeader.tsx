import React from 'react';
import { RefreshCw, AlertCircle } from 'lucide-react';
import { ConnectionStatus, OperatingMode } from '../../types/api';
import { StatusIndicator } from '../common/StatusIndicator';
import { Badge } from '../common/Badge';

interface PageHeaderProps {
  mode?: OperatingMode;
  connectionStatus: ConnectionStatus;
  secondsSinceLastUpdate: number | null;
  onRefresh?: () => void;
  isFetching?: boolean;
  notice?: string;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  mode = 'UNKNOWN',
  connectionStatus,
  secondsSinceLastUpdate,
  onRefresh,
  isFetching = false,
  notice,
}) => {
  const isMock = mode?.toUpperCase() === 'MOCK';

  return (
    <div className="space-y-4 pt-6 pb-2 border-b border-white/10">
      {/* Title & Top Metadata Row */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-display font-bold tracking-tight text-white">
            Operations Overview
          </h1>
          <p className="text-xs sm:text-sm text-white/60 mt-0.5">
            Monitor real-time intersection telemetry, camera ingestion, and incident controls.
          </p>
        </div>

        {/* Status Actions Strip */}
        <div className="flex items-center flex-wrap gap-2.5 sm:gap-3 text-xs font-mono">
          {/* Mode Badge */}
          <div className="flex items-center gap-1.5">
            <span className="text-white/40">Mode:</span>
            <Badge variant={isMock ? 'warning' : 'success'}>
              {mode}
            </Badge>
          </div>

          <div className="h-4 w-px bg-white/10 hidden sm:block" />

          {/* Connection Indicator */}
          <div className="flex items-center gap-1.5">
            <span className="text-white/40">Link:</span>
            <StatusIndicator status={connectionStatus} />
          </div>

          <div className="h-4 w-px bg-white/10 hidden sm:block" />

          {/* Freshness */}
          <div className="flex items-center gap-1 text-white/50">
            <span>Updated:</span>
            <span className="font-medium text-white/90">
              {secondsSinceLastUpdate === null ? 'Connecting...' : `${secondsSinceLastUpdate}s ago`}
            </span>
          </div>

          {/* Refresh Button */}
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isFetching}
              title="Manual Snapshot Fetch"
              className="p-1.5 rounded border border-white/15 bg-white/5 hover:bg-white/10 text-white/70 hover:text-white transition-colors disabled:opacity-50 ml-1 cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin text-[#45C982]' : ''}`} />
            </button>
          )}
        </div>
      </div>

      {/* Fixture / Mock Notice Banner */}
      {notice && (
        <div className="rounded border border-[#E9A23B]/30 bg-[#E9A23B]/10 p-3 text-xs text-[#E9A23B] flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-[#E9A23B]" />
          <div className="leading-relaxed">
            <span className="font-semibold uppercase tracking-wider text-[11px] block font-mono">
              Notice:
            </span>
            <p className="mt-0.5 text-white/80">{notice}</p>
          </div>
        </div>
      )}
    </div>
  );
};
