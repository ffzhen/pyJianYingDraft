import React from 'react'
import { Layout, Typography, Card, Row, Col, Button, List, Tag, CheckCircleOutlined } from 'antd'
import { Link } from 'react-router-dom'
import {
  CrownOutlined,
  UserOutlined,
  TeamOutlined,
  EnterpriseOutlined
} from '@ant-design/icons'
import styled from 'styled-components'
import { motion } from 'framer-motion'

const { Content } = Layout
const { Title, Paragraph } = Typography

const PricingContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 60px 20px;
`

const SectionTitle = styled(Title)`
  text-align: center;
  margin-bottom: 20px !important;
  color: white;
`

const SectionSubtitle = styled(Paragraph)`
  text-align: center;
  font-size: 18px;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 60px !important;
`

const PricingCard = styled(motion(Card))`
  height: 100%;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
  position: relative;
  
  &:hover {
    transform: translateY(-5px);
  }
  
  &.popular {
    border: 2px solid #667eea;
    transform: scale(1.05);
    
    .popular-badge {
      position: absolute;
      top: -12px;
      left: 50%;
      transform: translateX(-50%);
      background: #667eea;
      color: white;
      padding: 4px 16px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: bold;
    }
  }
`

const Price = styled.div`
  font-size: 3rem;
  font-weight: bold;
  color: #667eea;
  margin-bottom: 8px;
`

const PricePeriod = styled.span`
  font-size: 1rem;
  color: #666;
`

const FeatureList = styled(List)`
  .ant-list-item {
    border: none !important;
    padding: 8px 0 !important;
  }
