import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import styled from 'styled-components'
import Header from '@/components/Header'
import Footer from '@/components/Footer'
import HomePage from '@/pages/HomePage'
import LoginPage from '@/pages/LoginPage'
import RegisterPage from '@/pages/RegisterPage'
import FeaturesPage from '@/pages/FeaturesPage'
import PricingPage from '@/pages/PricingPage'
import DownloadPage from '@/pages/DownloadPage'
import ProtectedRoute from '@/components/ProtectedRoute'
import DashboardPage from '@/pages/DashboardPage'

const AppContainer = styled.div`
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
`

const MainContent = styled.main`
  flex: 1;
`

function App() {
  return (
    <AppContainer>
      <Helmet>
        <title>视频草稿 - 专业视频编辑工具</title>
        <meta name="description" content="专业的视频编辑工具，支持多平台，让您轻松创建精彩视频内容" />
      </Helmet>
      
      <Header />
      
      <MainContent>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/features" element={<FeaturesPage />} />
          <Route path="/pricing" element={<PricingPage />} />
          <Route path="/download" element={<DownloadPage />} />
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            } 
          />
        </Routes>
      </MainContent>
      
      <Footer />
    </AppContainer>
  )
}

export default App