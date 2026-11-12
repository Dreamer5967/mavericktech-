import React, { KeyboardEvent, useRef, useState } from 'react';
import { Send } from 'lucide-react';
import { JunctionId } from '../../types/api';

const JUNCTION_OPTIONS: { value: JunctionId | ''; label: string }[] = [
  { value: '', label: 'All junctions' },
  { value: 'J1', label: 'J1' },
  { value: 'J2', label: 'J2' },
  { value: 'J3', label: 'J3' },
  { value: 'J4', label: 'J4' },
];

const MAX_LENGTH = 500;

interface AssistantInputProps {
  onSubmit: (question: string, junctionId: JunctionId | null) => void;
  disabled: boolean;
}

export const AssistantInput: React.FC<AssistantInputProps> = ({ onSubmit, disabled }) => {
  const [question, setQuestion] = useState('');
  const [junctionId, setJunctionId] = useState<JunctionId | ''>('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = () => {
    const q = question.trim();
    if (!q || disabled) return;
    onSubmit(q, junctionId || null);
    setQuestion('');
    textareaRef.current?.focus();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const remaining = MAX_LENGTH - question.length;
  const isOverLimit = remaining < 0;

  return (
    <div className="border-t border-[#E5E5E5] pt-3 space-y-2">
      {/* Junction filter */}
      <div className="flex items-center gap-2">
        <label className="text-xs text-[#737373] whitespace-nowrap">Focus on:</label>
        <select
          value={junctionId}
          onChange={(e) => setJunctionId(e.target.value as JunctionId | '')}
          disabled={disabled}
          className="text-xs border border-[#E5E5E5] rounded px-2 py-1 bg-white text-[#262626] focus:outline-none focus:ring-1 focus:ring-[#171717] disabled:opacity-50"
        >
          {JUNCTION_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Text input row */}
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={question}
            onChange={(e) => setQuestion(e.target.value.slice(0, MAX_LENGTH + 10))}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            rows={2}
            placeholder="Ask about traffic conditions, camera status, signal phases…"
            className={`w-full text-sm border rounded px-3 py-2 resize-none focus:outline-none focus:ring-1 focus:ring-[#171717] transition-colors disabled:opacity-50 ${
              isOverLimit
                ? 'border-[#C0392B] bg-[#FFF5F5]'
                : 'border-[#E5E5E5] bg-white text-[#262626]'
            }`}
          />
          {/* Character counter */}
          <span
            className={`absolute bottom-1.5 right-2 text-[10px] font-mono ${
              isOverLimit ? 'text-[#C0392B]' : remaining < 50 ? 'text-[#B7791F]' : 'text-[#A3A3A3]'
            }`}
          >
            {remaining}
          </span>
        </div>

        <button
          onClick={handleSubmit}
          disabled={disabled || !question.trim() || isOverLimit}
          className="self-end px-3 py-2 rounded border border-[#171717] bg-[#171717] text-white text-xs font-medium hover:bg-[#262626] transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5"
        >
          <Send className="w-3.5 h-3.5" />
          Ask
        </button>
      </div>

      <p className="text-[10px] text-[#A3A3A3]">
        Press Enter to send · Shift+Enter for new line · Answers sourced from live snapshot data only
      </p>
    </div>
  );
};

