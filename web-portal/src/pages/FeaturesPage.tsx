import React from 'react'
import { Layout, Typography, Card, Row, Col, List, Tag } from 'antd'
import {
  VideoCameraOutlined,
  ThunderboltOutlined,
  TeamOutlined,
  CloudOutlined,
  MobileOutlined,
  SafetyOutlined,
  ApiOutlined,
  PictureOutlined
} from '@ant-design/icons'
import styled from 'styled-components'
import { motion } from 'framer-motion'

const { Content } = Layout
const { Title, Paragraph } = Typography

const FeaturesContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 60px 20px;
`

const SectionTitle = styled(Title)`
  text-align: center;
  margin-bottom: 60px !important;
  color: white;
`

const FeatureCard = styled(motion(Card))`
  height: 100%;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
  
  &:hover {
    transform: translateY(-5px);
  }
`

const IconWrapper = styled.div`
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
`

const ComparisonTable = styled.div`
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 40px;
  margin-top: 60px;
`

const FeaturesPage: React.FC = () => {
  const coreFeatures = [
    {
      icon: <VideoCameraOutlined style={{ fontSize: '32px', color: 'white' }} />,
      title: '多轨道编辑',
      description: '支持视频、音频、图片等多轨道编辑，精确控制时间轴'
    },
    {
      icon: <ThunderboltOutlined style={{ fontSize: '32px', color: 'white' }} />,
      title: '实时预览',
      description: '实时预览编辑效果，所见即所得的编辑体验'
    },
    {
      icon: <PictureOutlined style={{ fontSize: '32px', color: 'white' }} />,
      title: '丰富特效',
      description: '内置丰富的转场特效、滤镜和动画效果'
    },
    {
      icon: <ApiOutlined style={{ fontSize: '32px', color: 'white' }} />,
      title: '插件扩展',
      description: '支持第三方插件，扩展更多功能'
    }
  ]

  const advancedFeatures = [
    {
      icon: <TeamOutlined style={{ fontSize: '32px', color: 'white' }} />,
      title: '团队协作',
      description: '多人实时协作编辑，支持评论和版本控制'
    },
    {
      icon: <CloudOutlined style={{ fontSize: '32px', color: 'white' }} />,
      title: '云端同步',
      description: '项目文件云端存储，多设备无缝切换'
    },
    {
      icon: <MobileOutlined style={{ fontSize: '32px', color: 'white' }} />,
      title: '移动端支持',
      description: '支持移动端查看和简单编辑'
    },
    {
      icon: <SafetyOutlined style={{ fontSize: '32px', color: 'white' }} />,
      title: '安全可靠',
      description: '企业级安全保障，数据加密传输和存储'
    }
  ]

  const comparisonData = [
    {
      feature: '视频分辨率',
      free: '最高 1080p',
      premium: '最高 4K'
    },
    {
      feature: '导出格式',
      free: 'MP4',
      premium: 'MP4, MOV, AVI, MKV'
    },
    {
      feature: '存储空间',
      free: '5GB',
      premium: '100GB'
    },
    {
      feature: '团队协作',
      free: '不支持',
      premium: '支持'
    },
    {
      feature: '高级特效',
      free: '基础特效',
      premium: '全部特效'
    },
    {
      feature: '技术支持',
      free: '社区支持',
      premium: '专属客服'
    }
  ]

  return (
    <Content style={{ background: 'transparent' }}>
      <FeaturesContainer>
        <SectionTitle level={1}>功能特色</SectionTitle>
        
        <Title level={2} style={{ color: 'white', textAlign: 'center', marginBottom: '40px' }}>
          核心功能
        </Title>
        
        <Row gutter={[32, 32]} style={{ marginBottom: '80px' }}>
          {coreFeatures.map((feature, index) => (
            <Col xs={24} sm={12} lg={6} key={index}>
              <FeatureCard
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
              >
                <IconWrapper>
                  {feature.icon}
                </IconWrapper>
                <Title level={3}>{feature.title}</Title>
                <Paragraph>{feature.description}</Paragraph>
              </FeatureCard>
            </Col>
          ))}
        </Row>

        <Title level={2} style={{ color: 'white', textAlign: 'center', marginBottom: '40px' }}>
          高级功能
        </Title>
        
        <Row gutter={[32, 32]} style={{ marginBottom: '80px' }}>
          {advancedFeatures.map((feature, index) => (
            <Col xs={24} sm={12} lg={6} key={index}>
              <FeatureCard
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
              >
                <IconWrapper>
                  {feature.icon}
                </IconWrapper>
                <Title level={3}>{feature.title}</Title>
                <Paragraph>{feature.description}</Paragraph>
              </FeatureCard>
            </Col>
          ))}
        </Row>

        <ComparisonTable>
          <Title level={2} style={{ color: 'white', textAlign: 'center', marginBottom: '40px' }}>
            功能对比
          </Title>
          <Row gutter={[32, 32]}>
            <Col xs={24} md={8}>
              <Card title="功能" style={{ background: 'rgba(255,255,255,0.1)', border: 'none' }}>
                <List
                  dataSource={comparisonData}
                  renderItem={(item) => (
                    <List.Item>
                      <Tag color="blue">{item.feature}</Tag>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
            <Col xs={24} md={8}>
              <Card title="免费版" style={{ background: 'rgba(255,255,255,0.1)', border: 'none' }}>
                <List
                  dataSource={comparisonData}
                  renderItem={(item) => (
                    <List.Item>
                      <span style={{ color: 'white' }}>{item.free}</span>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
            <Col xs={24} md={8}>
              <Card title="专业版" style={{ background: 'rgba(255,255,255,0.1)', border: 'none' }}>
                <List
                  dataSource={comparisonData}
                  renderItem={(item) => (
                    <List.Item>
                      <span style={{ color: '#52c41a' }}>{item.premium}</span>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          </Row>
        </ComparisonTable>
      </FeaturesContainer>
    </Content>
  )
}

export default FeaturesPage