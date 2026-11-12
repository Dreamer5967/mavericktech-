import React, { useState } from 'react';
import { Bot, Eye, Trash2, MessageSquare } from 'lucide-react';
import { AssistantChat } from './AssistantChat';
import { AssistantInput } from './AssistantInput';
import { VQAPanel } from './VQAPanel';
import { JunctionId } from '../../types/api';
import { useAiAssistant } from '../../hooks/useAiAssistant';

type AssistantMode = 'chat' | 'vqa';

export const AiAssistantSection: React.FC = () => {
  const [mode, setMode] = useState<AssistantMode>('chat');

  const {
    chatHistory,
    submitQuestion,
    submitVQA,
    clearHistory,
    isQuestionPending,
    isVQAPending,
    isPending,
  } = useAiAssistant();

  return (
    <section className="bg-[#111A1D] border border-white/10 rounded-lg overflow-hidden shadow-sm">
      {/* Section header */}
      <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bot className="w-4 h-4 text-[#45C982]" />
          <span className="text-xs font-display font-semibold text-white">AI Assistant</span>
          <span className="text-xs font-mono text-white/40">· read-only informational</span>
        </div>

        <div className="flex items-center gap-2">
          {/* Mode toggle */}
          <div className="flex border border-white/15 rounded-md overflow-hidden text-xs font-mono">
            <button
              onClick={() => setMode('chat')}
              className={`px-3 py-1 flex items-center gap-1.5 transition-colors cursor-pointer ${mode === 'chat'
                  ? 'bg-[#45C982] text-[#080D10] font-bold'
                  : 'bg-[#080D10] text-white/60 hover:text-white'
                }`}
            >
              <MessageSquare className="w-3 h-3" />
              <span>Text Q&amp;A</span>
            </button>
            <button
              onClick={() => setMode('vqa')}
              className={`px-3 py-1 flex items-center gap-1.5 transition-colors border-l border-white/15 cursor-pointer ${mode === 'vqa'
                  ? 'bg-[#45C982] text-[#080D10] font-bold'
                  : 'bg-[#080D10] text-white/60 hover:text-white'
                }`}
            >
              <Eye className="w-3 h-3" />
              <span>Visual Q&amp;A</span>
            </button>
          </div>

          {/* Clear chat */}
          {chatHistory.length > 0 && (
            <button
              onClick={clearHistory}
              disabled={isPending}
              title="Clear chat history"
              className="p-1 rounded text-white/40 hover:text-red-400 hover:bg-white/5 transition-colors disabled:opacity-40 cursor-pointer"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      <div className="p-4 sm:p-5 space-y-4">
        {mode === 'chat' ? (
          <>
            {/* Chat message thread */}
            <AssistantChat messages={chatHistory} isLoading={isQuestionPending} />

            {/* Question input */}
            <AssistantInput
              onSubmit={(q, jid) => submitQuestion(q, jid as JunctionId | null)}
              disabled={isPending}
            />
          </>
        ) : (
          <>
            {/* VQA messages from same chatHistory */}
            {chatHistory.some((m) => m.source === 'vqa_model' || m.source === 'gemini' || m.content.startsWith('[Camera')) && (
              <div className="mb-4">
                <AssistantChat
                  messages={chatHistory.filter(
                    (m) =>
                      m.source === 'vqa_model' ||
                      m.source === 'gemini' ||
                      m.source === 'degraded' ||
                      m.content.startsWith('[Camera')
                  )}
                  isLoading={isVQAPending}
                />
              </div>
            )}

            {/* VQA input controls */}
            <VQAPanel
              onSubmitVQA={(imgB64, q, jid) => submitVQA(imgB64, q, jid)}
              isPending={isVQAPending}
            />
          </>
        )}
      </div>
    </section>
  );
};
