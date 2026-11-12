import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, LayoutDashboard } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[AEGIS ErrorBoundary Caught]:', error, errorInfo);
    this.setState({ errorInfo });
  }

  private handleReload = () => {
    window.location.reload();
  };

  private handleGoDashboard = () => {
    window.location.href = '/dashboard';
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#080D10] text-white flex items-center justify-center p-6 font-mono">
          <div className="max-w-2xl w-full bg-[#111A1D] border border-red-500/30 rounded-xl p-8 shadow-2xl space-y-6">
            <div className="flex items-center gap-3 text-red-400">
              <AlertTriangle className="w-8 h-8 text-red-400" />
              <div>
                <h1 className="text-xl font-bold tracking-tight text-white font-sans">
                  Application Runtime Error
                </h1>
                <p className="text-xs text-white/50">
                  AEGIS Client encountered an unhandled exception during rendering.
                </p>
              </div>
            </div>

            <div className="bg-[#080D10] rounded-lg p-4 border border-white/10 text-xs text-red-300 overflow-x-auto">
              <p className="font-semibold text-white/90">
                {this.state.error?.name}: {this.state.error?.message}
              </p>
              {this.state.error?.stack && (
                <pre className="mt-3 text-[11px] text-white/40 leading-relaxed overflow-x-auto whitespace-pre-wrap">
                  {this.state.error.stack}
                </pre>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <button
                onClick={this.handleReload}
                className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Reload Page</span>
              </button>
              <button
                onClick={this.handleGoDashboard}
                className="px-4 py-2 bg-[#45C982] hover:bg-[#3db874] text-[#080D10] rounded text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer"
              >
                <LayoutDashboard className="w-3.5 h-3.5" />
                <span>Return to Operator Console</span>
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
