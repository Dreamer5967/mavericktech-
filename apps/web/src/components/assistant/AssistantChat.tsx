import React, { useEffect, useRef } from 'react';
import { Bot, User, Loader2, AlertTriangle, Database, Eye, Sparkles } from 'lucide-react';
import { ChatMessage } from '../../types/api';

interface AssistantChatProps {
  messages: ChatMessage[];
  isLoading: boolean;
}

function SourceBadge({ source, status }: { source?: string; status?: string }) {
  if (!source) return null;

  if (status === 'ERROR') {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded border border-[#C0392B]/30 bg-[#FFF5F5] text-[#C0392B]">
        <AlertTriangle className="w-2.5 h-2.5" />
        error
      </span>
    );
  }

  if (source === 'gemini') {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded border border-[#23865A]/30 bg-[#F0FDF4] text-[#23865A]">
        <Sparkles className="w-2.5 h-2.5" />
        gemini vision estimate
      </span>
    );
  }

  if (source === 'vqa_model') {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded border border-[#B7791F]/30 bg-[#FFFBEB] text-[#B7791F]">
        <Eye className="w-2.5 h-2.5" />
        estimate — not a measurement
      </span>
    );
  }

  if (source === 'degraded') {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded border border-[#B7791F]/30 bg-[#FFFBEB] text-[#B7791F]">
        <AlertTriangle className="w-2.5 h-2.5" />
        degraded
      </span>
    );
  }

  // source === 'snapshot'
  return (
    <span className="inline-flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded border border-[#E5E5E5] bg-[#F5F5F5] text-[#737373]">
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
      <div className="flex flex-col items-center justify-center h-48 text-center text-[#A3A3A3] select-none">
        <Bot className="w-8 h-8 mb-3 text-[#D4D4D4]" />
        <p className="text-sm text-[#737373]">Ask a question about the current traffic situation.</p>
        <p className="text-xs mt-1">
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
            className={`flex gap-2 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
          >
            {/* Avatar */}
            <div
              className={`w-6 h-6 rounded flex-shrink-0 flex items-center justify-center mt-0.5 ${
                isUser ? 'bg-[#171717]' : 'bg-[#F5F5F5] border border-[#E5E5E5]'
              }`}
            >
              {isUser ? (
                <User className="w-3.5 h-3.5 text-white" />
              ) : (
                <Bot className="w-3.5 h-3.5 text-[#737373]" />
              )}
            </div>

            {/* Bubble */}
            <div className={`flex flex-col gap-1 max-w-[75%] ${isUser ? 'items-end' : 'items-start'}`}>
              <div
                className={`px-3 py-2 rounded text-sm leading-relaxed whitespace-pre-wrap ${
                  isUser
                    ? 'bg-[#171717] text-white rounded-tr-sm'
                    : 'bg-[#F5F5F5] border border-[#E5E5E5] text-[#262626] rounded-tl-sm'
                }`}
              >
                {msg.content}
              </div>

              {/* Source badge + timestamp */}
              {!isUser && (
                <div className="flex items-center gap-2 flex-wrap">
                  <SourceBadge source={msg.source} status={msg.status} />
                  <span className="text-[10px] text-[#A3A3A3] font-mono">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </span>
                  {msg.junction_id && (
                    <span className="text-[10px] text-[#A3A3A3] font-mono">· {msg.junction_id}</span>
                  )}
                </div>
              )}
            </div>
          </div>
        );
      })}

      {/* Loading indicator */}
      {isLoading && (
        <div className="flex gap-2 flex-row">
          <div className="w-6 h-6 rounded flex-shrink-0 flex items-center justify-center mt-0.5 bg-[#F5F5F5] border border-[#E5E5E5]">
            <Bot className="w-3.5 h-3.5 text-[#737373]" />
          </div>
          <div className="px-3 py-2 rounded bg-[#F5F5F5] border border-[#E5E5E5] flex items-center gap-2">
            <Loader2 className="w-3.5 h-3.5 text-[#737373] animate-spin" />
            <span className="text-xs text-[#737373]">Processing…</span>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
};

