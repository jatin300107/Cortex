import { Brain, Code2, GitBranch, Zap } from 'lucide-react';

interface EmptyStateProps {
  onSuggestionClick: (text: string) => void;
}

const SUGGESTIONS = [
  {
    icon: Code2,
    label: 'Explain the architecture',
    prompt: 'Explain the overall architecture of this repository',
  },
  {
    icon: GitBranch,
    label: 'Find dependencies',
    prompt: 'What are the main dependencies in this project?',
  },
  {
    icon: Zap,
    label: 'Identify patterns',
    prompt: 'What design patterns are used in this codebase?',
  },
];

export default function EmptyState({ onSuggestionClick }: EmptyStateProps) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4 animate-fade-in">
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cortex-400/20 to-cortex-600/20 border border-cortex-500/20 flex items-center justify-center mb-6">
        <Brain size={32} className="text-cortex-400" />
      </div>
      <h2 className="text-xl font-semibold text-white mb-2">Welcome to Cortex</h2>
      <p className="text-sm text-zinc-500 text-center max-w-md mb-8 leading-relaxed">
        AI-powered repository intelligence. Enter a repository path below and start
        exploring your codebase with natural language.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full max-w-xl">
        {SUGGESTIONS.map((s) => (
          <button
            key={s.label}
            onClick={() => onSuggestionClick(s.prompt)}
            className="group flex flex-col items-start gap-2 p-3.5 rounded-xl bg-surface-100 border border-border hover:border-cortex-500/30 hover:bg-surface-200 transition-all duration-200 text-left"
          >
            <s.icon size={16} className="text-cortex-400 group-hover:text-cortex-300 transition-colors" />
            <span className="text-xs text-zinc-400 group-hover:text-zinc-300 transition-colors font-medium">
              {s.label}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
