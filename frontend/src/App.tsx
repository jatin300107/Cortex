import { useState, useCallback, useMemo } from 'react';
import { useChat } from './hooks/useChat';
import { Conversation } from './types';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';

export default function App() {
  const { messages, isLoading, sendMessage, retryLastMessage, clearMessages } = useChat();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [repoPath, setRepoPath] = useState('');
  const [repoType, setRepoType] = useState('github');

  const conversations: Conversation[] = useMemo(() => [], []);

  const handleSend = useCallback(
    (message: string) => {
      sendMessage({ message, path: repoPath, repo_type: repoType });
    },
    [sendMessage, repoPath, repoType]
  );

  const handleRetry = useCallback(() => {
    retryLastMessage(repoPath, repoType);
  }, [retryLastMessage, repoPath, repoType]);

  const handleNewChat = useCallback(() => {
    clearMessages();
  }, [clearMessages]);

  const handleSuggestionClick = useCallback(
    (text: string) => {
      handleSend(text);
    },
    [handleSend]
  );

  return (
    <div className="flex flex-col h-screen bg-surface">
      <Header
        onNewChat={handleNewChat}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen((p) => !p)}
      />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar isOpen={sidebarOpen} conversations={conversations} />
        <main className="flex-1 flex flex-col min-w-0 relative">
          <ChatWindow
            messages={messages}
            isLoading={isLoading}
            onRetry={handleRetry}
            onSuggestionClick={handleSuggestionClick}
          />
          <ChatInput
            onSend={handleSend}
            isLoading={isLoading}
            repoPath={repoPath}
            repoType={repoType}
            onRepoPathChange={setRepoPath}
            onRepoTypeChange={setRepoType}
          />
        </main>
      </div>
    </div>
  );
}
