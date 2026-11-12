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
      dot: 'bg-[#23865A]',
      text: 'Connected',
      textColor: 'text-[#23865A]',
      bg: 'bg-[#EAF4EE]',
      border: 'border-[#D1E8DA]',
    },
    STALE: {
      dot: 'bg-[#B7791F]',
      text: 'Stale',
      textColor: 'text-[#B7791F]',
      bg: 'bg-[#FFFBEB]',
      border: 'border-[#FDE68A]',
    },
    DISCONNECTED: {
      dot: 'bg-[#C0392B]',
      text: 'Disconnected',
      textColor: 'text-[#C0392B]',
      bg: 'bg-[#FDF2F2]',
      border: 'border-[#FECACA]',
    },
  }[status];

  return (
    <div className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded border text-xs font-medium ${config.bg} ${config.border}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />
      {showText && <span className={config.textColor}>{config.text}</span>}
    </div>
  );
};
