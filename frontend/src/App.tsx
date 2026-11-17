import React, { lazy, Suspense, useEffect, useState } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Layout, Spin } from 'antd'
import { AuthProvider } from './context/AuthContext'
import PrototypeHeader from './components/Layout/PrototypeHeader'
import PrototypeSider from './components/Layout/PrototypeSider'
import './styles/prototype-theme.css'

const { Content } = Layout

const PrototypeHome = lazy(() => import('./pages/PrototypeHome'))
const PrescriptionAnalysis = lazy(() => import('./pages/PrescriptionAnalysis'))
const PrescriptionOptimization = lazy(() => import('./pages/PrescriptionOptimization'))
const PrescriptionComparison = lazy(() => import('./pages/PrescriptionComparison'))
const HerbKnowledge = lazy(() => import('./pages/HerbKnowledge'))
const PrescriptionDatabase = lazy(() => import('./pages/PrescriptionDatabase'))
const EvidenceSearch = lazy(() => import('./pages/EvidenceSearch'))
const Help = lazy(() => import('./pages/Help'))
const Guide = lazy(() => import('./pages/Guide'))
const SmartPrescription = lazy(() => import('./pages/SmartPrescription'))
const SimilarityRadar = lazy(() => import('./pages/SimilarityRadar'))
const DataVisualization = lazy(() => import('./pages/DataVisualization'))
const HerbRecognition = lazy(() => import('./pages/HerbRecognition'))
const EfficacyPrediction = lazy(() => import('./pages/EfficacyPrediction'))
const AdminManagement = lazy(() => import('./pages/AdminManagement'))

const PageFallback = (
  <div style={{ minHeight: 320, display: 'grid', placeItems: 'center' }}>
    <Spin size="large" />
  </div>
)

const App: React.FC = () => {
  const [siderCollapsed, setSiderCollapsed] = useState(() =>
    typeof window !== 'undefined' ? window.innerWidth < 980 : false,
  )

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 980) setSiderCollapsed(true)
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return (
    <AuthProvider>
      <Router>
        <Layout className="prototype-app-shell">
          <PrototypeHeader />
          <Layout className="prototype-body" style={{ marginTop: 68 }}>
            <PrototypeSider
              collapsed={siderCollapsed}
              onCollapsedChange={setSiderCollapsed}
            />
            <Layout
              className="prototype-main-layout"
              style={{
                marginLeft: siderCollapsed ? 64 : 200,
                transition: 'margin-left 0.25s ease',
              }}
            >
              <Content className="prototype-content">
                <Suspense fallback={PageFallback}>
                  <Routes>
                    <Route path="/" element={<PrototypeHome />} />
                    <Route path="/home" element={<PrototypeHome />} />
                    <Route path="/analysis" element={<PrescriptionAnalysis />} />
                    <Route path="/efficacy" element={<EfficacyPrediction />} />
                    <Route path="/admin" element={<AdminManagement />} />
                    <Route path="/smart" element={<SmartPrescription />} />
                    <Route path="/similarity" element={<SimilarityRadar />} />
                    <Route path="/visualization" element={<DataVisualization />} />
                    <Route path="/recognize" element={<HerbRecognition />} />
                    <Route path="/optimization" element={<PrescriptionOptimization />} />
                    <Route path="/comparison" element={<PrescriptionComparison />} />
                    <Route path="/herbs" element={<HerbKnowledge />} />
                    <Route path="/database" element={<PrescriptionDatabase />} />
                    <Route path="/evidence" element={<EvidenceSearch />} />
                    <Route path="/help" element={<Help />} />
                    <Route path="/guide" element={<Guide />} />
                  </Routes>
                </Suspense>
              </Content>
            </Layout>
          </Layout>
        </Layout>
      </Router>
    </AuthProvider>
  )
}

export default App
