import React from 'react';
import { History, Trash2, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { IncidentLogEntry } from '../../types/api';
import { Badge } from '../common/Badge';

interface IncidentHistoryLogProps {
  logs: IncidentLogEntry[];
  onClear: () => void;
}

export const IncidentHistoryLog: React.FC<IncidentHistoryLogProps> = ({ logs, onClear }) => {
  return (
    <section className="bg-[#111A1D] border border-white/10 rounded-lg p-4 sm:p-5 space-y-4 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-white/10">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-[#45C982]" />
          <h2 className="text-sm font-display font-semibold tracking-tight text-white">
            Incident Action History & Idempotency Audit
          </h2>
          <Badge variant="outline" className="text-[10px]">
            {logs.length} logged
          </Badge>
        </div>

        {logs.length > 0 && (
          <button
            onClick={onClear}
            className="text-xs font-mono text-white/50 hover:text-white flex items-center gap-1 transition-colors cursor-pointer"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear Log</span>
          </button>
        )}
      </div>

      {/* Log Table / List */}
      {logs.length === 0 ? (
        <div className="py-8 text-center text-xs text-white/40 font-mono">
          <Clock className="w-6 h-6 mx-auto mb-2 text-white/30" />
          <p className="font-medium text-white/70">No incidents recorded this session.</p>
          <p className="mt-0.5 text-white/40">Actions triggered in the control panel will appear here with idempotency tracking.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-white/10 text-white/40 text-[11px] uppercase tracking-wider">
                <th className="pb-2 font-normal">Timestamp</th>
                <th className="pb-2 font-normal">Target</th>
                <th className="pb-2 font-normal">Action Type</th>
                <th className="pb-2 font-normal">Request ID</th>
                <th className="pb-2 font-normal">Status</th>
                <th className="pb-2 font-normal text-right">Confirmed Revision</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {logs.map((entry) => {
                const isSuccess = entry.status === 'APPLIED';
                const isError = entry.status === 'REJECTED';

                return (
                  <tr key={entry.id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-2.5 text-white/50 whitespace-nowrap">
                      {entry.timestamp}
                    </td>
                    <td className="py-2.5 font-semibold text-white">
                      {entry.junction_id ? `Intersection ${entry.junction_id}` : 'All'}
                    </td>
                    <td className="py-2.5 text-white/80">
                      {entry.type === 'FAULT_INJECTION' && 'Camera Dropout'}
                      {entry.type === 'FAULT_CLEAR' && 'Camera Restoration'}
                      {entry.type === 'SCENARIO_RESET' && 'Scenario Reset'}
                    </td>
                    <td className="py-2.5 text-[11px] text-white/50 max-w-[140px] truncate" title={entry.request_id}>
                      {entry.request_id}
                    </td>
                    <td className="py-2.5">
                      {isSuccess && (
                        <Badge variant="success" className="gap-1 text-[10px]">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>Applied</span>
                        </Badge>
                      )}
                      {isError && (
                        <Badge variant="danger" className="gap-1 text-[10px]">
                          <XCircle className="w-3 h-3" />
                          <span>Rejected</span>
                        </Badge>
                      )}
                      {!isSuccess && !isError && (
                        <Badge variant="neutral" className="gap-1 text-[10px]">
                          <span>Pending</span>
                        </Badge>
                      )}
                    </td>
                    <td className="py-2.5 text-right font-mono text-[#45C982]">
                      {entry.state_revision !== undefined ? `#${entry.state_revision}` : '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
};
