import { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { Spin } from 'antd'

interface ProtectedRouteProps {
  children: ReactNode
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const token = localStorage.getItem('token')
  
  if (!token) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

export default ProtectedRoute