import { useState, useCallback, useRef } from 'react';
import { Message, ChatRequest } from '../types';

const API_URL = '/chat/request';

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (request: ChatRequest) => {
      const userMessage: Message = {
        id: generateId(),
        role: 'user',
        content: request.message,
        timestamp: new Date(),
        status: 'sent',
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

      const assistantId = generateId();

      try {
        abortControllerRef.current = new AbortController();

        const response = await fetch(API_URL, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: request.message,
            path: request.path,
            repo_type: request.repo_type,
          }),
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) {
          throw new Error(`Server error: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        const content = typeof data === 'string' ? data : data.response || data.message || data.answer || JSON.stringify(data);

        const assistantMessage: Message = {
          id: assistantId,
          role: 'assistant',
          content,
          timestamp: new Date(),
          status: 'sent',
        };

        setMessages((prev) => [...prev, assistantMessage]);
      } catch (error: unknown) {
        if (error instanceof Error && error.name === 'AbortError') {
          return;
        }

        const errorContent =
          error instanceof Error
            ? error.message
            : 'An unexpected error occurred. Please try again.';

        const errorMessage: Message = {
          id: assistantId,
          role: 'assistant',
          content: `⚠️ **Error:** ${errorContent}`,
          timestamp: new Date(),
          status: 'error',
        };

        setMessages((prev) => [...prev, errorMessage]);
      } finally {
        setIsLoading(false);
        abortControllerRef.current = null;
      }
    },
    []
  );

  const retryLastMessage = useCallback(
    async (path: string, repoType: string) => {
      const lastUserMessage = [...messages].reverse().find((m) => m.role === 'user');
      if (!lastUserMessage) return;

      // Remove the last error message
      setMessages((prev) => {
        const lastIdx = prev.length - 1;
        if (prev[lastIdx]?.status === 'error') {
          return prev.slice(0, lastIdx);
        }
        return prev;
      });

      // Re-send (but we already have the user message, so we need a custom flow)
      setIsLoading(true);
      const assistantId = generateId();

      try {
        abortControllerRef.current = new AbortController();

        const response = await fetch(API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: lastUserMessage.content,
            path,
            repo_type: repoType,
          }),
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) {
          throw new Error(`Server error: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        const content = typeof data === 'string' ? data : data.response || data.message || data.answer || JSON.stringify(data);

        setMessages((prev) => [
          ...prev,
          {
            id: assistantId,
            role: 'assistant',
            content,
            timestamp: new Date(),
            status: 'sent',
          },
        ]);
      } catch (error: unknown) {
        if (error instanceof Error && error.name === 'AbortError') return;
        const errorContent = error instanceof Error ? error.message : 'An unexpected error occurred.';
        setMessages((prev) => [
          ...prev,
          {
            id: assistantId,
            role: 'assistant',
            content: `⚠️ **Error:** ${errorContent}`,
            timestamp: new Date(),
            status: 'error',
          },
        ]);
      } finally {
        setIsLoading(false);
        abortControllerRef.current = null;
      }
    },
    [messages]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    isLoading,
    sendMessage,
    retryLastMessage,
    clearMessages,
  };
}
