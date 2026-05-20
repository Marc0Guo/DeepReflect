export function PageLoader({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <div className="flex flex-col items-center gap-3">
        <div
          className="w-8 h-8 border-2 rounded-full motion-safe:animate-spin"
          style={{
            borderColor: 'color-mix(in srgb, var(--accent) 30%, transparent)',
            borderTopColor: 'var(--accent)',
          }}
        />
        <span className="text-sm" style={{ color: 'var(--text-muted)' }}>
          {label}
        </span>
      </div>
    </div>
  )
}
