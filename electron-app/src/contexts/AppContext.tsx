import React, { createContext, useContext, useState, useEffect } from 'react'
import { message } from 'antd'

interface AppContextType {
  isDarkMode: boolean
  setIsDarkMode: (dark: boolean) => void
  isOnline: boolean
  appVersion: string
  systemInfo: any
  recentProjects: any[]
  settings: any
  updateSettings: (key: string, value: any) => void
  addRecentProject: (project: any) => void
  removeRecentProject: (path: string) => void
  showNotification: (type: 'success' | 'error' | 'warning' | 'info', message: string, description?: string) => void
}

const AppContext = createContext<AppContextType | undefined>(undefined)

export const useAppContext = () => {
  const context = useContext(AppContext)
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider')
  }
  return context
}

interface AppProviderProps {
  children: React.ReactNode
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [isDarkMode, setIsDarkMode] = useState(false)
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  const [appVersion, setAppVersion] = useState('')
  const [systemInfo, setSystemInfo] = useState<any>({})
  const [recentProjects, setRecentProjects] = useState<any[]>([])
  const [settings, setSettings] = useState<any>({})

  useEffect(() => {
    // 获取应用版本
    const getAppVersion = async () => {
      try {
        const version = await window.electronAPI.getAppVersion()
        setAppVersion(version)
      } catch (error) {
        console.error('Failed to get app version:', error)
      }
    }

    // 获取系统信息
    const getSystemInfo = async () => {
      try {
        const info = await window.electronAPI.getSystemInfo()
        setSystemInfo(info)
      } catch (error) {
        console.error('Failed to get system info:', error)
      }
    }

    // 获取设置
    const getSettings = async () => {
      try {
        const appSettings = await window.electronAPI.getSettings()
        setSettings(appSettings)
        setIsDarkMode(appSettings.general?.theme === 'dark')
      } catch (error) {
        console.error('Failed to get settings:', error)
      }
    }

    // 获取最近项目
    const getRecentProjects = async () => {
      try {
        const projects = await window.electronAPI.getRecentProjects()
        setRecentProjects(projects)
      } catch (error) {
        console.error('Failed to get recent projects:', error)
      }
    }

    getAppVersion()
    getSystemInfo()
    getSettings()
    getRecentProjects()
  }, [])

  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  const updateSettings = async (key: string, value: any) => {
    try {
      await window.electronAPI.updateSettings(key, value)
      setSettings(prev => ({ ...prev, [key]: value }))
      
      if (key === 'general.theme') {
        setIsDarkMode(value === 'dark')
      }
    } catch (error) {
      console.error('Failed to update settings:', error)
      message.error('设置更新失败')
    }
  }

  const addRecentProject = async (project: any) => {
    try {
      await window.electronAPI.addRecentProject(project)
      setRecentProjects(prev => {
        const filtered = prev.filter(p => p.path !== project.path)
        return [project, ...filtered].slice(0, 10)
      })
    } catch (error) {
      console.error('Failed to add recent project:', error)
    }
  }

  const removeRecentProject = async (path: string) => {
    try {
      await window.electronAPI.removeRecentProject(path)
      setRecentProjects(prev => prev.filter(p => p.path !== path))
    } catch (error) {
      console.error('Failed to remove recent project:', error)
    }
  }

  const showNotification = (type: 'success' | 'error' | 'warning' | 'info', message: string, description?: string) => {
    if (type === 'error') {
      message.error(message)
    } else if (type === 'success') {
      message.success(message)
    } else if (type === 'warning') {
      message.warning(message)
    } else {
      message.info(message)
    }
  }

  const value: AppContextType = {
    isDarkMode,
    setIsDarkMode,
    isOnline,
    appVersion,
    systemInfo,
    recentProjects,
    settings,
    updateSettings,
    addRecentProject,
    removeRecentProject,
    showNotification
  }

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  )
}