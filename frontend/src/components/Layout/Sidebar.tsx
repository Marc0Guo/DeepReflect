import { useEffect, useRef, useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'

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
  {
    to: '/settings', label: 'Settings',
    icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>,
  },
]

export function Sidebar() {
  const location = useLocation()
  const navRef = useRef<HTMLElement>(null)
  const [pill, setPill] = useState({ top: 0, height: 40, ready: false })

  // Slide pill to whichever nav item is active
  useEffect(() => {
    if (!navRef.current) return
    const activePath = location.pathname === '/'
      ? '/'
      : '/' + location.pathname.split('/')[1]
    const el = navRef.current.querySelector<HTMLElement>(`[data-navpath="${activePath}"]`)
    if (el) {
      setPill({ top: el.offsetTop, height: el.offsetHeight, ready: true })
    }
  }, [location.pathname])

  return (
    <aside className="sidebar-rail w-[220px] shrink-0 flex flex-col py-5 px-3 relative z-10">
      {/* Logo */}
      <div className="px-3 mb-8 flex items-center gap-2.5 mt-1">
        <div className="w-7 h-7 rounded-[10px] flex items-center justify-center"
          style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent-secondary))' }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
          </svg>
        </div>
        <span className="font-display text-sm font-bold tracking-wide" style={{ color: 'var(--text-primary)' }}>
          Deep<span style={{ color: 'var(--accent)' }}>Reflect</span>
        </span>
      </div>

      <div className="section-label px-3 mb-2">Navigate</div>

      <nav ref={navRef} className="flex flex-col gap-1 relative">
        {/* Liquid sliding pill — positioned behind links */}
        {pill.ready && (
          <div
            aria-hidden
            className="absolute inset-x-0 pointer-events-none"
            style={{
              top: pill.top,
              height: pill.height,
              borderRadius: 14,
              background: 'color-mix(in srgb, var(--accent) 10%, transparent)',
              transition: 'top 0.42s cubic-bezier(0.34,1.56,0.64,1), height 0.3s ease',
            }}
          />
        )}

        {links.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            data-navpath={to}
            className="flex items-center gap-3 px-3 py-2.5 rounded-[14px] text-[13px] font-medium transition-colors duration-200 group"
            style={({ isActive }) => ({
              color: isActive ? 'var(--accent)' : 'var(--text-muted)',
              background: 'transparent',
              position: 'relative', // sit above the pill
              zIndex: 1,
            })}
          >
            {({ isActive }) => (
              <>
                <span
                  className="transition-all duration-200"
                  style={{
                    opacity: isActive ? 1 : 0.55,
                    transform: isActive ? 'scale(1.05)' : 'scale(1)',
                  }}
                >
                  {icon}
                </span>
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto px-3 pt-4" style={{ borderTop: '1px solid var(--divider-subtle)' }}>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full animate-pulse" style={{ background: 'var(--accent-green)' }} />
          <span className="text-[11px]" style={{ color: 'var(--text-faint)' }}>Local agent active</span>
        </div>
      </div>
    </aside>
  )
}
