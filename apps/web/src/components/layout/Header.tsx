import React from 'react';
import { PageHeader } from './PageHeader';
import { ConnectionStatus, OperatingMode } from '../../types/api';

interface HeaderProps {
  connectionStatus: ConnectionStatus;
  mode?: OperatingMode;
  secondsSinceLastUpdate: number | null;
  onRefresh?: () => void;
  isFetching?: boolean;
}

export const Header: React.FC<HeaderProps> = (props) => {
  return <PageHeader {...props} />;
};
