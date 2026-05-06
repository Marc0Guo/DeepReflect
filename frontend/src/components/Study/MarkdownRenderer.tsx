import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Props {
  content: string
}

export function MarkdownRenderer({ content }: Props) {
  return (
    <div className="markdown-body">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        children={content}
        components={{
          h1: ({ children }) => (
            <h1 className="font-display text-2xl font-extrabold mt-2 mb-4 tracking-tight" style={{ color: 'var(--text-primary)' }}>{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="font-display text-xl font-bold mt-8 mb-3 pb-2 flex items-center gap-2" style={{ color: 'var(--text-primary)', borderBottom: '1px solid var(--glass-border)' }}>
              <span className="w-1 h-5 rounded-full inline-block" style={{ background: 'var(--accent)' }} />
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="font-display text-base font-bold mt-6 mb-2" style={{ color: 'var(--accent)' }}>{children}</h3>
          ),
          p: ({ children }) => (
            <p className="text-sm leading-relaxed mb-3" style={{ color: 'var(--text-secondary)' }}>{children}</p>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold" style={{ color: 'var(--text-primary)' }}>{children}</strong>
          ),
          em: ({ children }) => (
            <em className="not-italic font-medium" style={{ color: 'var(--accent)', opacity: 0.8 }}>{children}</em>
          ),
          ul: ({ children }) => <ul className="space-y-2 mb-4">{children}</ul>,
          ol: ({ children }) => <ol className="space-y-2 mb-4 list-decimal list-inside">{children}</ol>,
          li: ({ children }) => (
            <li className="text-sm leading-relaxed flex gap-2" style={{ color: 'var(--text-secondary)' }}>
              <span className="mt-0.5 shrink-0" style={{ color: 'var(--accent)', opacity: 0.5 }}>•</span>
              <span className="flex-1">{children}</span>
            </li>
          ),
          code: ({ className, children }) => {
            const isBlock = className?.includes('language-')
            if (isBlock) {
              return (
                <div className="my-4 rounded-[14px] overflow-hidden" style={{ background: 'var(--surface-raised)', border: '1px solid var(--glass-border)' }}>
                  <div className="px-4 py-1.5" style={{ background: 'var(--glass)', borderBottom: '1px solid var(--glass-border)' }}>
                    <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-faint)' }}>{className?.replace('language-', '') || 'code'}</span>
                  </div>
                  <pre className="p-4 overflow-x-auto"><code className="text-[13px] font-mono leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{children}</code></pre>
                </div>
              )
            }
            return (
              <code className="text-[13px] font-mono px-1.5 py-0.5 rounded-md" style={{ background: 'color-mix(in srgb, var(--accent) 10%, transparent)', color: 'var(--accent)', border: '1px solid color-mix(in srgb, var(--accent) 15%, transparent)' }}>{children}</code>
            )
          },
          blockquote: ({ children }) => (
            <blockquote className="pl-4 my-4 italic" style={{ borderLeft: '2px solid color-mix(in srgb, var(--accent) 30%, transparent)', color: 'var(--text-muted)' }}>{children}</blockquote>
          ),
          hr: () => (
            <hr className="my-6 border-0 h-px" style={{ background: 'linear-gradient(90deg, transparent, var(--glass-border), transparent)' }} />
          ),
        }}
      />
    </div>
  )
}
