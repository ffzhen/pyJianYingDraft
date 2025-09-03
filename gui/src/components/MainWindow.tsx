import React, { useState, useEffect } from 'react'
import { Layout, Menu, Button, Avatar, Dropdown, Space, Typography, message, theme } from 'antd'
import {
  VideoCameraOutlined,
  AppstoreOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  PlusOutlined,
  FolderOpenOutlined,
  CloudUploadOutlined,
  ExportOutlined,
  InfoCircleOutlined
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useAppContext } from '../contexts/AppContext'
import styled from 'styled-components'

const { Header, Sider, Content } = Layout
const { Text } = Typography

const StyledLayout = styled(Layout)`
  height: 100vh;
`

const StyledHeader = styled(Header)`
  background: ${props => props.isDarkMode ? '#1f1f1f' : '#fff'};
  border-bottom: 1px solid ${props => props.isDarkMode ? '#303030' : '#f0f0f0'};
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
`

const Logo = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: bold;
  color: #667eea;
`

const ContentArea = styled(Content)`
  background: ${props => props.isDarkMode ? '#141414' : '#f5f5f5'};
  overflow-y: auto;
`

const WelcomeCard = styled.div`
  background: ${props => props.isDarkMode ? '#1f1f1f' : '#fff'};
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
`

const ActionCard = styled.div`
  background: ${props => props.isDarkMode ? '#1f1f1f' : '#fff'};
  border-radius: 8px;
  padding: 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  
  &:hover {
    border-color: #667eea;
    transform: translateY(-2px);
  }
