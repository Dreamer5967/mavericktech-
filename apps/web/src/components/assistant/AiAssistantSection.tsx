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
    <section className="bg-white border border-[#E5E5E5] rounded overflow-hidden">
      {/* Section header */}
      <div className="px-4 py-3 border-b border-[#E5E5E5] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bot className="w-4 h-4 text-[#737373]" />
          <span className="text-xs font-semibold text-[#171717]">AI Assistant</span>
          <span className="text-xs text-[#737373]">· read-only informational</span>
        </div>

        <div className="flex items-center gap-2">
          {/* Mode toggle */}
          <div className="flex border border-[#E5E5E5] rounded overflow-hidden text-xs">
            <button
              onClick={() => setMode('chat')}
              className={`px-2.5 py-1 flex items-center gap-1 transition-colors ${mode === 'chat'
                  ? 'bg-[#171717] text-white'
                  : 'bg-white text-[#737373] hover:bg-[#F5F5F5]'
                }`}
            >
              <MessageSquare className="w-3 h-3" />
              Text Q&amp;A
            </button>
            <button
              onClick={() => setMode('vqa')}
              className={`px-2.5 py-1 flex items-center gap-1 transition-colors border-l border-[#E5E5E5] ${mode === 'vqa'
                  ? 'bg-[#171717] text-white'
                  : 'bg-white text-[#737373] hover:bg-[#F5F5F5]'
                }`}
            >
              <Eye className="w-3 h-3" />
              Visual Q&amp;A
            </button>
          </div>

          {/* Clear chat */}
          {chatHistory.length > 0 && (
            <button
              onClick={clearHistory}
              disabled={isPending}
              title="Clear chat history"
              className="p-1 rounded text-[#737373] hover:text-[#C0392B] hover:bg-[#F5F5F5] transition-colors disabled:opacity-40"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      <div className="p-4 space-y-4">
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
              <div className="mb-2">
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

            {/* VQA input panel */}
            <VQAPanel
              onSubmitVQA={(b64, q, jid) => submitVQA(b64, q, jid as JunctionId | null)}
              isPending={isVQAPending}
            />
          </>
        )}

        {/* Role boundary notice */}
        <p className="text-[10px] text-[#A3A3A3] border-t border-[#E5E5E5] pt-2">
          The AI Assistant is read-only and has no access to control endpoints.
          It cannot inject faults or trigger resets.
          Answers are sourced from live snapshot data only — no fabrication.
        </p>
      </div>
    </section>
  );
};

