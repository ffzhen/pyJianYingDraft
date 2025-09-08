import React from 'react'
import { Layout, Typography, Card, Button, Space, Row, Col } from 'antd'
import { Link } from 'react-router-dom'
import {
  VideoCameraOutlined,
  UserOutlined,
  ThunderboltOutlined,
  CloudOutlined,
  TeamOutlined,
  SafetyOutlined
} from '@ant-design/icons'
import { motion } from 'framer-motion'
import styled from 'styled-components'

const { Content } = Layout
const { Title, Paragraph } = Typography

const WelcomeContainer = styled.div`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
`

const WelcomeCard = styled(motion.div)`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 60px;
  max-width: 1000px;
  width: 100%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
`

const Logo = styled.div`
  text-align: center;
  margin-bottom: 40px;
`

const LogoIcon = styled.div`
  font-size: 80px;
  color: #667eea;
  margin-bottom: 16px;
`

const FeatureGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
  margin: 40px 0;
`

const FeatureCard = styled.div`
  text-align: center;
  padding: 24px;
  border-radius: 12px;
  background: rgba(102, 126, 234, 0.1);
  transition: transform 0.3s ease;
  
  &:hover {
    transform: translateY(-5px);
  }
`

const ActionButtons = styled.div`
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 40px;
`

const WelcomePage: React.FC = () => {
  const features = [
    {
      icon: <VideoCameraOutlined style={{ fontSize: '48px', color: '#667eea' }} />,
      title: '专业编辑',
      description: '多轨道编辑，实时预览'
    },
    {
      icon: <ThunderboltOutlined style={{ fontSize: '48px', color: '#667eea' }} />,
      title: '极速渲染',
      description: 'GPU加速，快速导出'
    },
    {
      icon: <CloudOutlined style={{ fontSize: '48px', color: '#667eea' }} />,
      title: '云端同步',
      description: '项目文件云端存储'
    },
    {
      icon: <TeamOutlined style={{ fontSize: '48px', color: '#667eea' }} />,
      title: '团队协作',
      description: '多人协作编辑'
    },
    {
      icon: <SafetyOutlined style={{ fontSize: '48px', color: '#667eea' }} />,
      title: '安全可靠',
      description: '数据加密，安全存储'
    },
    {
      icon: <UserOutlined style={{ fontSize: '48px', color: '#667eea' }} />,
      title: '简单易用',
      description: '直观界面，快速上手'
    }
  ]

  return (
    <WelcomeContainer>
      <WelcomeCard
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
      >
        <Logo>
          <LogoIcon>
            <VideoCameraOutlined />
          </LogoIcon>
          <Title level={1} style={{ color: '#667eea', margin: 0 }}>
            视频草稿
          </Title>
          <Paragraph style={{ fontSize: '18px', color: '#666', margin: '8px 0 0 0' }}>
            专业视频编辑工具
          </Paragraph>
        </Logo>

        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <Title level={2} style={{ color: '#333', marginBottom: '16px' }}>
            欢迎使用视频草稿桌面版
          </Title>
          <Paragraph style={{ fontSize: '16px', color: '#666', lineHeight: '1.6' }}>
            视频草稿是一款专业的视频编辑工具，支持多平台使用，提供完整的视频编辑功能。
            <br />
            无论是个人创作还是团队协作，都能满足您的需求。
          </Paragraph>
        </div>

        <FeatureGrid>
          {features.map((feature, index) => (
            <FeatureCard
              key={index}
              as={motion.div}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <div style={{ marginBottom: '16px' }}>
                {feature.icon}
              </div>
              <Title level={4} style={{ color: '#333', margin: '0 0 8px 0' }}>
                {feature.title}
              </Title>
              <Paragraph style={{ color: '#666', margin: 0 }}>
                {feature.description}
              </Paragraph>
            </FeatureCard>
          ))}
        </FeatureGrid>

        <ActionButtons>
          <Link to="/login">
            <Button type="primary" size="large" style={{ height: '50px', fontSize: '16px', minWidth: '120px' }}>
              登录账户
            </Button>
          </Link>
          <Link to="/register">
            <Button size="large" style={{ height: '50px', fontSize: '16px', minWidth: '120px' }}>
              注册账户
            </Button>
          </Link>
        </ActionButtons>

        <div style={{ textAlign: 'center', marginTop: '40px' }}>
          <Paragraph style={{ color: '#999', fontSize: '14px' }}>
            还没有账户？立即注册享受更多功能
          </Paragraph>
        </div>
      </WelcomeCard>
    </WelcomeContainer>
  )
}

export default WelcomePage