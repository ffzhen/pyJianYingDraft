import React from 'react'
import { Layout, Typography, Card, Row, Col, Button, Statistic, List, Tag } from 'antd'
import { Link } from 'react-router-dom'
import {
  VideoCameraOutlined,
  CloudUploadOutlined,
  TeamOutlined,
  TrophyOutlined,
  ClockCircleOutlined,
  FireOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CopyOutlined,
  DownloadOutlined
} from '@ant-design/icons'
import styled from 'styled-components'
import { motion } from 'framer-motion'

const { Content } = Layout
const { Title, Paragraph } = Typography

const DashboardContainer = styled.div`
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px 20px;
`

const WelcomeSection = styled.div`
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 40px;
  margin-bottom: 40px;
  text-align: center;
`

const StatsCard = styled(motion(Card))`
  text-align: center;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
  
  &:hover {
    transform: translateY(-5px);
  }
`

const ProjectCard = styled(motion(Card))`
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
  margin-bottom: 16px;
  
  &:hover {
    transform: translateY(-2px);
  }
`

const DashboardPage: React.FC = () => {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  
  const stats = [
    {
      title: '总项目数',
      value: 12,
      icon: <VideoCameraOutlined style={{ color: '#667eea' }} />,
      color: '#667eea'
    },
    {
      title: '已完成',
      value: 8,
      icon: <TrophyOutlined style={{ color: '#52c41a' }} />,
      color: '#52c41a'
    },
    {
      title: '进行中',
      value: 3,
      icon: <ClockCircleOutlined style={{ color: '#faad14' }} />,
      color: '#faad14'
    },
    {
      title: '总观看次数',
      value: 1543,
      icon: <FireOutlined style={{ color: '#f5222d' }} />,
      color: '#f5222d'
    }
  ]

  const recentProjects = [
    {
      id: '1',
      title: '产品介绍视频',
      description: '新产品功能介绍和演示',
      status: 'completed',
      duration: '2:30',
      views: 245,
      createdAt: '2024-01-10',
      thumbnail: '/images/project1.jpg'
    },
    {
      id: '2',
      title: '培训教程系列',
      description: '员工培训视频课程',
      status: 'draft',
      duration: '15:45',
      views: 0,
      createdAt: '2024-01-08',
      thumbnail: '/images/project2.jpg'
    },
    {
      id: '3',
      title: '活动回顾',
      description: '公司年度活动精彩回顾',
      status: 'rendering',
      duration: '8:20',
      views: 89,
      createdAt: '2024-01-05',
      thumbnail: '/images/project3.jpg'
    }
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success'
      case 'draft':
        return 'default'
      case 'rendering':
        return 'processing'
      default:
        return 'default'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return '已完成'
      case 'draft':
        return '草稿'
      case 'rendering':
        return '渲染中'
      default:
        return '未知'
    }
  }

  return (
    <Content style={{ background: 'transparent' }}>
      <DashboardContainer>
        <WelcomeSection>
          <Title level={1} style={{ color: 'white', marginBottom: '16px' }}>
            欢迎回来，{user.username || '用户'}！
          </Title>
          <Paragraph style={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: '18px' }}>
            继续您的视频创作之旅，让每一个故事都精彩
          </Paragraph>
          <Button type="primary" size="large" icon={<PlusOutlined />} style={{ marginTop: '20px' }}>
            创建新项目
          </Button>
        </WelcomeSection>

        <Row gutter={[24, 24]} style={{ marginBottom: '40px' }}>
          {stats.map((stat, index) => (
            <Col xs={24} sm={12} lg={6} key={index}>
              <StatsCard
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
              >
                <div style={{ fontSize: '32px', marginBottom: '16px' }}>
                  {stat.icon}
                </div>
                <Statistic
                  title={stat.title}
                  value={stat.value}
                  valueStyle={{ color: stat.color, fontSize: '24px' }}
                />
              </StatsCard>
            </Col>
          ))}
        </Row>

        <Row gutter={[24, 24]}>
          <Col xs={24} lg={16}>
            <Card title="最近项目" style={{ background: 'rgba(255, 255, 255, 0.1)', border: 'none' }}>
              <List
                dataSource={recentProjects}
                renderItem={(project) => (
                  <ProjectCard
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.4 }}
                  >
                    <Row gutter={[16, 16]} align="middle">
                      <Col xs={24} sm={4}>
                        <div
                          style={{
                            width: '80px',
                            height: '60px',
                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            borderRadius: '8px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                          }}
                        >
                          <VideoCameraOutlined style={{ fontSize: '24px', color: 'white' }} />
                        </div>
                      </Col>
                      <Col xs={24} sm={12}>
                        <Title level={4} style={{ margin: 0, color: 'white' }}>
                          {project.title}
                        </Title>
                        <Paragraph type="secondary" style={{ margin: '4px 0' }}>
                          {project.description}
                        </Paragraph>
                        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                          <Tag color={getStatusColor(project.status)}>
                            {getStatusText(project.status)}
                          </Tag>
                          <span style={{ color: 'rgba(255, 255, 255, 0.6)' }}>
                            {project.duration}
                          </span>
                          <span style={{ color: 'rgba(255, 255, 255, 0.6)' }}>
                            • {project.views} 次观看
                          </span>
                        </div>
                      </Col>
                      <Col xs={24} sm={8}>
                        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                          <Button icon={<EditOutlined />} size="small">
                            编辑
                          </Button>
                          <Button icon={<CopyOutlined />} size="small">
                            复制
                          </Button>
                          <Button icon={<DeleteOutlined />} size="small" danger>
                            删除
                          </Button>
                        </div>
                      </Col>
                    </Row>
                  </ProjectCard>
                )}
              />
              <div style={{ textAlign: 'center', marginTop: '20px' }}>
                <Button type="link" style={{ color: '#667eea' }}>
                  查看所有项目
                </Button>
              </div>
            </Card>
          </Col>
          
          <Col xs={24} lg={8}>
            <Card title="快速操作" style={{ background: 'rgba(255, 255, 255, 0.1)', border: 'none', marginBottom: '24px' }}>
              <List
                dataSource={[
                  { icon: <PlusOutlined />, text: '创建新项目', action: '/create' },
                  { icon: <CloudUploadOutlined />, text: '导入媒体文件', action: '/import' },
                  { icon: <TeamOutlined />, text: '团队协作', action: '/team' },
                  { icon: <DownloadOutlined />, text: '下载桌面版', action: '/download' }
                ]}
                renderItem={(item) => (
                  <List.Item
                    style={{ cursor: 'pointer', border: 'none' }}
                    onClick={() => console.log('Navigate to:', item.action)}
                  >
                    <List.Item.Meta
                      avatar={item.icon}
                      title={item.text}
                    />
                  </List.Item>
                )}
              />
            </Card>

            <Card title="存储空间" style={{ background: 'rgba(255, 255, 255, 0.1)', border: 'none' }}>
              <div style={{ textAlign: 'center' }}>
                <Statistic
                  title="已使用"
                  value={2.3}
                  suffix="/ 5 GB"
                  valueStyle={{ color: '#667eea' }}
                />
                <div style={{ marginTop: '16px' }}>
                  <Button type="primary" size="small">
                    升级存储
                  </Button>
                </div>
              </div>
            </Card>
          </Col>
        </Row>
      </DashboardContainer>
    </Content>
  )
}

export default DashboardPage