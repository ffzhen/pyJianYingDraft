import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Button, Layout, Menu, Avatar, Dropdown, Space } from 'antd'
import {
  HomeOutlined,
  VideoCameraOutlined,
  DollarOutlined,
  DownloadOutlined,
  UserOutlined,
  LogoutOutlined,
  DashboardOutlined,
  LoginOutlined,
  UserAddOutlined
} from '@ant-design/icons'
import styled from 'styled-components'

const { Header: AntHeader } = Layout

const StyledHeader = styled(AntHeader)`
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  padding: 0 50px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
`

const Logo = styled(Link)`
  font-size: 24px;
  font-weight: bold;
  color: #667eea;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 8px;
`

const Header: React.FC = () => {
  const location = useLocation()
  const token = localStorage.getItem('token')
  const user = JSON.parse(localStorage.getItem('user') || '{}')

  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: <Link to="/">首页</Link>,
    },
    {
      key: '/features',
      icon: <VideoCameraOutlined />,
      label: <Link to="/features">功能特色</Link>,
    },
    {
      key: '/pricing',
      icon: <DollarOutlined />,
      label: <Link to="/pricing">价格方案</Link>,
    },
    {
      key: '/download',
      icon: <DownloadOutlined />,
      label: <Link to="/download">下载应用</Link>,
    },
  ]

  const userMenuItems = [
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: <Link to="/dashboard">工作台</Link>,
    },
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: () => {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.href = '/'
      },
    },
  ]

  return (
    <StyledHeader>
      <div style={{ display: 'flex', alignItems: 'center', height: '100%' }}>
        <Logo to="/">
          <VideoCameraOutlined />
          视频草稿
        </Logo>
        
        <Menu
          mode="horizontal"
          selectedKeys={[location.pathname]}
          items={menuItems}
          style={{ flex: 1, marginLeft: 50, border: 'none' }}
        />

        <Space size="middle">
          {token ? (
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Button type="text" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Avatar size="small" icon={<UserOutlined />} />
                {user.username || '用户'}
              </Button>
            </Dropdown>
          ) : (
            <>
              <Button type="default" icon={<LoginOutlined />}>
                <Link to="/login">登录</Link>
              </Button>
              <Button type="primary" icon={<UserAddOutlined />}>
                <Link to="/register">注册</Link>
              </Button>
            </>
          )}
        </Space>
      </div>
    </StyledHeader>
  )
}

export default Header