`

const MainWindow: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuth()
  const { isDarkMode, appVersion, recentProjects, showNotification } = useAppContext()
  const [collapsed, setCollapsed] = useState(false)

  const menuItems = [
    {
      key: '/dashboard',
      icon: <AppstoreOutlined />,
      label: '工作台',
    },
    {
      key: '/projects',
      icon: <FolderOpenOutlined />,
      label: '项目管理',
    },
    {
      key: '/templates',
      icon: <VideoCameraOutlined />,
      label: '模板库',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '设置',
    },
  ]

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
      onClick: () => {
        showNotification('info', '个人资料功能开发中')
      },
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
      onClick: () => {
        navigate('/settings')
      },
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: logout,
    },
  ]

  const handleNewProject = () => {
    showNotification('info', '新建项目功能开发中')
  }

  const handleOpenProject = async () => {
    try {
      const result = await window.electronAPI.showOpenDialog({
        properties: ['openFile'],
        filters: [
          { name: '视频项目', extensions: ['vdp'] },
          { name: '所有文件', extensions: ['*'] }
        ]
      })

      if (result.filePaths && result.filePaths.length > 0) {
        showNotification('success', `打开项目: ${result.filePaths[0]}`)
      }
    } catch (error) {
      showNotification('error', '打开项目失败')
    }
  }

  const handleImportMedia = async () => {
    try {
      const result = await window.electronAPI.showOpenDialog({
        properties: ['openFile', 'multiSelections'],
        filters: [
          { name: '视频文件', extensions: ['mp4', 'mov', 'avi', 'mkv'] },
          { name: '音频文件', extensions: ['mp3', 'wav', 'aac'] },
          { name: '图片文件', extensions: ['jpg', 'png', 'gif', 'bmp'] },
          { name: '所有文件', extensions: ['*'] }
        ]
      })

      if (result.filePaths && result.filePaths.length > 0) {
        showNotification('success', `导入 ${result.filePaths.length} 个文件`)
      }
    } catch (error) {
      showNotification('error', '导入媒体失败')
    }
  }

  const handleExport = () => {
    showNotification('info', '导出功能开发中')
  }

  const quickActions = [
    {
      icon: <PlusOutlined style={{ fontSize: '32px', color: '#667eea' }} />,
      title: '新建项目',
      description: '创建一个新的视频项目',
      onClick: handleNewProject
    },
    {
      icon: <FolderOpenOutlined style={{ fontSize: '32px', color: '#667eea' }} />,
      title: '打开项目',
      description: '打开已有的项目文件',
      onClick: handleOpenProject
    },
    {
      icon: <CloudUploadOutlined style={{ fontSize: '32px', color: '#667eea' }} />,
      title: '导入媒体',
      description: '导入视频、音频、图片文件',
      onClick: handleImportMedia
    },
    {
      icon: <ExportOutlined style={{ fontSize: '32px', color: '#667eea' }} />,
      title: '导出视频',
      description: '导出编辑好的视频文件',
      onClick: handleExport
    }
  ]

  return (
    <StyledLayout>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        style={{ background: isDarkMode ? '#1f1f1f' : '#fff' }}
      >
        <div style={{ padding: '16px', textAlign: 'center' }}>
          <Logo>
            <VideoCameraOutlined />
            {!collapsed && '视频草稿'}
          </Logo>
        </div>
        
        <Menu
          theme={isDarkMode ? 'dark' : 'light'}
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          style={{ border: 'none' }}
        />
      </Sider>

      <Layout>
        <StyledHeader isDarkMode={isDarkMode}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <Button
              type="text"
              icon={collapsed ? <VideoCameraOutlined /> : <VideoCameraOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              style={{ marginRight: 16 }}
            />
            <Text strong>视频草稿桌面版</Text>
          </div>

          <Space size="middle">
            <Text type="secondary">v{appVersion}</Text>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Button type="text" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Avatar size="small" icon={<UserOutlined />} />
                {user?.username || '用户'}
              </Button>
            </Dropdown>
          </Space>
        </StyledHeader>

        <ContentArea isDarkMode={isDarkMode}>
          <div style={{ padding: '24px' }}>
            <WelcomeCard>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h2 style={{ margin: 0, color: isDarkMode ? '#fff' : '#000' }}>
                    欢迎回来，{user?.username}！
                  </h2>
                  <p style={{ margin: '8px 0 0 0', color: isDarkMode ? '#bfbfbf' : '#666' }}>
                    开始您的视频创作之旅
                  </p>
                </div>
                <Space>
                  <Button type="primary" icon={<PlusOutlined />} onClick={handleNewProject}>
                    新建项目
                  </Button>
                  <Button icon={<FolderOpenOutlined />} onClick={handleOpenProject}>
                    打开项目
                  </Button>
                </Space>
              </div>
            </WelcomeCard>

            <div style={{ marginBottom: '24px' }}>
              <h3 style={{ color: isDarkMode ? '#fff' : '#000', marginBottom: '16px' }}>
                快速操作
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                {quickActions.map((action, index) => (
                  <ActionCard key={index} onClick={action.onClick} isDarkMode={isDarkMode}>
                    <div style={{ marginBottom: '16px' }}>
                      {action.icon}
                    </div>
                    <h4 style={{ margin: '0 0 8px 0', color: isDarkMode ? '#fff' : '#000' }}>
                      {action.title}
                    </h4>
                    <p style={{ margin: 0, color: isDarkMode ? '#bfbfbf' : '#666', fontSize: '14px' }}>
                      {action.description}
                    </p>
                  </ActionCard>
                ))}
              </div>
            </div>

            {recentProjects.length > 0 && (
              <div>
                <h3 style={{ color: isDarkMode ? '#fff' : '#000', marginBottom: '16px' }}>
                  最近项目
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
                  {recentProjects.slice(0, 6).map((project, index) => (
                    <WelcomeCard key={index}>
                      <h4 style={{ margin: '0 0 8px 0', color: isDarkMode ? '#fff' : '#000' }}>
                        {project.name}
                      </h4>
                      <p style={{ margin: 0, color: isDarkMode ? '#bfbfbf' : '#666', fontSize: '12px' }}>
                        {project.path}
                      </p>
                      <p style={{ margin: '8px 0 0 0', color: isDarkMode ? '#bfbfbf' : '#666', fontSize: '12px' }}>
                        最后访问: {new Date(project.lastAccessed).toLocaleDateString()}
                      </p>
                    </WelcomeCard>
                  ))}
                </div>
              </div>
            )}
          </div>
        </ContentArea>
      </Layout>
    </StyledLayout>
  )
}

export default MainWindow