import { useMutation, useQuery, useQueryClient } from 'react-query'
import { authService, LoginRequest, RegisterRequest } from '../services/auth'
import { message } from 'antd'

export const useAuth = () => {
  const queryClient = useQueryClient()

  const loginMutation = useMutation(
    (credentials: LoginRequest) => authService.login(credentials),
    {
      onSuccess: (data) => {
        localStorage.setItem('token', data.token)
        localStorage.setItem('user', JSON.stringify(data.user))
        queryClient.setQueryData('user', data.user)
        message.success('登录成功')
      },
      onError: (error: any) => {
        message.error(error.response?.data?.error || '登录失败')
      }
    }
  )

  const registerMutation = useMutation(
    (data: RegisterRequest) => authService.register(data),
    {
      onSuccess: (data) => {
        localStorage.setItem('token', data.token)
        localStorage.setItem('user', JSON.stringify(data.user))
        queryClient.setQueryData('user', data.user)
        message.success('注册成功')
      },
      onError: (error: any) => {
        message.error(error.response?.data?.error || '注册失败')
      }
    }
  )

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    queryClient.setQueryData('user', null)
    queryClient.clear()
    message.success('已退出登录')
  }

  return {
    loginMutation,
    registerMutation,
    logout
  }
}

export const useUser = () => {
  return useQuery(
    'user',
    () => authService.getCurrentUser(),
    {
      enabled: !!localStorage.getItem('token'),
      retry: 1,
      onError: () => {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
      }
    }
  )
}