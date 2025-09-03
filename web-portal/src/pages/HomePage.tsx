import React from 'react'
import { Layout, Typography, Button, Space, Card, Row, Col } from 'antd'
import { Link } from 'react-router-dom'
import {
  VideoCameraOutlined,
  ThunderboltOutlined,
  TeamOutlined,
  CloudOutlined
} from '@ant-design/icons'
import styled from 'styled-components'
import { motion } from 'framer-motion'

const { Content } = Layout
const { Title, Paragraph } = Typography

const HeroSection = styled.div`
  text-align: center;
  padding: 100px 0;
  color: white;
`

const HeroTitle = styled(motion.h1)`
  font-size: 4rem;
  font-weight: bold;
  margin-bottom: 20px;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
`

const HeroSubtitle = styled(motion.p)`
  font-size: 1.5rem;
  margin-bottom: 40px;
  opacity: 0.9;
`

const FeatureCard = styled(motion(Card))`
  text-align: center;
  height: 100%;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
  
  &:hover {
    transform: translateY(-5px);
  }
`

const CTASection = styled.div`
  text-align: center;
  padding: 80px 0;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  margin: 60px 0;
`

const HomePage: React.FC = () => {
  const features = [
    {
      icon: <VideoCameraOutlined style={{ fontSize: '48px', color: '#667eea' }} />,
      title: '专业视频编辑',
      description: '强大的视频编辑功能，支持多轨道编辑、特效处理和格式转换'
    },
    {
      icon: <ThunderboltOutlined style={{ fontSize: '48px', color: '#667eea' }} />,
      title: '极速渲染',
      description: '采用最新的渲染技术，大幅提升视频处理速度'
    },
    {
      icon: <TeamOutlined style={{ fontSize: '48px', color: '#667eea' }} />,
      title: '团队协作',
      description: '支持多人协作编辑，实时同步项目进度'
    },
    {
      icon: <CloudOutlined style={{ fontSize: '48px', color: '#667eea' }} />,
      title: '云端存储',
      description: '项目文件云端存储，随时随地访问您的创作内容'
    }
  ]

  return (
    <Content style={{ background: 'transparent' }}>
      <HeroSection>
        <HeroTitle
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          视频草稿
        </HeroTitle>
        <HeroSubtitle
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          专业的视频编辑工具，让创作变得简单
        </HeroSubtitle>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
        >
          <Space size="large">
            <Button type="primary" size="large" style={{ height: '50px', fontSize: '18px' }}>
              <Link to="/download">免费下载</Link>
            </Button>
            <Button size="large" style={{ height: '50px', fontSize: '18px', color: 'white', borderColor: 'white' }}>
              <Link to="/features">了解更多</Link>
            </Button>
          </Space>
        </motion.div>
      </HeroSection>

      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 20px' }}>
        <Row gutter={[32, 32]} style={{ marginBottom: '80px' }}>
          {features.map((feature, index) => (
            <Col xs={24} sm={12} lg={6} key={index}>
              <FeatureCard
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
              >
                <div style={{ marginBottom: '20px' }}>
                  {feature.icon}
                </div>
                <Title level={3}>{feature.title}</Title>
                <Paragraph>{feature.description}</Paragraph>
              </FeatureCard>
            </Col>
          ))}
        </Row>

        <CTASection>
          <Title level={2} style={{ color: 'white', marginBottom: '20px' }}>
            开始您的视频创作之旅
          </Title>
          <Paragraph style={{ color: 'white', fontSize: '18px', marginBottom: '40px' }}>
            立即下载视频草稿，体验专业级的视频编辑功能
          </Paragraph>
          <Button type="primary" size="large" style={{ height: '50px', fontSize: '18px' }}>
            <Link to="/download">立即下载</Link>
          </Button>
        </CTASection>
      </div>
    </Content>
  )
}

export default HomePage