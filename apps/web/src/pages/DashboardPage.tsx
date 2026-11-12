import React, { useState } from 'react';
import { Terminal, ChevronDown, ChevronUp, Copy, Check } from 'lucide-react';
import { useAegisSnapshot } from '../hooks/useAegisSnapshot';
import { Navbar } from '../components/layout/Navbar';
import { PageHeader } from '../components/layout/PageHeader';
import { ReadinessPanel } from '../components/readiness/ReadinessPanel';
import { JunctionGrid } from '../components/junctions/JunctionGrid';
import { CameraViewer } from '../components/camera/CameraViewer';
import { LiveDigitalTwinCommandBanner } from '../components/dashboard/LiveDigitalTwinCommandBanner';
import { AiAssistantSection } from '../components/assistant/AiAssistantSection';

export const DashboardPage: React.FC = () => {
  const {
    data: snapshot,
    isLoading,
    isFetching,
    connectionStatus,
    secondsSinceLastUpdate,
    refetch,
  } = useAegisSnapshot();

  const [activeTab, setActiveTab] = useState('overview');
  const [showRawJson, setShowRawJson] = useState(false);
  const [copied, setCopied] = useState(false);

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

  const isStale = connectionStatus === 'STALE';

  return (
    <div className="aegis-dashboard min-h-screen bg-[#080D10] text-white flex flex-col font-sans">
      {/* Top Navigation */}
      <Navbar activeTab={activeTab} onTabChange={handleTabChange} />

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

        <section id="incidents-section" className="bg-white border border-[#E5E5E5] rounded p-4 text-sm text-[#737373]">
          <h2 className="text-sm font-semibold text-[#171717]">Incident Controls</h2>
          <p className="mt-1">This dashboard is read-only. Fault injection requires a runtime token and is not exposed here.</p>
        </section>

        {/* AI Assistant Section — P4-04 */}
        <div id="assistant-section">
          <AiAssistantSection />
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
          <span>P2 observation feed: http://127.0.0.1:8765</span>
        </div>
      </footer>
    </div>
  );
};
