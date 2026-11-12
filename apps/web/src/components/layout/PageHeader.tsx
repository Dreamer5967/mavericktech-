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
    <div className="space-y-4 pt-6 pb-2 border-b border-[#E5E5E5]">
      {/* Title & Top Metadata Row */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[#171717]">
            Operations Overview
          </h1>
          <p className="text-sm text-[#737373] mt-0.5">
            Monitor traffic conditions and system readiness across all four intersections.
          </p>
        </div>

        {/* Status Actions Strip */}
        <div className="flex items-center flex-wrap gap-2.5 sm:gap-3 text-xs">
          {/* Mode Badge */}
          <div className="flex items-center gap-1.5">
            <span className="text-[#737373]">Mode:</span>
            <Badge variant={isMock ? 'warning' : 'success'}>
              {mode}
            </Badge>
          </div>

          <div className="h-4 w-px bg-[#E5E5E5] hidden sm:block" />

          {/* Connection Indicator */}
          <div className="flex items-center gap-1.5">
            <span className="text-[#737373]">Link:</span>
            <StatusIndicator status={connectionStatus} />
          </div>

          <div className="h-4 w-px bg-[#E5E5E5] hidden sm:block" />

          {/* Freshness */}
          <div className="flex items-center gap-1 text-[#737373]">
            <span>Updated:</span>
            <span className="font-medium text-[#262626]">
              {secondsSinceLastUpdate === null ? 'Connecting...' : `${secondsSinceLastUpdate}s ago`}
            </span>
          </div>

          {/* Refresh Button */}
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isFetching}
              title="Manual Snapshot Fetch"
              className="p-1.5 rounded border border-[#E5E5E5] hover:bg-[#F5F5F5] text-[#737373] hover:text-[#171717] transition-colors disabled:opacity-50 ml-1"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin text-[#171717]' : ''}`} />
            </button>
          )}
        </div>
      </div>

      {/* MOCK Banner */}
      {isMock && (
        <div className="rounded border border-[#FDE68A] bg-[#FFFBEB] px-3.5 py-2.5 text-xs text-[#92400E] flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 text-[#B7791F] shrink-0 mt-0.5" />
          <div className="flex-1 leading-relaxed">
            <span className="font-semibold text-[#B7791F]">MOCK MODE ACTIVE — </span>
            <span>{notice || 'Development fixtures only. No CARLA, YOLO, or trained MARL policies are active.'}</span>
          </div>
        </div>
      )}

      {/* Disconnection Warning */}
      {connectionStatus === 'DISCONNECTED' && (
        <div className="rounded border border-[#FECACA] bg-[#FDF2F2] px-3.5 py-2.5 text-xs text-[#991B1B] flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 text-[#C0392B] shrink-0 mt-0.5" />
          <div className="flex-1 leading-relaxed">
            <span className="font-semibold text-[#C0392B]">Backend Connection Disconnected: </span>
            <span>Cannot reach the P2 observation feed on http://127.0.0.1:8765. Data displayed below is frozen or cached.</span>
          </div>
        </div>
      )}
    </div>
  );
};
