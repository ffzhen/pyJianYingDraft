import axios from 'axios'
import { electronAPI } from './electron'

// 获取 API 基础 URL
const getApiBaseUrl = async () => {
  try {
    const settings = await electronAPI.getSettings()
    return settings.network?.apiUrl || 'http://localhost:5000/api'
  } catch (error) {
    return 'http://localhost:5000/api'
  }
}

// 创建 axios 实例
const createApiInstance = async () => {
  const baseURL = await getApiBaseUrl()
  
  const api = axios.create({
    baseURL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json'
    }
  })

  // 请求拦截器
  api.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    },
    (error) => {
      return Promise.reject(error)
    }
  )

  // 响应拦截器
  api.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }
  )

  return api
}

// 用户相关接口
export interface User {
  id: string
  username: string
  email: string
  profile?: {
    firstName?: string
    lastName?: string
    avatar?: string
    bio?: string
  }
  preferences?: {
    theme: 'light' | 'dark'
    language: string
    notifications: boolean
  }
  subscription?: {
    type: 'free' | 'premium'
    expiresAt?: Date
  }
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
}

export interface AuthResponse {
  message: string
  token: string
  user: User
}

export const authService = {
  async login(data: LoginRequest): Promise<AuthResponse> {
    const api = await createApiInstance()
    const response = await api.post('/auth/login', data)
    return response.data
  },

  async register(data: RegisterRequest): Promise<AuthResponse> {
    const api = await createApiInstance()
    const response = await api.post('/auth/register', data)
    return response.data
  },

  async getCurrentUser(): Promise<{ user: User }> {
    const api = await createApiInstance()
    const response = await api.get('/auth/me')
    return response.data
  },

  async updateProfile(data: Partial<User>): Promise<{ message: string; user: User }> {
    const api = await createApiInstance()
    const response = await api.put('/auth/profile', data)
    return response.data
  },

  async changePassword(data: { currentPassword: string; newPassword: string }): Promise<{ message: string }> {
    const api = await createApiInstance()
    const response = await api.post('/auth/change-password', data)
    return response.data
  }
}

// 项目相关接口
export interface Project {
  id: string
  title: string
  description?: string
  user: string
  projectData: any
  exportSettings: any
  status: 'draft' | 'rendering' | 'completed' | 'failed'
  tags: string[]
  isPublic: boolean
  views: number
  likes: number
  createdAt: string
  updatedAt: string
}

export const projectService = {
  async getProjects(params?: { page?: number; limit?: number; status?: string }): Promise<{ 
    projects: Project[]; 
    pagination: any 
  }> {
    const api = await createApiInstance()
    const response = await api.get('/videos', { params })
    return response.data
  },

  async getProject(id: string): Promise<{ project: Project }> {
    const api = await createApiInstance()
    const response = await api.get(`/videos/${id}`)
    return response.data
  },

  async createProject(data: { title: string; description?: string; projectData?: any }): Promise<{ 
    message: string; 
    project: Project 
  }> {
    const api = await createApiInstance()
    const response = await api.post('/videos', data)
    return response.data
  },

  async updateProject(id: string, data: Partial<Project>): Promise<{ 
    message: string; 
    project: Project 
  }> {
    const api = await createApiInstance()
    const response = await api.put(`/videos/${id}`, data)
    return response.data
  },

  async deleteProject(id: string): Promise<{ message: string }> {
    const api = await createApiInstance()
    const response = await api.delete(`/videos/${id}`)
    return response.data
  },

  async duplicateProject(id: string): Promise<{ 
    message: string; 
    project: Project 
  }> {
    const api = await createApiInstance()
    const response = await api.post(`/videos/${id}/duplicate`)
    return response.data
  }
}

// 文件上传接口
export const fileService = {
  async uploadFile(file: File, type: 'video' | 'audio' | 'image'): Promise<{ 
    url: string; 
    filename: string; 
    size: number 
  }> {
    const api = await createApiInstance()
    const formData = new FormData()
    formData.append('file', file)
    formData.append('type', type)

    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  async deleteFile(filename: string): Promise<{ message: string }> {
    const api = await createApiInstance()
    const response = await api.delete(`/upload/${filename}`)
    return response.data
  }
}