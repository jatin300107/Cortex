import { useState, useCallback } from 'react';
import { Copy, Check, RotateCcw } from 'lucide-react';
import { Message } from '../types';
import MarkdownRenderer from './MarkdownRenderer';

interface MessageBubbleProps {
  message: Message;
  onRetry?: () => void;
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export default function MessageBubble({ message, onRetry }: MessageBubbleProps) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';
  const isError = message.status === 'error';

  const handleCopy = useCallback(async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [message.content]);

  return (
    <div
      className={`flex items-start gap-3 animate-slide-up ${
        isUser ? 'flex-row-reverse' : ''
      }`}
    >
      {/* Avatar */}
      {isUser ? (
        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-zinc-600 to-zinc-700 flex items-center justify-center flex-shrink-0 mt-0.5">
          <span className="text-[11px] font-semibold text-zinc-200">U</span>
        </div>
      ) : (
        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-cortex-500 to-cortex-700 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-md shadow-cortex-500/10">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" className="text-white">
            <path
              d="M12 3C7.03 3 3 7.03 3 12s4.03 9 9 9 9-4.03 9-9-4.03-9-9-9zm0 3.5a5.5 5.5 0 110 11 5.5 5.5 0 010-11z"
              fill="currentColor"
              fillOpacity="0.9"
            />
          </svg>
        </div>
      )}

      {/* Message Content */}
      <div className={`max-w-[75%] min-w-0 group ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`rounded-2xl px-4 py-2.5 ${
            isUser
              ? 'bg-cortex-600 text-white rounded-tr-md'
              : isError
              ? 'bg-red-500/8 border border-red-500/20 rounded-tl-md'
              : 'bg-surface-100 border border-border rounded-tl-md'
          }`}
        >
          {isUser ? (
            <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
          ) : (
            <MarkdownRenderer content={message.content} />
          )}
        </div>

        {/* Meta Row */}
        <div
          className={`flex items-center gap-2 mt-1.5 px-1 ${
            isUser ? 'justify-end' : 'justify-start'
          }`}
        >
          <span className="text-[10px] text-zinc-600">{formatTime(message.timestamp)}</span>

          {!isUser && (
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={handleCopy}
                className="p-1 rounded-md hover:bg-surface-200 text-zinc-600 hover:text-zinc-400 transition-colors"
                aria-label="Copy message"
              >
                {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
              </button>
              {isError && onRetry && (
                <button
                  onClick={onRetry}
                  className="flex items-center gap-1 px-1.5 py-0.5 rounded-md hover:bg-surface-200 text-zinc-600 hover:text-zinc-400 transition-colors"
                  aria-label="Retry"
                >
                  <RotateCcw size={12} />
                  <span className="text-[10px]">Retry</span>
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
