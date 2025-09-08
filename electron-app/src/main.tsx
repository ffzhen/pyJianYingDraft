import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from 'react-query'
import { ConfigProvider, theme } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { Toaster } from 'react-hot-toast'
import App from './App'
import { AppProvider } from './contexts/AppContext'
import { AuthProvider } from './contexts/AuthContext'
import './styles/index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AppProvider>
        <AuthProvider>
          <BrowserRouter>
            <ConfigProvider
              locale={zhCN}
              theme={{
                algorithm: theme.defaultAlgorithm,
                token: {
                  colorPrimary: '#667eea',
                },
              }}
            >
              <App />
              <Toaster position="top-right" />
            </ConfigProvider>
          </BrowserRouter>
        </AuthProvider>
      </AppProvider>
    </QueryClientProvider>
  </React.StrictMode>,
)