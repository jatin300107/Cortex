import { useEffect, useRef } from 'react';
import { Message } from '../types';
import MessageBubble from './MessageBubble';
import LoadingIndicator from './LoadingIndicator';
import EmptyState from './EmptyState';

interface ChatWindowProps {
  messages: Message[];
  isLoading: boolean;
  onRetry: () => void;
  onSuggestionClick: (text: string) => void;
}

export default function ChatWindow({
  messages,
  isLoading,
  onRetry,
  onSuggestionClick,
}: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages or loading state change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  if (messages.length === 0 && !isLoading) {
    return <EmptyState onSuggestionClick={onSuggestionClick} />;
  }

  return (
    <div ref={containerRef} className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto px-4 py-6 space-y-5">
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            onRetry={message.status === 'error' ? onRetry : undefined}
          />
        ))}
        {isLoading && <LoadingIndicator />}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
