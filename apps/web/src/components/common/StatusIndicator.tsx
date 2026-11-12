import React from 'react';
import { ConnectionStatus } from '../../types/api';

interface StatusIndicatorProps {
  status: ConnectionStatus;
  showText?: boolean;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  showText = true,
}) => {
  const config = {
    CONNECTED: {
      dot: 'bg-[#45C982] shadow-[0_0_8px_#45C982]',
      text: 'Connected',
      textColor: 'text-[#45C982]',
      bg: 'bg-[#45C982]/10',
      border: 'border-[#45C982]/25',
    },
    STALE: {
      dot: 'bg-[#E9A23B] shadow-[0_0_8px_#E9A23B]',
      text: 'Stale',
      textColor: 'text-[#E9A23B]',
      bg: 'bg-[#E9A23B]/10',
      border: 'border-[#E9A23B]/25',
    },
    DISCONNECTED: {
      dot: 'bg-red-500 shadow-[0_0_8px_#ef4444]',
      text: 'Disconnected',
      textColor: 'text-red-400',
      bg: 'bg-red-500/10',
      border: 'border-red-500/25',
    },
  }[status];

  return (
    <div className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded border text-xs font-mono font-medium ${config.bg} ${config.border}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />
      {showText && <span className={config.textColor}>{config.text}</span>}
    </div>
  );
};
