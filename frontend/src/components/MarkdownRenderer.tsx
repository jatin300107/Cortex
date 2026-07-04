import { useState, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { Copy, Check } from 'lucide-react';
import type { Components } from 'react-markdown';

interface MarkdownRendererProps {
  content: string;
}

function CodeBlock({ className, children }: { className?: string; children: React.ReactNode }) {
  const [copied, setCopied] = useState(false);
  const match = /language-(\w+)/.exec(className || '');
  const language = match ? match[1] : '';
  const codeString = String(children).replace(/\n$/, '');

  const handleCopy = useCallback(async () => {
    await navigator.clipboard.writeText(codeString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [codeString]);

  return (
    <div className="relative group">
      <div className="flex items-center justify-between px-4 py-2 bg-surface-200/60 border-b border-border">
        <span className="text-[11px] font-medium text-zinc-500 font-mono uppercase tracking-wide">
          {language || 'code'}
        </span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 text-[11px] text-zinc-500 hover:text-zinc-300 transition-colors"
          aria-label="Copy code"
        >
          {copied ? (
            <>
              <Check size={12} className="text-emerald-400" />
              <span className="text-emerald-400">Copied</span>
            </>
          ) : (
            <>
              <Copy size={12} />
              <span className="opacity-0 group-hover:opacity-100 transition-opacity">Copy</span>
            </>
          )}
        </button>
      </div>
      <code className={className}>{children}</code>
    </div>
  );
}

const components: Components = {
  pre({ children }) {
    return <pre>{children}</pre>;
  },
  code({ className, children, ...props }) {
    const isBlock = className?.includes('language-') || className?.includes('hljs');
    if (isBlock) {
      return <CodeBlock className={className}>{children}</CodeBlock>;
    }
    return (
      <code className={className} {...props}>
        {children}
      </code>
    );
  },
  a({ href, children }) {
    return (
      <a href={href} target="_blank" rel="noopener noreferrer">
        {children}
      </a>
    );
  },
};

export default function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <div className="markdown-body">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
