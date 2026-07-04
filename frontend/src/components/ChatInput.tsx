import { useState, useRef, useCallback, KeyboardEvent, useEffect } from 'react';
import { Send, FolderOpen, ChevronDown } from 'lucide-react';
import { REPO_TYPES } from '../types';

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  repoPath: string;
  repoType: string;
  onRepoPathChange: (path: string) => void;
  onRepoTypeChange: (type: string) => void;
}

export default function ChatInput({
  onSend,
  isLoading,
  repoPath,
  repoType,
  onRepoPathChange,
  onRepoTypeChange,
}: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const canSend = message.trim().length > 0 && !isLoading;

  const handleSend = useCallback(() => {
    if (!canSend) return;
    onSend(message.trim());
    setMessage('');
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, [canSend, message, onSend]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    // Auto-resize
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  };

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const selectedLabel = REPO_TYPES.find((r) => r.value === repoType)?.label || repoType;

  return (
    <div className="border-t border-border bg-surface-50/80 backdrop-blur-xl">
      <div className="max-w-3xl mx-auto px-4 py-3">
        {/* Repository Controls */}
        <div className="flex items-center gap-2 mb-2.5">
          {/* Path Input */}
          <div className="flex-1 flex items-center gap-2 bg-surface-200 border border-border rounded-lg px-3 py-1.5 focus-within:border-cortex-500/40 transition-colors">
            <FolderOpen size={14} className="text-zinc-500 flex-shrink-0" />
            <input
              type="text"
              value={repoPath}
              onChange={(e) => onRepoPathChange(e.target.value)}
              placeholder="Repository path (e.g. C:\Users\project or /home/user/project)"
              className="flex-1 bg-transparent text-sm text-zinc-200 placeholder:text-zinc-600 outline-none font-mono text-[13px]"
              spellCheck={false}
            />
          </div>

          {/* Repo Type Dropdown */}
          <div ref={dropdownRef} className="relative">
            <button
              onClick={() => setDropdownOpen((o) => !o)}
              className="flex items-center gap-1.5 bg-surface-200 border border-border rounded-lg px-3 py-1.5 text-sm text-zinc-300 hover:border-border-hover transition-colors min-w-[110px] justify-between"
            >
              <span className="text-[13px]">{selectedLabel}</span>
              <ChevronDown
                size={14}
                className={`text-zinc-500 transition-transform ${dropdownOpen ? 'rotate-180' : ''}`}
              />
            </button>
            {dropdownOpen && (
              <div className="absolute bottom-full mb-1 right-0 w-40 bg-surface-100 border border-border rounded-lg shadow-2xl shadow-black/40 overflow-hidden z-50 animate-fade-in">
                {REPO_TYPES.map((rt) => (
                  <button
                    key={rt.value}
                    onClick={() => {
                      onRepoTypeChange(rt.value);
                      setDropdownOpen(false);
                    }}
                    className={`w-full text-left px-3 py-2 text-[13px] hover:bg-surface-200 transition-colors ${
                      repoType === rt.value
                        ? 'text-cortex-400 bg-cortex-500/8'
                        : 'text-zinc-300'
                    }`}
                  >
                    {rt.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Message Input */}
        <div className="flex items-end gap-2">
          <div className="flex-1 bg-surface-200 border border-border rounded-xl px-4 py-2.5 focus-within:border-cortex-500/40 transition-colors">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={handleTextareaChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your repository..."
              rows={1}
              className="w-full bg-transparent text-sm text-zinc-200 placeholder:text-zinc-600 outline-none resize-none leading-relaxed"
              disabled={isLoading}
              style={{ maxHeight: '160px' }}
            />
          </div>
          <button
            onClick={handleSend}
            disabled={!canSend}
            className={`p-2.5 rounded-xl transition-all duration-200 flex-shrink-0 ${
              canSend
                ? 'bg-cortex-600 hover:bg-cortex-500 text-white shadow-lg shadow-cortex-500/20 hover:shadow-cortex-500/30'
                : 'bg-surface-300 text-zinc-600 cursor-not-allowed'
            }`}
            aria-label="Send message"
          >
            <Send size={16} className={isLoading ? 'animate-pulse' : ''} />
          </button>
        </div>

        {/* Help Text */}
        <p className="text-[10px] text-zinc-600 mt-1.5 text-center">
          <kbd className="px-1 py-0.5 bg-surface-200 rounded text-[9px] border border-border">Enter</kbd>
          {' '}to send · {' '}
          <kbd className="px-1 py-0.5 bg-surface-200 rounded text-[9px] border border-border">Shift + Enter</kbd>
          {' '}for new line
        </p>
      </div>
    </div>
  );
}
