import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import './index.css'
import { Shell } from './components/ui'
import Queue from './pages/Queue'
import CaseReview from './pages/CaseReview'
import { LeadPage, LeadsList } from './pages/Leads'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Shell>
        <Routes>
          <Route path="/" element={<Queue />} />
          <Route path="/cases/:id" element={<CaseReview />} />
          <Route path="/leads" element={<LeadsList />} />
          <Route path="/leads/:id" element={<LeadPage />} />
          <Route path="/patterns" element={<Navigate to="/leads" replace />} />
        </Routes>
      </Shell>
    </BrowserRouter>
  </StrictMode>,
)
