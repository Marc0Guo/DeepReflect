import { useEffect } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { Sidebar } from './components/Layout/Sidebar'
import { ThemeToggle } from './components/Layout/ThemeToggle'
import { DashboardPage } from './pages/DashboardPage'
import { GraphPage } from './pages/GraphPage'
import { SettingsPage } from './pages/SettingsPage'
import { StudyPage } from './pages/StudyPage'
import { SummaryPage } from './pages/SummaryPage'

const GLASS_SELECTOR = '.glass, .glass-strong, .glass-subtle, .liquid-glass'

export function App() {
  useEffect(() => {
    const saved = localStorage.getItem('dr-theme') || 'dark'
    document.documentElement.setAttribute('data-theme', saved)
  }, [])

  // Silky mouse-following spotlight via lerp + requestAnimationFrame.
  // Rather than snapping --mouse-x/y to the cursor every mousemove event,
  // we lerp the stored position toward the target each frame (60fps).
  // This gives the spotlight a liquid "glide" quality.
  useEffect(() => {
    let active: HTMLElement | null = null
    // Separate current/target per axis so we can interpolate
    let tx = 50, ty = 50   // target  (updated on mousemove)
    let cx = 50, cy = 50   // current (lerped toward target)
    let rafId = 0
    const LERP = 0.10      // 0.06 = very dreamy, 0.14 = snappier

    function onMove(e: MouseEvent) {
      const el = (e.target as HTMLElement).closest<HTMLElement>(GLASS_SELECTOR)
      if (active && active !== el) {
        // When leaving an element, reset so next entry starts fresh
        if (active) {
          const r = active.getBoundingClientRect()
          cx = ((e.clientX - r.left) / r.width) * 100
          cy = ((e.clientY - r.top)  / r.height) * 100
        }
      }
      if (el) {
        const r = el.getBoundingClientRect()
        tx = ((e.clientX - r.left) / r.width) * 100
        ty = ((e.clientY - r.top)  / r.height) * 100
      }
      active = el
    }

    function tick() {
      if (active) {
        cx += (tx - cx) * LERP
        cy += (ty - cy) * LERP
        active.style.setProperty('--mouse-x', `${cx.toFixed(2)}%`)
        active.style.setProperty('--mouse-y', `${cy.toFixed(2)}%`)
      }
      rafId = requestAnimationFrame(tick)
    }

    window.addEventListener('mousemove', onMove, { passive: true })
    rafId = requestAnimationFrame(tick)
    return () => {
      window.removeEventListener('mousemove', onMove)
      cancelAnimationFrame(rafId)
    }
  }, [])

  return (
    <BrowserRouter>
      <div className="flex h-screen overflow-hidden font-body relative">
        <div className="mesh-bg" />
        <Sidebar />
        <main className="flex-1 overflow-y-auto relative z-10">
          <div className="fixed top-5 right-6 z-50">
            <ThemeToggle />
          </div>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/graph" element={<GraphPage />} />
            <Route path="/study" element={<StudyPage />} />
            <Route path="/summary" element={<SummaryPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
