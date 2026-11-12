import { useMutation } from '@tanstack/react-query';
import { useCallback, useState } from 'react';
import { postQuestion, postVQAQuestion } from '../services/api/aegisApi';
import { ChatMessage, JunctionId, QuestionRequest, VQARequest } from '../types/api';

function generateId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `id-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

export function useAiAssistant() {
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [sessionId] = useState(() => generateId());

  // --- text Q&A mutation ---
  const questionMutation = useMutation({
    mutationFn: (payload: QuestionRequest) => postQuestion(payload),
    onMutate: (payload) => {
      // Append user message immediately (non-authoritative display)
      const userMsg: ChatMessage = {
        id: generateId(),
        role: 'user',
        content: payload.question,
        timestamp: new Date().toISOString(),
        junction_id: payload.junction_id ?? null,
      };
      setChatHistory((prev) => [...prev, userMsg]);
      return { userMsg };
    },
    onSuccess: (data) => {
      const assistantMsg: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: data.answer,
        timestamp: data.timestamp,
        source: data.source,
        junction_id: data.junction_id ?? null,
        status: data.status,
        data_quality: data.data_quality,
      };
      setChatHistory((prev) => [...prev, assistantMsg]);
    },
    onError: (error: Error) => {
      const errorMsg: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: `Error: ${error.message}`,
        timestamp: new Date().toISOString(),
        source: 'degraded',
        status: 'ERROR',
      };
      setChatHistory((prev) => [...prev, errorMsg]);
    },
  });

  // --- VQA mutation ---
  const vqaMutation = useMutation({
    mutationFn: (payload: VQARequest) => postVQAQuestion(payload),
    onMutate: (payload) => {
      const userMsg: ChatMessage = {
        id: generateId(),
        role: 'user',
        content: payload.junction_id
          ? `[Camera ${payload.junction_id}] ${payload.question}`
          : `[Camera frame] ${payload.question}`,
        timestamp: new Date().toISOString(),
        junction_id: payload.junction_id ?? null,
      };
      setChatHistory((prev) => [...prev, userMsg]);
    },
    onSuccess: (data) => {
      const assistantMsg: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: data.answer,
        timestamp: data.timestamp,
        source: data.source,
        junction_id: data.junction_id ?? null,
        status: data.status,
        data_quality: data.data_quality,
      };
      setChatHistory((prev) => [...prev, assistantMsg]);
    },
    onError: (error: Error) => {
      const errorMsg: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: `VQA error: ${error.message}`,
        timestamp: new Date().toISOString(),
        source: 'degraded',
        status: 'ERROR',
      };
      setChatHistory((prev) => [...prev, errorMsg]);
    },
  });

  const submitQuestion = useCallback(
    (question: string, junctionId: JunctionId | null) => {
      if (!question.trim() || questionMutation.isPending) return;
      questionMutation.mutate({
        question: question.trim(),
        junction_id: junctionId ?? undefined,
        session_id: sessionId,
      });
    },
    [questionMutation, sessionId]
  );

  const submitVQA = useCallback(
    (imageB64: string | undefined, question: string, junctionId: JunctionId | null) => {
      if (!question.trim() || (!imageB64 && !junctionId) || vqaMutation.isPending) return;
      vqaMutation.mutate({
        image_b64: imageB64 || undefined,
        question: question.trim(),
        junction_id: junctionId ?? undefined,
        session_id: sessionId,
      });
    },
    [vqaMutation, sessionId]
  );

  const clearHistory = useCallback(() => setChatHistory([]), []);

  return {
    chatHistory,
    submitQuestion,
    submitVQA,
    clearHistory,
    isQuestionPending: questionMutation.isPending,
    isVQAPending: vqaMutation.isPending,
    isPending: questionMutation.isPending || vqaMutation.isPending,
    sessionId,
  };
}