`

const PricingPage: React.FC = () => {
  const pricingPlans = [
    {
      name: '免费版',
      icon: <UserOutlined style={{ fontSize: '48px', color: '#667eea' }} />,
      price: '0',
      period: '永久免费',
      description: '适合个人用户和轻度使用',
      features: [
        '最高 1080p 视频编辑',
        '基础特效和转场',
        '5GB 云端存储',
        '社区技术支持',
        '基础导出格式',
        '移动端查看'
      ],
      limitations: [
        '不支持 4K 分辨率',
        '无团队协作功能',
        '有限的高级特效'
      ],
      popular: false,
      buttonText: '开始使用',
      buttonType: 'default' as const
    },
    {
      name: '专业版',
      icon: <CrownOutlined style={{ fontSize: '48px', color: '#667eea' }} />,
      price: '99',
      period: '每月',
      description: '适合专业用户和小团队',
      features: [
        '最高 4K 视频编辑',
        '全部特效和转场',
        '100GB 云端存储',
        '优先技术支持',
        '多种导出格式',
        '高级编辑工具',
        '团队协作功能',
        '版本历史记录'
      ],
      limitations: [],
      popular: true,
      buttonText: '立即升级',
      buttonType: 'primary' as const
    },
    {
      name: '企业版',
      icon: <EnterpriseOutlined style={{ fontSize: '48px', color: '#667eea' }} />,
      price: '定制',
      period: '联系销售',
      description: '适合大型团队和企业',
      features: [
        '无限分辨率支持',
        '企业级安全',
        '无限云端存储',
        '专属客户经理',
        '定制化功能',
        'API 接口支持',
        'SLA 服务保障',
        '培训服务',
        '数据迁移服务'
      ],
      limitations: [],
      popular: false,
      buttonText: '联系销售',
      buttonType: 'default' as const
    }
  ]

  const comparisonFeatures = [
    { name: '视频分辨率', free: '1080p', pro: '4K', enterprise: '无限制' },
    { name: '存储空间', free: '5GB', pro: '100GB', enterprise: '无限制' },
    { name: '团队协作', free: '❌', pro: '✅', enterprise: '✅' },
    { name: '高级特效', free: '基础', pro: '全部', enterprise: '全部+定制' },
    { name: '技术支持', free: '社区', pro: '优先', enterprise: '专属' },
    { name: 'API 接口', free: '❌', pro: '❌', enterprise: '✅' }
  ]

  return (
    <Content style={{ background: 'transparent' }}>
      <PricingContainer>
        <SectionTitle level={1}>选择适合您的方案</SectionTitle>
        <SectionSubtitle>
          从个人创作到企业级应用，我们为您提供最适合的解决方案
        </SectionSubtitle>

        <Row gutter={[32, 32]} style={{ marginBottom: '80px' }}>
          {pricingPlans.map((plan, index) => (
            <Col xs={24} md={8} key={index}>
              <PricingCard
                className={plan.popular ? 'popular' : ''}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
              >
                {plan.popular && <div className="popular-badge">最受欢迎</div>}
                
                <div style={{ textAlign: 'center', marginBottom: '32px' }}>
                  {plan.icon}
                  <Title level={2} style={{ marginTop: '16px' }}>{plan.name}</Title>
                  <Paragraph>{plan.description}</Paragraph>
                  
                  <div style={{ margin: '24px 0' }}>
                    <Price>
                      {plan.price}
                      <PricePeriod>/{plan.period}</PricePeriod>
                    </Price>
                  </div>
                </div>

                <div style={{ marginBottom: '32px' }}>
                  <Title level={4}>功能特性</Title>
                  <FeatureList
                    dataSource={plan.features}
                    renderItem={(feature) => (
                      <List.Item>
                        <CheckCircleOutlined style={{ color: '#52c41a', marginRight: '8px' }} />
                        {feature}
                      </List.Item>
                    )}
                  />
                </div>

                {plan.limitations.length > 0 && (
                  <div style={{ marginBottom: '32px' }}>
                    <Title level={4}>限制</Title>
                    <FeatureList
                      dataSource={plan.limitations}
                      renderItem={(limitation) => (
                        <List.Item>
                          <span style={{ color: '#ff4d4f' }}>• {limitation}</span>
                        </List.Item>
                      )}
                    />
                  </div>
                )}

                <Button
                  type={plan.buttonType}
                  size="large"
                  style={{ width: '100%' }}
                >
                  {plan.buttonText}
                </Button>
              </PricingCard>
            </Col>
          ))}
        </Row>

        <div style={{ background: 'rgba(255, 255, 255, 0.1)', borderRadius: '12px', padding: '40px' }}>
          <Title level={2} style={{ color: 'white', textAlign: 'center', marginBottom: '40px' }}>
            功能对比
          </Title>
          <Row gutter={[16, 16]}>
            <Col xs={24} md={6}>
              <Card title="功能" style={{ background: 'rgba(255,255,255,0.1)', border: 'none' }}>
                <List
                  dataSource={comparisonFeatures}
                  renderItem={(item) => (
                    <List.Item>
                      <Tag color="blue">{item.name}</Tag>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
            <Col xs={24} md={6}>
              <Card title="免费版" style={{ background: 'rgba(255,255,255,0.1)', border: 'none' }}>
                <List
                  dataSource={comparisonFeatures}
                  renderItem={(item) => (
                    <List.Item>
                      <span style={{ color: 'white' }}>{item.free}</span>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
            <Col xs={24} md={6}>
              <Card title="专业版" style={{ background: 'rgba(255,255,255,0.1)', border: 'none' }}>
                <List
                  dataSource={comparisonFeatures}
                  renderItem={(item) => (
                    <List.Item>
                      <span style={{ color: '#52c41a' }}>{item.pro}</span>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
            <Col xs={24} md={6}>
              <Card title="企业版" style={{ background: 'rgba(255,255,255,0.1)', border: 'none' }}>
                <List
                  dataSource={comparisonFeatures}
                  renderItem={(item) => (
                    <List.Item>
                      <span style={{ color: '#52c41a' }}>{item.enterprise}</span>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          </Row>
        </div>
      </PricingContainer>
    </Content>
  )
}

export default PricingPage