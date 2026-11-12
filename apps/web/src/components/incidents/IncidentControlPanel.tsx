import React, { useState } from 'react';
import { KeyRound, Eye, EyeOff, RotateCcw, Camera, CameraOff, AlertTriangle, CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { JunctionData, JunctionId } from '../../types/api';
import { Badge } from '../common/Badge';

interface IncidentControlPanelProps {
  junctions?: JunctionData[];
  operatorToken: string;
  onTokenChange: (token: string) => void;
  onTriggerFault: (junctionId: JunctionId, enabled: boolean) => Promise<unknown>;
  onTriggerReset: () => Promise<unknown>;
  isPending: boolean;
  feedback: {
    type: 'success' | 'error' | null;
    message: string | null;
  };
  onClearFeedback: () => void;
}

export const IncidentControlPanel: React.FC<IncidentControlPanelProps> = ({
  junctions = [],
  operatorToken,
  onTokenChange,
  onTriggerFault,
  onTriggerReset,
  isPending,
  feedback,
  onClearFeedback,
}) => {
  const [showToken, setShowToken] = useState(false);
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [actionInProgressId, setActionInProgressId] = useState<string | null>(null);

  const handleFaultToggle = async (jId: JunctionId, currentlyMissing: boolean) => {
    setActionInProgressId(jId);
    try {
      await onTriggerFault(jId, !currentlyMissing);
    } catch {
      // Feedback handled in hook
    } finally {
      setActionInProgressId(null);
    }
  };

  const handleResetConfirm = async () => {
    setShowResetConfirm(false);
    setActionInProgressId('reset');
    try {
      await onTriggerReset();
    } catch {
      // Feedback handled in hook
    } finally {
      setActionInProgressId(null);
    }
  };

  return (
    <section className="bg-[#111A1D] border border-white/10 rounded-lg p-4 sm:p-5 space-y-5 shadow-sm">
      {/* Panel Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-white/10">
        <div>
          <h2 className="text-sm font-display font-semibold tracking-tight text-white">
            Operator Incident & Fault Control
          </h2>
          <p className="text-xs text-white/50 mt-0.5">
            Inject allowlisted roadside sensor failures and reset scenario fixtures.
          </p>
        </div>

        {/* Global Reset Trigger */}
        <div>
          <button
            onClick={() => setShowResetConfirm(true)}
            disabled={isPending}
            className="px-3.5 py-1.5 rounded border border-white/15 bg-white/5 hover:bg-red-500/10 hover:border-red-500/30 hover:text-red-400 text-xs font-mono text-white/70 transition-colors flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
          >
            {actionInProgressId === 'reset' ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin text-red-400" />
            ) : (
              <RotateCcw className="w-3.5 h-3.5" />
            )}
            <span>Reset All Fixtures</span>
          </button>
        </div>
      </div>

      {/* Operator Token Authentication Bar */}
      <div className="rounded-lg border border-white/10 bg-[#080D10] p-3 text-xs flex flex-col md:flex-row md:items-center justify-between gap-3 font-mono">
        <div className="flex items-center gap-2">
          <KeyRound className="w-4 h-4 text-[#45C982] shrink-0" />
          <span className="font-medium text-white">Operator Credential:</span>
          <span className="text-white/40 hidden sm:inline">(Bearer Token)</span>
        </div>

        <div className="flex items-center gap-2 max-w-sm w-full">
          <div className="relative flex-1">
            <input
              type={showToken ? 'text' : 'password'}
              value={operatorToken}
              onChange={(e) => onTokenChange(e.target.value)}
              placeholder="Enter authorization token..."
              className="w-full pl-3 pr-8 py-1.5 rounded border border-white/15 bg-[#111A1D] text-xs font-mono text-white placeholder-white/30 focus:outline-none focus:border-[#45C982] focus:ring-1 focus:ring-[#45C982]"
            />
            <button
              type="button"
              onClick={() => setShowToken(!showToken)}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-white/40 hover:text-white"
            >
              {showToken ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
            </button>
          </div>
          <span className="text-[10px] text-white/40 hidden sm:inline">P4-03</span>
        </div>
      </div>

      {/* Operation Feedback Banner */}
      {feedback.message && (
        <div
          className={`p-3 rounded-lg border text-xs flex items-center justify-between gap-3 ${
            feedback.type === 'success'
              ? 'bg-[#45C982]/10 border-[#45C982]/30 text-[#45C982]'
              : 'bg-red-500/10 border-red-500/30 text-red-400'
          }`}
        >
          <div className="flex items-center gap-2 font-mono">
            {feedback.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 shrink-0 text-[#45C982]" />
            ) : (
              <XCircle className="w-4 h-4 shrink-0 text-red-400" />
            )}
            <span>{feedback.message}</span>
          </div>
          <button
            onClick={onClearFeedback}
            className="text-xs hover:opacity-75 transition-opacity font-mono"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Reset Confirmation Modal Banner */}
      {showResetConfirm && (
        <div className="p-4 rounded-lg border border-[#E9A23B]/30 bg-[#161C1D] space-y-3">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-[#E9A23B] shrink-0 mt-0.5" />
            <div>
              <h3 className="text-xs font-display font-bold text-white">
                Confirm Global Scenario Reset?
              </h3>
              <p className="text-xs text-white/70 mt-0.5">
                This will clear all camera failure injections across J1–J4 and advance the authoritative server revision.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 justify-end pt-1">
            <button
              onClick={() => setShowResetConfirm(false)}
              className="px-3 py-1.5 rounded border border-white/15 bg-white/5 hover:bg-white/10 text-xs font-mono text-white/70 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleResetConfirm}
              disabled={isPending}
              className="px-3 py-1.5 rounded bg-[#E9A23B] hover:bg-[#d69230] text-[#080D10] text-xs font-mono font-bold transition-colors flex items-center gap-1.5"
            >
              {isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              <span>Execute Reset</span>
            </button>
          </div>
        </div>
      )}

      {/* Junction Fault Controls Grid (Allowlisted: J1, J2, J3, J4) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {(['J1', 'J2', 'J3', 'J4'] as JunctionId[]).map((jId) => {
          const jData = junctions.find((item) => item.junction_id === jId);
          const isMissing = jData?.camera_status === 'MISSING';
          const isThisPending = actionInProgressId === jId;

          return (
            <div
              key={jId}
              className={`p-3.5 rounded-lg border flex flex-col justify-between space-y-3 transition-colors ${
                isMissing
                  ? 'bg-[#161C1D] border-[#E9A23B]/30'
                  : 'bg-[#080D10] border-white/10'
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-display font-bold text-sm text-white">
                    Intersection {jId}
                  </span>
                  <div className="flex items-center gap-1 text-[11px] font-mono text-white/40 mt-0.5">
                    <span>Target: cam_{jId.toLowerCase()}</span>
                  </div>
                </div>

                <Badge variant={isMissing ? 'warning' : 'success'}>
                  {isMissing ? 'Dropout' : 'Active'}
                </Badge>
              </div>

              {/* Status Notice */}
              <div className="text-[11px] font-mono">
                {isMissing ? (
                  <span className="text-[#E9A23B]">Degraded: queue interval expanded</span>
                ) : (
                  <span className="text-white/40">Nominal 1 FPS ingestion</span>
                )}
              </div>

              {/* Action Toggle Button */}
              <button
                onClick={() => handleFaultToggle(jId, isMissing)}
                disabled={isPending}
                className={`w-full py-1.5 px-3 rounded text-xs font-mono font-semibold transition-all flex items-center justify-center gap-1.5 disabled:opacity-50 cursor-pointer ${
                  isMissing
                    ? 'bg-[#45C982] hover:bg-[#3db874] text-[#080D10] shadow-sm shadow-[#45C982]/20'
                    : 'border border-[#E9A23B]/30 bg-[#E9A23B]/10 hover:bg-[#E9A23B]/20 text-[#E9A23B]'
                }`}
              >
                {isThisPending ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : isMissing ? (
                  <Camera className="w-3.5 h-3.5" />
                ) : (
                  <CameraOff className="w-3.5 h-3.5" />
                )}
                <span>{isMissing ? 'Restore Camera' : 'Inject Dropout'}</span>
              </button>
            </div>
          );
        })}
      </div>
    </section>
  );
};
