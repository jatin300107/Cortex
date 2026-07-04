export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  status: 'sending' | 'sent' | 'error';
}

export interface ChatRequest {
  message: string;
  path: string;
  repo_type: string;
}

export interface Conversation {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
}

export type RepoType = 'github' | 'local' | 'gitlab' | 'bitbucket';

export const REPO_TYPES: { value: RepoType; label: string }[] = [
  { value: 'github', label: 'GitHub' },
  { value: 'local', label: 'Local' },
  { value: 'gitlab', label: 'GitLab' },
  { value: 'bitbucket', label: 'Bitbucket' },
];
