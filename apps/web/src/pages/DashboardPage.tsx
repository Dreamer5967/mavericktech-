import React, { useState } from 'react';
import { Terminal, ChevronDown, ChevronUp, Copy, Check } from 'lucide-react';
import { useAegisSnapshot } from '../hooks/useAegisSnapshot';
import { useIncidentMutation } from '../hooks/useIncidentMutation';
import { Navbar } from '../components/layout/Navbar';
import { PageHeader } from '../components/layout/PageHeader';
import { ReadinessPanel } from '../components/readiness/ReadinessPanel';
import { JunctionGrid } from '../components/junctions/JunctionGrid';
import { CameraViewer } from '../components/camera/CameraViewer';
import { IncidentControlPanel } from '../components/incidents/IncidentControlPanel';
import { IncidentHistoryLog } from '../components/incidents/IncidentHistoryLog';
import { JunctionId } from '../types/api';

export const DashboardPage: React.FC = () => {
  const {
    data: snapshot,
    isLoading,
    isFetching,
    connectionStatus,
    secondsSinceLastUpdate,
    refetch,
  } = useAegisSnapshot();

  const [operatorToken, setOperatorToken] = useState('local-demo-only');
  const [activeTab, setActiveTab] = useState('overview');
  const [showRawJson, setShowRawJson] = useState(false);
  const [copied, setCopied] = useState(false);

  const {
    triggerFault,
    triggerReset,
    isPending,
    feedback,
    clearFeedback,
    incidentLogs,
    clearLogs,
  } = useIncidentMutation(operatorToken);

  const handleCopyJson = () => {
    if (snapshot) {
      navigator.clipboard.writeText(JSON.stringify(snapshot, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleTabChange = (tabId: string) => {
    setActiveTab(tabId);
    if (tabId === 'intersections') {
      document.getElementById('intersections-section')?.scrollIntoView({ behavior: 'smooth' });
    } else if (tabId === 'cameras') {
      document.getElementById('cameras-section')?.scrollIntoView({ behavior: 'smooth' });
    } else if (tabId === 'incidents') {
      document.getElementById('incidents-section')?.scrollIntoView({ behavior: 'smooth' });
    } else if (tabId === 'overview') {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleFaultTrigger = (junctionId: JunctionId, enabled: boolean) => {
    return triggerFault({ junction_id: junctionId, enabled });
  };

  const isStale = connectionStatus === 'STALE';

  return (
    <div className="min-h-screen bg-white text-[#171717] flex flex-col font-sans">
      {/* Top Navigation */}
      <Navbar activeTab={activeTab} onTabChange={handleTabChange} />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Operations Overview Page Header */}
        <PageHeader
          mode={snapshot?.mode}
          connectionStatus={connectionStatus}
          secondsSinceLastUpdate={secondsSinceLastUpdate}
          onRefresh={() => refetch()}
          isFetching={isFetching}
          notice={snapshot?.notice}
        />

        {/* System Readiness Strip */}
        <ReadinessPanel
          snapshot={snapshot}
          connectionStatus={connectionStatus}
        />

        {/* Intersection Monitoring Grid */}
        <div id="intersections-section">
          <JunctionGrid
            junctions={snapshot?.junctions}
            isLoading={isLoading}
            isStale={isStale}
          />
        </div>

        {/* Camera Viewer Inspection Section */}
        <div id="cameras-section">
          <CameraViewer junctions={snapshot?.junctions} />
        </div>

        {/* Incident Management Section */}
        <div id="incidents-section" className="space-y-4">
          <IncidentControlPanel
            junctions={snapshot?.junctions}
            operatorToken={operatorToken}
            onTokenChange={setOperatorToken}
            onTriggerFault={handleFaultTrigger}
            onTriggerReset={triggerReset}
            isPending={isPending}
            feedback={feedback}
            onClearFeedback={clearFeedback}
          />

          <IncidentHistoryLog
            logs={incidentLogs}
            onClear={clearLogs}
          />
        </div>

        {/* Data Contract Inspection Drawer (Clean Industrial Collapsible) */}
        <section className="bg-white border border-[#E5E5E5] rounded overflow-hidden">
          <button
            onClick={() => setShowRawJson(!showRawJson)}
            className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-[#F5F5F5] transition-colors"
          >
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-[#737373]" />
              <span className="text-xs font-semibold text-[#171717]">
                Snapshot Payload Verification
              </span>
              <span className="text-xs text-[#737373]">
                ({snapshot?.junctions?.length ?? 0} intersections · rev #{snapshot?.state_revision ?? 0})
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-[#737373]">
              <span>{showRawJson ? 'Collapse' : 'Inspect'}</span>
              {showRawJson ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </div>
          </button>

          {showRawJson && (
            <div className="border-t border-[#E5E5E5] p-4 bg-[#FAFAFA]">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-[#737373] font-mono">
                  GET /api/v1/snapshot
                </span>
                <button
                  onClick={handleCopyJson}
                  className="flex items-center gap-1 px-2.5 py-1 rounded border border-[#E5E5E5] bg-white hover:bg-[#F5F5F5] text-xs text-[#262626] transition-colors"
                >
                  {copied ? <Check className="w-3 h-3 text-[#23865A]" /> : <Copy className="w-3 h-3" />}
                  <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
              <pre className="p-3 rounded border border-[#E5E5E5] bg-white font-mono text-xs text-[#262626] overflow-x-auto max-h-80 leading-relaxed">
                {snapshot ? JSON.stringify(snapshot, null, 2) : '// No snapshot data available.'}
              </pre>
            </div>
          )}
        </section>
      </main>

      {/* Industrial Operations Footer */}
      <footer className="border-t border-[#E5E5E5] bg-[#F5F5F5] py-3 px-4 sm:px-6 text-xs text-[#737373]">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>AEGIS Traffic Management System &bull; Operator Console</span>
          <span>Target Service: http://127.0.0.1:8000</span>
        </div>
      </footer>
    </div>
  );
};
