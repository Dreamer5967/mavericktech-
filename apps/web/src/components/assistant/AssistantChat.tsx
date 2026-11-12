import React, { useEffect, useRef } from 'react';
import { Bot, User, AlertTriangle, Database, Eye, Sparkles } from 'lucide-react';
import { ChatMessage } from '../../types/api';

interface AssistantChatProps {
  messages: ChatMessage[];
  isLoading: boolean;
}

function SourceBadge({ source, status }: { source?: string; status?: string }) {
  if (!source) return null;

  if (status === 'ERROR') {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded border border-red-500/30 bg-red-500/10 text-red-400">
        <AlertTriangle className="w-2.5 h-2.5" />
        error
      </span>
    );
  }

  if (source === 'gemini') {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded border border-[#45C982]/30 bg-[#45C982]/10 text-[#45C982]">
        <Sparkles className="w-2.5 h-2.5" />
        gemini vision estimate
      </span>
    );
  }

  if (source === 'vqa_model') {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded border border-[#E9A23B]/30 bg-[#E9A23B]/10 text-[#E9A23B]">
        <Eye className="w-2.5 h-2.5" />
        estimate — not a measurement
      </span>
    );
  }

  if (source === 'degraded') {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded border border-[#E9A23B]/30 bg-[#E9A23B]/10 text-[#E9A23B]">
        <AlertTriangle className="w-2.5 h-2.5" />
        degraded
      </span>
    );
  }

  // source === 'snapshot'
  return (
    <span className="inline-flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded border border-white/10 bg-white/5 text-white/50">
      <Database className="w-2.5 h-2.5" />
      snapshot data
    </span>
  );
}

export const AssistantChat: React.FC<AssistantChatProps> = ({ messages, isLoading }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-center text-white/40 select-none font-mono">
        <Bot className="w-8 h-8 mb-3 text-white/20" />
        <p className="text-sm text-white/60">Ask a question about the current traffic situation.</p>
        <p className="text-xs mt-1 text-white/40">
          Try: &ldquo;Which junction has the highest queue?&rdquo; or &ldquo;Camera status?&rdquo;
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3 overflow-y-auto max-h-80 pr-1">
      {messages.map((msg) => {
        const isUser = msg.role === 'user';
        return (
          <div
            key={msg.id}
            className={`flex gap-2.5 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
          >
            {/* Avatar */}
            <div
              className={`w-6 h-6 rounded flex-shrink-0 flex items-center justify-center mt-0.5 ${isUser ? 'bg-[#45C982] text-[#080D10]' : 'bg-white/5 border border-white/10 text-white/60'
                }`}
            >
              {isUser ? (
                <User className="w-3.5 h-3.5" />
              ) : (
                <Bot className="w-3.5 h-3.5" />
              )}
            </div>

            {/* Bubble */}
            <div className={`flex flex-col gap-1 max-w-[80%] ${isUser ? 'items-end' : 'items-start'}`}>
              <div
                className={`px-3.5 py-2.5 rounded-lg text-xs leading-relaxed ${isUser
                    ? 'bg-[#45C982]/15 border border-[#45C982]/30 text-white'
                    : 'bg-[#080D10] border border-white/10 text-white/90 shadow-sm'
                  }`}
              >
                <p className="whitespace-pre-wrap">{msg.content}</p>
              </div>

              {/* Message metadata */}
              <div className="flex items-center gap-2 px-1">
                <span className="text-[10px] text-white/30 font-mono">
                  {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                </span>
                <SourceBadge source={msg.source} status={msg.status} />
              </div>
            </div>
          </div>
        );
      })}

      {isLoading && (
        <div className="flex gap-2.5">
          <div className="w-6 h-6 rounded bg-white/5 border border-white/10 flex items-center justify-center mt-0.5">
            <Bot className="w-3.5 h-3.5 text-[#45C982]" />
          </div>
          <div className="bg-[#080D10] border border-white/10 px-3.5 py-2 rounded-lg text-xs text-white/50 flex items-center gap-2 font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-[#45C982] animate-pulse" />
            <span>Analyzing situation…</span>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
};
