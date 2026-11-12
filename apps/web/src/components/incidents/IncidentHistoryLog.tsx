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
    <section className="bg-white border border-[#E5E5E5] rounded p-4 sm:p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E5]">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-[#737373]" />
          <h2 className="text-sm font-semibold tracking-tight text-[#171717]">
            Incident Action History & Idempotency Audit
          </h2>
          <Badge variant="outline" className="text-[10px]">
            {logs.length} logged
          </Badge>
        </div>

        {logs.length > 0 && (
          <button
            onClick={onClear}
            className="text-xs text-[#737373] hover:text-[#171717] flex items-center gap-1 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear Log</span>
          </button>
        )}
      </div>

      {/* Log Table / List */}
      {logs.length === 0 ? (
        <div className="py-8 text-center text-xs text-[#737373]">
          <Clock className="w-6 h-6 mx-auto mb-2 text-[#A3A3A3]" />
          <p className="font-medium text-[#171717]">No incidents recorded this session.</p>
          <p className="mt-0.5">Actions triggered in the control panel will appear here with idempotency tracking.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#E5E5E5] text-[#737373] font-medium">
                <th className="pb-2 font-normal">Timestamp</th>
                <th className="pb-2 font-normal">Target</th>
                <th className="pb-2 font-normal">Action Type</th>
                <th className="pb-2 font-normal">Request ID</th>
                <th className="pb-2 font-normal">Status</th>
                <th className="pb-2 font-normal text-right">Confirmed Revision</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5E5E5]">
              {logs.map((entry) => {
                const isSuccess = entry.status === 'APPLIED';
                const isError = entry.status === 'REJECTED';

                return (
                  <tr key={entry.id} className="hover:bg-[#FAFAFA] transition-colors">
                    <td className="py-2.5 font-mono text-[#737373] whitespace-nowrap">
                      {entry.timestamp}
                    </td>
                    <td className="py-2.5 font-semibold text-[#171717]">
                      {entry.junction_id ? `Intersection ${entry.junction_id}` : 'All'}
                    </td>
                    <td className="py-2.5 text-[#262626]">
                      {entry.type === 'FAULT_INJECTION' && 'Camera Dropout'}
                      {entry.type === 'FAULT_CLEAR' && 'Camera Restoration'}
                      {entry.type === 'SCENARIO_RESET' && 'Scenario Reset'}
                    </td>
                    <td className="py-2.5 font-mono text-[11px] text-[#737373] max-w-[140px] truncate" title={entry.request_id}>
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
                    <td className="py-2.5 text-right font-mono text-[#171717]">
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

