import React, { useState, useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout, Spin } from 'antd'
import { useAuth } from './hooks/useAuth'
import { useAppContext } from './contexts/AppContext'
import MainWindow from './components/MainWindow'
import LoginPage from './pages/LoginPage'
import SettingsPage from './pages/SettingsPage'
import ProjectPage from './pages/ProjectPage'
import WelcomePage from './pages/WelcomePage'

const { Content } = Layout

const App: React.FC = () => {
  const { isAuthenticated, loading } = useAuth()
  const { isDarkMode } = useAppContext()
  const [isReady, setIsReady] = useState(false)

  useEffect(() => {
    // 等待应用初始化完成
    const timer = setTimeout(() => {
      setIsReady(true)
    }, 1000)

    return () => clearTimeout(timer)
  }, [])

  if (loading || !isReady) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        background: isDarkMode ? '#1f1f1f' : '#f5f5f5'
      }}>
        <Spin size="large" tip="正在启动视频草稿..." />
      </div>
    )
  }

  return (
    <Layout style={{ height: '100vh', background: isDarkMode ? '#1f1f1f' : '#f5f5f5' }}>
      <Content style={{ overflow: 'hidden' }}>
        <Routes>
          <Route 
            path="/login" 
            element={
              isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />
            } 
          />
          <Route 
            path="/settings" 
            element={
              isAuthenticated ? <SettingsPage /> : <Navigate to="/login" replace />
            } 
          />
          <Route 
            path="/project/:id" 
            element={
              isAuthenticated ? <ProjectPage /> : <Navigate to="/login" replace />
            } 
          />
          <Route 
            path="/dashboard" 
            element={
              isAuthenticated ? <MainWindow /> : <Navigate to="/login" replace />
            } 
          />
          <Route 
            path="/" 
            element={
              isAuthenticated ? <Navigate to="/dashboard" replace /> : <WelcomePage />
            } 
          />
        </Routes>
      </Content>
    </Layout>
  )
}

export default App