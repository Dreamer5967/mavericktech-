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
import { AiAssistantSection } from '../components/assistant/AiAssistantSection';
import { LiveDigitalTwinCommandBanner } from '../components/dashboard/LiveDigitalTwinCommandBanner';
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
    } else if (tabId === 'assistant') {
      document.getElementById('assistant-section')?.scrollIntoView({ behavior: 'smooth' });
    } else if (tabId === 'overview') {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleFaultTrigger = (junctionId: JunctionId, enabled: boolean) => {
    return triggerFault({ junction_id: junctionId, enabled });
  };

  const isStale = connectionStatus === 'STALE';

  return (
    <div className="min-h-screen bg-[#080D10] text-white selection:bg-[#45C982] selection:text-[#080D10] flex flex-col font-sans">
      {/* Top Navigation */}
      <Navbar activeTab={activeTab} onTabChange={handleTabChange} />

      {/* Live Digital Twin Command Canopy — Real-time Arterial Co-Simulation */}
      <LiveDigitalTwinCommandBanner snapshot={snapshot} />

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

        {/* AI Assistant Section — P4-04 */}
        <div id="assistant-section">
          <AiAssistantSection />
        </div>

        {/* Data Contract Inspection Drawer */}
        <section className="bg-[#111A1D] border border-white/10 rounded-lg overflow-hidden shadow-sm">
          <button
            onClick={() => setShowRawJson(!showRawJson)}
            className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-white/[0.03] transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-[#45C982]" />
              <span className="text-xs font-mono font-semibold text-white">
                Snapshot Payload Verification
              </span>
              <span className="text-xs font-mono text-white/40">
                ({snapshot?.junctions?.length ?? 0} intersections · rev #{snapshot?.state_revision ?? 0})
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-xs font-mono text-white/50">
              <span>{showRawJson ? 'Collapse' : 'Inspect'}</span>
              {showRawJson ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </div>
          </button>

          {showRawJson && (
            <div className="border-t border-white/10 p-4 bg-[#080D10]">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-[#45C982] font-mono">
                  GET /api/v1/snapshot
                </span>
                <button
                  onClick={handleCopyJson}
                  className="flex items-center gap-1 px-2.5 py-1 rounded border border-white/15 bg-white/5 hover:bg-white/10 text-xs font-mono text-white transition-colors cursor-pointer"
                >
                  {copied ? <Check className="w-3 h-3 text-[#45C982]" /> : <Copy className="w-3 h-3" />}
                  <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
              <pre className="p-3.5 rounded border border-white/10 bg-[#080D10] font-mono text-xs text-white/80 overflow-x-auto max-h-80 leading-relaxed">
                {snapshot ? JSON.stringify(snapshot, null, 2) : '// No snapshot data available.'}
              </pre>
            </div>
          )}
        </section>
      </main>

      {/* Industrial Operations Footer */}
      <footer className="border-t border-white/10 bg-[#080D10] py-4 px-4 sm:px-6 text-xs font-mono text-white/40">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>AEGIS Traffic Management System &bull; Operator Console</span>
          <span>Target Service: http://127.0.0.1:8000</span>
        </div>
      </footer>
    </div>
  );
};
