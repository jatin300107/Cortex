import { MessageSquare, Clock } from 'lucide-react';
import { Conversation } from '../types';

interface SidebarProps {
  isOpen: boolean;
  conversations: Conversation[];
}

const PLACEHOLDER_CONVERSATIONS: Conversation[] = [
  {
    id: '1',
    title: 'Getting started with Cortex',
    lastMessage: 'How do I analyze a repository?',
    timestamp: new Date(),
  },
];

export default function Sidebar({ isOpen, conversations }: SidebarProps) {
  const displayConversations = conversations.length > 0 ? conversations : PLACEHOLDER_CONVERSATIONS;

  return (
    <aside
      className={`${
        isOpen ? 'w-64' : 'w-0'
      } flex-shrink-0 border-r border-border bg-surface-50 overflow-hidden transition-all duration-300 ease-in-out`}
    >
      <div className="w-64 h-full flex flex-col">
        <div className="px-4 py-3 border-b border-border">
          <div className="flex items-center gap-2 text-xs text-zinc-500 font-medium uppercase tracking-wider">
            <Clock size={12} />
            Recent
          </div>
        </div>

        <div className="flex-1 overflow-y-auto py-2 px-2">
          {displayConversations.map((conv) => (
            <button
              key={conv.id}
              className="w-full text-left p-2.5 rounded-lg hover:bg-surface-200 transition-colors duration-150 group mb-0.5"
            >
              <div className="flex items-start gap-2.5">
                <MessageSquare
                  size={14}
                  className="text-zinc-600 group-hover:text-cortex-400 mt-0.5 flex-shrink-0 transition-colors"
                />
                <div className="min-w-0">
                  <p className="text-[13px] text-zinc-300 group-hover:text-white truncate font-medium transition-colors">
                    {conv.title}
                  </p>
                  <p className="text-[11px] text-zinc-600 truncate mt-0.5">
                    {conv.lastMessage}
                  </p>
                </div>
              </div>
            </button>
          ))}
        </div>

        <div className="p-3 border-t border-border">
          <p className="text-[10px] text-zinc-600 text-center">Cortex v1.0</p>
        </div>
      </div>
    </aside>
  );
}
