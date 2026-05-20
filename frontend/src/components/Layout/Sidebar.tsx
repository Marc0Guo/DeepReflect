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

  const [pinned, setPinned] = useState(() => {
    if (typeof window === 'undefined') return true
    return localStorage.getItem('dr-sidebar-pinned') !== 'false'
  })
  const [hovering, setHovering] = useState(false)
  const hoverTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const visible = pinned || hovering

  function handleEdgeEnter() {
    if (pinned) return
    hoverTimer.current = setTimeout(() => setHovering(true), 80)
  }
  function handleSidebarLeave() {
    if (hoverTimer.current) clearTimeout(hoverTimer.current)
    if (!pinned) setHovering(false)
  }

  // Slide pill to whichever nav item is active
  useEffect(() => {
    if (!navRef.current) return
    const activePath = location.pathname === '/'
      ? '/'
      : '/' + location.pathname.split('/')[1]
    const el = navRef.current.querySelector<HTMLElement>(`[data-navpath="${activePath}"]`)
    if (el) setPill({ top: el.offsetTop, height: el.offsetHeight, ready: true })
  }, [location.pathname])

  function togglePin() {
    if (pinned) {
      setPinned(false)
      localStorage.setItem('dr-sidebar-pinned', 'false')
    } else {
      // Sidebar visible via hover — close it
      setHovering(false)
    }
  }

  return (
    <>
      {/* Flex spacer — always rendered, width animates to push content */}
      <div
        style={{
          width: visible ? 220 : 0,
          flexShrink: 0,
          transition: 'width 0.38s cubic-bezier(0.4, 0, 0.2, 1)',
        }}
      />

      {/* Edge hover zone — thin invisible strip at left when collapsed */}
      {!pinned && (
        <div
          className="fixed left-0 top-0 h-full z-40"
          style={{ width: 18 }}
          onMouseEnter={handleEdgeEnter}
        />
      )}

      {/* Sidebar — always fixed so it can slide in/out smoothly */}
      <aside
        className="fixed flex flex-col py-5 px-3 glass z-40"
        style={{
          width: 220,
          top: 12,
          bottom: 12,
          left: 0,
          borderRadius: '0 20px 20px 0',
          borderLeft: 'none',
          transform: visible ? 'translateX(0)' : 'translateX(calc(-100% - 4px))',
          transition: 'transform 0.38s cubic-bezier(0.4, 0, 0.2, 1)',
          willChange: 'transform',
        }}
        onMouseEnter={() => { if (!pinned) { if (hoverTimer.current) clearTimeout(hoverTimer.current); setHovering(true) } }}
        onMouseLeave={handleSidebarLeave}
      >
        {/* Logo + toggle */}
        <div className="px-3 mb-8 flex items-center gap-2.5 mt-1">
          <div
            className="w-7 h-7 rounded-[10px] flex items-center justify-center shrink-0"
            style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent-secondary))' }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
            </svg>
          </div>
          <span className="font-display text-sm font-bold tracking-wide flex-1 truncate" style={{ color: 'var(--text-primary)' }}>
            Deep<span style={{ color: 'var(--accent)' }}>Reflect</span>
          </span>

          {/* Collapse / pin toggle button */}
          <button
            onClick={togglePin}
            title="Collapse sidebar"
            className="w-6 h-6 rounded-full flex items-center justify-center cursor-pointer transition-all duration-200 hover:scale-110 active:scale-95 shrink-0"
            style={{
              background: 'var(--surface-raised)',
              color: 'var(--text-faint)',
              border: '1px solid var(--border-divider)',
            }}
          >
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="15 18 9 12 15 6" />
            </svg>
          </button>
        </div>

        <div className="section-label px-3 mb-2">Navigate</div>

        <nav ref={navRef} className="flex flex-col gap-1 relative">
          {/* Liquid sliding pill */}
          {pill.ready && (
            <div
              aria-hidden
              className="absolute inset-x-0 pointer-events-none"
              style={{
                top: pill.top,
                height: pill.height,
                borderRadius: 99,
                background: 'var(--surface-pill)',
                backdropFilter: 'blur(8px)',
                WebkitBackdropFilter: 'blur(8px)',
                boxShadow: 'var(--tab-pill-shadow)',
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
              className="flex items-center gap-3 px-3 py-2.5 rounded-[14px] text-[13px] font-medium transition-colors duration-200"
              style={({ isActive }) => ({
                color: isActive ? 'var(--accent)' : 'var(--text-muted)',
                background: 'transparent',
                position: 'relative',
                zIndex: 1,
              })}
            >
              {({ isActive }) => (
                <>
                  <span
                    className="transition-all duration-200 shrink-0"
                    style={{
                      opacity: isActive ? 1 : 0.55,
                      transform: isActive ? 'scale(1.05)' : 'scale(1)',
                    }}
                  >
                    {icon}
                  </span>
                  <span className="truncate">{label}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto px-3 pt-4" style={{ borderTop: '1px solid var(--border-divider)' }}>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full shrink-0 animate-pulse" style={{ background: 'var(--accent-green)' }} />
            <span className="text-[11px] truncate" style={{ color: 'var(--text-faint)' }}>Local agent active</span>
          </div>
        </div>
      </aside>
    </>
  )
}
