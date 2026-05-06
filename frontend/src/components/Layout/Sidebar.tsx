import { NavLink } from 'react-router-dom'

const links = [
  {
    to: '/', label: 'Dashboard',
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="4" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="11" width="7" height="10" rx="1.5"/></svg>,
  },
  {
    to: '/graph', label: 'Knowledge Graph',
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="6" cy="6" r="3"/><circle cx="18" cy="18" r="3"/><circle cx="18" cy="6" r="3"/><line x1="8.5" y1="7.5" x2="15.5" y2="16.5"/><line x1="15" y1="6" x2="9" y2="6"/></svg>,
  },
  {
    to: '/study', label: 'Study',
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>,
  },
  {
    to: '/summary', label: 'Summaries',
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>,
  },
]

export function Sidebar() {
  return (
    <aside className="w-[220px] shrink-0 flex flex-col py-5 px-3 relative z-10 glass" style={{ borderRadius: '0 20px 20px 0', borderLeft: 'none', margin: '12px 0 12px 0' }}>
      <div className="px-3 mb-8 flex items-center gap-2.5 mt-1">
        <div className="w-7 h-7 rounded-[10px] flex items-center justify-center" style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent-secondary))' }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
          </svg>
        </div>
        <span className="font-display text-sm font-bold tracking-wide" style={{ color: 'var(--text-primary)' }}>
          Deep<span style={{ color: 'var(--accent)' }}>Reflect</span>
        </span>
      </div>

      <div className="section-label px-3 mb-2">Navigate</div>

      <nav className="flex flex-col gap-1">
        {links.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-[14px] text-[13px] font-medium transition-all duration-200 group ${isActive ? '' : 'hover:bg-[var(--surface-raised)]'}`
            }
            style={({ isActive }) => ({
              color: isActive ? 'var(--accent)' : 'var(--text-muted)',
              background: isActive ? 'color-mix(in srgb, var(--accent) 12%, transparent)' : undefined,
              boxShadow: isActive ? 'inset 0 0 0 1px color-mix(in srgb, var(--accent) 20%, transparent)' : undefined,
            })}
          >
            <span className="opacity-70 group-hover:opacity-100 transition-opacity">{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto px-3 pt-4" style={{ borderTop: '1px solid var(--glass-border)' }}>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full animate-pulse" style={{ background: 'var(--accent-green)' }} />
          <span className="text-[11px]" style={{ color: 'var(--text-faint)' }}>Local agent active</span>
        </div>
      </div>
    </aside>
  )
}
