import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { postFault, postReset, ApiError } from '../services/api/aegisApi';
import { FaultRequestPayload, IncidentLogEntry, JunctionId, SnapshotResponse } from '../types/api';

export function useIncidentMutation(operatorToken: string) {
  const queryClient = useQueryClient();
  const [incidentLogs, setIncidentLogs] = useState<IncidentLogEntry[]>([]);
  const [feedback, setFeedback] = useState<{
    type: 'success' | 'error' | null;
    message: string | null;
  }>({ type: null, message: null });

  // Fault mutation
  const faultMutation = useMutation<
    SnapshotResponse,
    ApiError | Error,
    { junction_id: JunctionId; enabled: boolean }
  >({
    mutationFn: async ({ junction_id, enabled }) => {
      const requestId = `req-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
      const payload: FaultRequestPayload = {
        junction_id,
        enabled,
        request_id: requestId,
      };

      const logId = `log-${Date.now()}`;
      const logEntry: IncidentLogEntry = {
        id: logId,
        request_id: requestId,
        timestamp: new Date().toLocaleTimeString(),
        type: enabled ? 'FAULT_INJECTION' : 'FAULT_CLEAR',
        junction_id,
        status: 'PENDING',
        message: enabled ? `Injecting camera dropout on ${junction_id}...` : `Restoring camera on ${junction_id}...`,
      };

      setIncidentLogs((prev) => [logEntry, ...prev.slice(0, 19)]);

      try {
        const response = await postFault(payload, operatorToken);
        // Authoritative update on success
        setIncidentLogs((prev) =>
          prev.map((item) =>
            item.id === logId
              ? {
                  ...item,
                  status: 'APPLIED',
                  state_revision: response.state_revision,
                  message: enabled
                    ? `Camera dropout applied on ${junction_id} (rev #${response.state_revision})`
                    : `Camera restored on ${junction_id} (rev #${response.state_revision})`,
                }
              : item
          )
        );
        return response;
      } catch (err) {
        const errMsg = err instanceof Error ? err.message : 'Request rejected by server';
        setIncidentLogs((prev) =>
          prev.map((item) =>
            item.id === logId
              ? {
                  ...item,
                  status: 'REJECTED',
                  message: errMsg,
                }
              : item
          )
        );
        throw err;
      }
    },
    onSuccess: (data) => {
      // Authoritative cache update only
      queryClient.setQueryData(['aegis-snapshot'], data);
      setFeedback({
        type: 'success',
        message: `State updated successfully to revision #${data.state_revision}`,
      });
    },
    onError: (err) => {
      setFeedback({
        type: 'error',
        message: err.message || 'Incident request failed',
      });
    },
  });

  // Reset mutation
  const resetMutation = useMutation<SnapshotResponse, ApiError | Error, void>({
    mutationFn: async () => {
      const requestId = `reset-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
      const logId = `log-${Date.now()}`;

      const logEntry: IncidentLogEntry = {
        id: logId,
        request_id: requestId,
        timestamp: new Date().toLocaleTimeString(),
        type: 'SCENARIO_RESET',
        junction_id: 'ALL',
        status: 'PENDING',
        message: 'Resetting all intersection fixtures...',
      };

      setIncidentLogs((prev) => [logEntry, ...prev.slice(0, 19)]);

      try {
        const response = await postReset(operatorToken, { request_id: requestId });
        setIncidentLogs((prev) =>
          prev.map((item) =>
            item.id === logId
              ? {
                  ...item,
                  status: 'APPLIED',
                  state_revision: response.state_revision,
                  message: `All fixtures reset to baseline (rev #${response.state_revision})`,
                }
              : item
          )
        );
        return response;
      } catch (err) {
        const errMsg = err instanceof Error ? err.message : 'Reset rejected by server';
        setIncidentLogs((prev) =>
          prev.map((item) =>
            item.id === logId
              ? {
                  ...item,
                  status: 'REJECTED',
                  message: errMsg,
                }
              : item
          )
        );
        throw err;
      }
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['aegis-snapshot'], data);
      setFeedback({
        type: 'success',
        message: `Scenario reset confirmed (rev #${data.state_revision})`,
      });
    },
    onError: (err) => {
      setFeedback({
        type: 'error',
        message: err.message || 'Scenario reset failed',
      });
    },
  });

  const isPending = faultMutation.isPending || resetMutation.isPending;

  return {
    triggerFault: faultMutation.mutateAsync,
    triggerReset: resetMutation.mutateAsync,
    isPending,
    feedback,
    clearFeedback: () => setFeedback({ type: null, message: null }),
    incidentLogs,
    clearLogs: () => setIncidentLogs([]),
  };
}

