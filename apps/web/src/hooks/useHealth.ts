import { useQuery } from '@tanstack/react-query';
import { fetchHealth } from '../services/api/aegisApi';
import { HealthResponse } from '../types/api';

export function useHealth() {
  return useQuery<HealthResponse, Error>({
    queryKey: ['aegis-health'],
    queryFn: fetchHealth,
    refetchInterval: 5000,
    retry: 1,
  });
}

