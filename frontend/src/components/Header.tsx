import { Brain, Plus, PanelLeftClose, PanelLeft } from 'lucide-react';

interface HeaderProps {
  onNewChat: () => void;
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
}

export default function Header({ onNewChat, sidebarOpen, onToggleSidebar }: HeaderProps) {
  return (
    <header className="h-14 flex items-center justify-between px-4 border-b border-border bg-surface-50/80 backdrop-blur-xl z-20 relative">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-surface-300 transition-all duration-200"
          aria-label="Toggle sidebar"
        >
          {sidebarOpen ? <PanelLeftClose size={18} /> : <PanelLeft size={18} />}
        </button>
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cortex-400 to-cortex-600 flex items-center justify-center shadow-lg shadow-cortex-500/20">
            <Brain size={18} className="text-white" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-white tracking-tight leading-none">Cortex</h1>
            <p className="text-[10px] text-zinc-500 font-medium tracking-wider uppercase mt-0.5">Repository Intelligence</p>
          </div>
        </div>
      </div>
      <button
        onClick={onNewChat}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-zinc-300 hover:text-white bg-surface-200 hover:bg-surface-300 border border-border hover:border-border-hover transition-all duration-200"
      >
        <Plus size={14} />
        New Chat
      </button>
    </header>
  );
}
