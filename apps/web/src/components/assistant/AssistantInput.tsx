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
    <div className="border-t border-white/10 pt-3 space-y-2">
      {/* Junction filter */}
      <div className="flex items-center gap-2">
        <label className="text-xs text-white/50 font-mono whitespace-nowrap">Focus on:</label>
        <select
          value={junctionId}
          onChange={(e) => setJunctionId(e.target.value as JunctionId | '')}
          disabled={disabled}
          className="text-xs font-mono border border-white/15 rounded px-2.5 py-1 bg-[#080D10] text-white focus:outline-none focus:border-[#45C982] focus:ring-1 focus:ring-[#45C982] disabled:opacity-50"
        >
          {JUNCTION_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value} className="bg-[#111A1D] text-white">
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
            className={`w-full text-xs font-mono border rounded px-3 py-2 resize-none focus:outline-none focus:ring-1 focus:ring-[#45C982] focus:border-[#45C982] transition-colors disabled:opacity-50 ${isOverLimit
                ? 'border-red-500 bg-red-500/10 text-white'
                : 'border-white/15 bg-[#080D10] text-white placeholder-white/30'
              }`}
          />
          {/* Character counter */}
          <span
            className={`absolute bottom-1.5 right-2 text-[10px] font-mono ${isOverLimit ? 'text-red-400' : remaining < 50 ? 'text-[#E9A23B]' : 'text-white/30'
              }`}
          >
            {remaining}
          </span>
        </div>

        <button
          onClick={handleSubmit}
          disabled={disabled || !question.trim() || isOverLimit}
          className="self-end px-3.5 py-2.5 rounded bg-[#45C982] text-[#080D10] font-mono text-xs font-bold hover:bg-[#3db874] transition-all disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-1.5 cursor-pointer shadow-sm shadow-[#45C982]/20"
        >
          <Send className="w-3.5 h-3.5" />
          <span>Ask</span>
        </button>
      </div>

      <p className="text-[10px] font-mono text-white/30">
        Press Enter to send · Shift+Enter for newline · Real-time snapshot evaluation only
      </p>
    </div>
  );
};
