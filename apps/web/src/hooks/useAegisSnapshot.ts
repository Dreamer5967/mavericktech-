import { useQuery } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import { fetchSnapshot } from '../services/api/aegisApi';
import { ConnectionStatus, SnapshotResponse } from '../types/api';

const STALE_THRESHOLD_MS = 7000;
const POLLING_INTERVAL_MS = 500;

export function useAegisSnapshot() {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('DISCONNECTED');
  const [secondsSinceLastUpdate, setSecondsSinceLastUpdate] = useState<number | null>(null);

  const query = useQuery<SnapshotResponse, Error>({
    queryKey: ['aegis-snapshot'],
    queryFn: fetchSnapshot,
    refetchInterval: POLLING_INTERVAL_MS,
    refetchIntervalInBackground: true,
    retry: 1,
    staleTime: 250,
  });

  const { data, dataUpdatedAt, isError, isSuccess } = query;

  // Track wall-clock freshness and connection status
  useEffect(() => {
    const updateFreshness = () => {
      // If no successful snapshot has ever been received
      if (!dataUpdatedAt || !data) {
        setConnectionStatus('DISCONNECTED');
        setSecondsSinceLastUpdate(null);
        return;
      }

      const elapsedMs = Date.now() - dataUpdatedAt;
      const elapsedSec = Math.floor(elapsedMs / 1000);
      setSecondsSinceLastUpdate(elapsedSec);

      // If the latest query errored out, the backend link is severed
      if (isError) {
        setConnectionStatus('DISCONNECTED');
        return;
      }

      // If data is older than threshold, it is stale
      if (elapsedMs > STALE_THRESHOLD_MS) {
        setConnectionStatus('STALE');
      } else if (isSuccess) {
        setConnectionStatus('CONNECTED');
      }
    };

    updateFreshness();
    const interval = setInterval(updateFreshness, 1000);
    return () => clearInterval(interval);
  }, [data, dataUpdatedAt, isError, isSuccess]);

  return {
    ...query,
    connectionStatus,
    secondsSinceLastUpdate,
  };
}
