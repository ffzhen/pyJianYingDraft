import api from './api'

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
    const response = await api.post('/auth/login', data)
    return response.data
  },

  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await api.post('/auth/register', data)
    return response.data
  },

  async getCurrentUser(): Promise<{ user: User }> {
    const response = await api.get('/auth/me')
    return response.data
  },

  async updateProfile(data: Partial<User>): Promise<{ message: string; user: User }> {
    const response = await api.put('/auth/profile', data)
    return response.data
  },

  async changePassword(data: { currentPassword: string; newPassword: string }): Promise<{ message: string }> {
    const response = await api.post('/auth/change-password', data)
    return response.data
  },

  logout() {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    window.location.href = '/login'
  }
}