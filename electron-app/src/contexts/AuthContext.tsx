import React, { createContext, useContext, useState, useEffect } from 'react'
import { message } from 'antd'
import { authService, User, LoginRequest, RegisterRequest } from '../services/api'

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  loading: boolean
  login: (credentials: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => void
  updateProfile: (data: Partial<User>) => Promise<void>
  changePassword: (data: { currentPassword: string; newPassword: string }) => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: React.ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('token')
      if (token) {
        try {
          const response = await authService.getCurrentUser()
          setUser(response.user)
        } catch (error) {
          console.error('Failed to get current user:', error)
          localStorage.removeItem('token')
          localStorage.removeItem('user')
        }
      }
      setLoading(false)
    }

    initAuth()
  }, [])

  const login = async (credentials: LoginRequest) => {
    try {
      const response = await authService.login(credentials)
      localStorage.setItem('token', response.token)
      localStorage.setItem('user', JSON.stringify(response.user))
      setUser(response.user)
      message.success('登录成功')
    } catch (error: any) {
      console.error('Login failed:', error)
      throw new Error(error.response?.data?.error || '登录失败')
    }
  }

  const register = async (data: RegisterRequest) => {
    try {
      const response = await authService.register(data)
      localStorage.setItem('token', response.token)
      localStorage.setItem('user', JSON.stringify(response.user))
      setUser(response.user)
      message.success('注册成功')
    } catch (error: any) {
      console.error('Registration failed:', error)
      throw new Error(error.response?.data?.error || '注册失败')
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
    message.success('已退出登录')
  }

  const updateProfile = async (data: Partial<User>) => {
    try {
      const response = await authService.updateProfile(data)
      localStorage.setItem('user', JSON.stringify(response.user))
      setUser(response.user)
      message.success('个人资料更新成功')
    } catch (error: any) {
      console.error('Profile update failed:', error)
      throw new Error(error.response?.data?.error || '更新失败')
    }
  }

  const changePassword = async (data: { currentPassword: string; newPassword: string }) => {
    try {
      await authService.changePassword(data)
      message.success('密码修改成功')
    } catch (error: any) {
      console.error('Password change failed:', error)
      throw new Error(error.response?.data?.error || '密码修改失败')
    }
  }

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    loading,
    login,
    register,
    logout,
    updateProfile,
    changePassword
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}