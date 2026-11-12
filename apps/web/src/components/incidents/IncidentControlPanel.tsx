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
    <section className="bg-white border border-[#E5E5E5] rounded p-4 sm:p-5 space-y-5">
      {/* Panel Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#E5E5E5]">
        <div>
          <h2 className="text-sm font-semibold tracking-tight text-[#171717]">
            Operator Incident & Fault Control
          </h2>
          <p className="text-xs text-[#737373] mt-0.5">
            Inject allowlisted roadside sensor failures and reset scenario fixtures.
          </p>
        </div>

        {/* Global Reset Trigger */}
        <div>
          <button
            onClick={() => setShowResetConfirm(true)}
            disabled={isPending}
            className="px-3 py-1.5 rounded border border-[#E5E5E5] bg-white hover:bg-[#FDF2F2] hover:border-[#FECACA] hover:text-[#C0392B] text-xs font-medium text-[#737373] transition-colors flex items-center gap-1.5 disabled:opacity-50"
          >
            {actionInProgressId === 'reset' ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin text-[#C0392B]" />
            ) : (
              <RotateCcw className="w-3.5 h-3.5" />
            )}
            <span>Reset All Fixtures</span>
          </button>
        </div>
      </div>

      {/* Operator Token Authentication Bar */}
      <div className="rounded border border-[#E5E5E5] bg-[#F5F5F5] p-3 text-xs flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <KeyRound className="w-4 h-4 text-[#737373] shrink-0" />
          <span className="font-medium text-[#262626]">Operator Credential:</span>
          <span className="text-[#737373] hidden sm:inline">(Bearer Token)</span>
        </div>

        <div className="flex items-center gap-2 max-w-sm w-full">
          <div className="relative flex-1">
            <input
              type={showToken ? 'text' : 'password'}
              value={operatorToken}
              onChange={(e) => onTokenChange(e.target.value)}
              placeholder="Enter operator token..."
              className="w-full px-2.5 py-1 text-xs font-mono bg-white border border-[#E5E5E5] rounded pr-8 text-[#171717] focus:outline-none focus:border-[#171717]"
            />
            <button
              type="button"
              onClick={() => setShowToken(!showToken)}
              className="absolute right-2 top-1.5 text-[#737373] hover:text-[#171717]"
              title={showToken ? 'Hide token' : 'Show token'}
            >
              {showToken ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
            </button>
          </div>
          <Badge variant="outline" className="text-[10px]">
            Role: Operator
          </Badge>
        </div>
      </div>

      {/* Feedback Banners */}
      {feedback.message && (
        <div
          className={`rounded border px-3.5 py-2.5 text-xs flex items-center justify-between gap-2.5 ${
            feedback.type === 'success'
              ? 'border-[#D1E8DA] bg-[#EAF4EE] text-[#23865A]'
              : 'border-[#FECACA] bg-[#FDF2F2] text-[#C0392B]'
          }`}
        >
          <div className="flex items-center gap-2">
            {feedback.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 shrink-0" />
            ) : (
              <XCircle className="w-4 h-4 shrink-0" />
            )}
            <span>{feedback.message}</span>
          </div>
          <button
            onClick={onClearFeedback}
            className="text-xs hover:opacity-75 font-semibold px-1"
          >
            &times;
          </button>
        </div>
      )}

      {/* Junction Allowlist Fault Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {(['J1', 'J2', 'J3', 'J4'] as JunctionId[]).map((jId) => {
          const junction = junctions.find((j) => j.junction_id === jId);
          const isMissing = junction?.camera_status === 'MISSING';
          const isThisLoading = actionInProgressId === jId && isPending;

          return (
            <div
              key={jId}
              className={`rounded border p-3.5 flex flex-col justify-between transition-colors ${
                isMissing ? 'border-[#FDE68A] bg-[#FFFBEB]/40' : 'border-[#E5E5E5] bg-white'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-sm text-[#171717]">Intersection {jId}</span>
                  {isMissing ? (
                    <Badge variant="warning" className="gap-1 text-[11px]">
                      <CameraOff className="w-3 h-3" />
                      <span>Dropout</span>
                    </Badge>
                  ) : (
                    <Badge variant="success" className="gap-1 text-[11px]">
                      <Camera className="w-3 h-3" />
                      <span>Available</span>
                    </Badge>
                  )}
                </div>

                <div className="text-xs text-[#737373] space-y-1 mb-3">
                  <div className="flex justify-between">
                    <span>Camera Feed:</span>
                    <span className="font-mono text-[#171717]">{isMissing ? 'OFFLINE' : 'ONLINE'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Observed:</span>
                    <span className="font-mono text-[#171717]">
                      {junction?.observed_count === null ? 'null' : `${junction?.observed_count ?? '--'} veh`}
                    </span>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <button
                onClick={() => handleFaultToggle(jId, isMissing)}
                disabled={isPending}
                className={`w-full py-1.5 px-3 rounded text-xs font-medium transition-colors flex items-center justify-center gap-1.5 disabled:opacity-50 ${
                  isMissing
                    ? 'border border-[#D1E8DA] bg-[#EAF4EE] text-[#23865A] hover:bg-[#DDF0E4]'
                    : 'border border-[#E5E5E5] bg-[#F5F5F5] text-[#262626] hover:bg-[#EAEAEA]'
                }`}
              >
                {isThisLoading ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : isMissing ? (
                  <Camera className="w-3.5 h-3.5" />
                ) : (
                  <CameraOff className="w-3.5 h-3.5" />
                )}
                <span>
                  {isThisLoading
                    ? 'Transmitting...'
                    : isMissing
                    ? 'Restore Camera'
                    : 'Drop Camera'}
                </span>
              </button>
            </div>
          );
        })}
      </div>

      {/* Reset Confirmation Modal */}
      {showResetConfirm && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded border border-[#E5E5E5] shadow-lg max-w-md w-full p-5 space-y-4">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-[#FDF2F2] border border-[#FECACA] flex items-center justify-center text-[#C0392B] shrink-0">
                <AlertTriangle className="w-4 h-4" />
              </div>
              <div>
                <h3 className="font-bold text-sm text-[#171717]">Confirm Scenario Reset</h3>
                <p className="text-xs text-[#737373] mt-1 leading-relaxed">
                  This will clear all simulated camera dropouts and restore all 4 intersections (J1–J4) to their operational baseline.
                  This action increments the system revision.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#E5E5E5]">
              <button
                onClick={() => setShowResetConfirm(false)}
                className="px-3 py-1.5 rounded border border-[#E5E5E5] text-xs font-medium text-[#737373] hover:bg-[#F5F5F5] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleResetConfirm}
                className="px-3 py-1.5 rounded bg-[#C0392B] text-white text-xs font-medium hover:bg-[#A93226] transition-colors"
              >
                Yes, Reset Fixtures
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};

