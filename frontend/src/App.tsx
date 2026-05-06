import { useEffect } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { Sidebar } from './components/Layout/Sidebar'
import { ThemeToggle } from './components/Layout/ThemeToggle'
import { DashboardPage } from './pages/DashboardPage'
import { GraphPage } from './pages/GraphPage'
import { StudyPage } from './pages/StudyPage'
import { SummaryPage } from './pages/SummaryPage'

export function App() {
  useEffect(() => {
    const saved = localStorage.getItem('dr-theme') || 'dark'
    document.documentElement.setAttribute('data-theme', saved)
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
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
