import React, { useState } from 'react'
import { Layout, Typography, Card, Button, Space, Tag, Progress, Statistic, Row, Col, message } from 'antd'
import { 
  VideoCameraOutlined, 
  ClockCircleOutlined, 
  EyeOutlined, 
  LikeOutlined,
  EditOutlined,
  PlayCircleOutlined,
  DeleteOutlined,
  CopyOutlined,
  ExportOutlined
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAppContext } from '../contexts/AppContext'
import styled from 'styled-components'
import { motion } from 'framer-motion'

const { Content } = Layout
const { Title, Paragraph, Text } = Typography

const ProjectContainer = styled.div`
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
`

const ProjectCard = styled(motion.div)`
  background: ${props => props.isDarkMode ? '#1f1f1f' : '#fff'};
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  }
`

const ProjectHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
`

const ProjectThumbnail = styled.div`
  width: 120px;
  height: 80px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  flex-shrink: 0;
`

const ProjectInfo = styled.div`
  flex: 1;
`

const ProjectActions = styled.div`
  display: flex;
  gap: 8px;
`

const StatusTag = styled(Tag)`
  margin-left: 8px;
`

const TimelinePreview = styled.div`
  background: ${props => props.isDarkMode ? '#2d2d2d' : '#f5f5f5'};
  border-radius: 4px;
  height: 40px;
  margin: 12px 0;
  position: relative;
  overflow: hidden;
`

const TimelineTrack = styled.div`
  position: absolute;
  height: 4px;
  background: #667eea;
  top: 50%;
  transform: translateY(-50%);
  border-radius: 2px;
`

const ProjectPage: React.FC = () => {
  const navigate = useNavigate()
  const { isDarkMode, showNotification } = useAppContext()
  const [loading, setLoading] = useState(false)

  // 模拟项目数据
  const projects = [
    {
      id: '1',
      title: '产品介绍视频',
      description: '新产品功能介绍和演示视频',
      status: 'completed',
      duration: '2:30',
      progress: 100,
      views: 1245,
      likes: 89,
      createdAt: '2024-01-10',
      lastModified: '2024-01-15',
      scenes: [
        { id: '1', title: '开场', duration: 30, color: '#ff6b6b' },
        { id: '2', title: '功能展示', duration: 60, color: '#4ecdc4' },
        { id: '3', title: '总结', duration: 60, color: '#45b7d1' }
      ]
    },
    {
      id: '2',
      title: '培训教程系列',
      description: '员工培训视频课程制作',
      status: 'draft',
      duration: '15:45',
      progress: 65,
      views: 0,
      likes: 0,
      createdAt: '2024-01-08',
      lastModified: '2024-01-12',
      scenes: [
        { id: '1', title: '第一章', duration: 180, color: '#ff6b6b' },
        { id: '2', title: '第二章', duration: 240, color: '#4ecdc4' },
        { id: '3', title: '第三章', duration: 180, color: '#45b7d1' },
        { id: '4', title: '第四章', duration: 225, color: '#f9ca24' }
      ]
    },
    {
      id: '3',
      title: '活动回顾',
      description: '公司年度活动精彩回顾',
      status: 'rendering',
      duration: '8:20',
      progress: 85,
      views: 234,
      likes: 45,
      createdAt: '2024-01-05',
      lastModified: '2024-01-11',
      scenes: [
        { id: '1', title: '开场', duration: 60, color: '#ff6b6b' },
        { id: '2', title: '活动过程', duration: 300, color: '#4ecdc4' },
        { id: '3', title: '精彩瞬间', duration: 120, color: '#45b7d1' },
        { id: '4', title: '结束', duration: 40, color: '#f9ca24' }
      ]
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

  const handleProjectClick = (projectId: string) => {
    navigate(`/project/${projectId}`)
  }

  const handleEdit = (e: React.MouseEvent, projectId: string) => {
    e.stopPropagation()
    showNotification('info', '编辑功能开发中')
  }

  const handleDuplicate = (e: React.MouseEvent, projectId: string) => {
    e.stopPropagation()
    showNotification('success', '项目复制成功')
  }

  const handleExport = (e: React.MouseEvent, projectId: string) => {
    e.stopPropagation()
    showNotification('info', '导出功能开发中')
  }

  const handleDelete = (e: React.MouseEvent, projectId: string) => {
    e.stopPropagation()
    showNotification('error', '删除功能开发中')
  }

  const stats = {
    totalProjects: projects.length,
    completedProjects: projects.filter(p => p.status === 'completed').length,
    totalViews: projects.reduce((sum, p) => sum + p.views, 0),
    totalLikes: projects.reduce((sum, p) => sum + p.likes, 0)
  }

  return (
    <Content style={{ background: 'transparent' }}>
      <ProjectContainer>
        <div style={{ marginBottom: '24px' }}>
          <Title level={2} style={{ color: isDarkMode ? '#fff' : '#000', marginBottom: '8px' }}>
            项目管理
          </Title>
          <Paragraph style={{ color: isDarkMode ? '#bfbfbf' : '#666' }}>
            管理您的所有视频项目
          </Paragraph>
        </div>

        {/* 统计卡片 */}
        <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="总项目数"
                value={stats.totalProjects}
                prefix={<VideoCameraOutlined />}
                valueStyle={{ color: '#667eea' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="已完成"
                value={stats.completedProjects}
                prefix={<PlayCircleOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="总观看次数"
                value={stats.totalViews}
                prefix={<EyeOutlined />}
                valueStyle={{ color: '#fa8c16' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="总点赞数"
                value={stats.totalLikes}
                prefix={<LikeOutlined />}
                valueStyle={{ color: '#eb2f96' }}
              />
            </Card>
          </Col>
        </Row>

        {/* 项目列表 */}
        <div>
          {projects.map((project, index) => (
            <ProjectCard
              key={project.id}
              isDarkMode={isDarkMode}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: index * 0.1 }}
              onClick={() => handleProjectClick(project.id)}
            >
              <ProjectHeader>
                <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                  <ProjectThumbnail>
                    <VideoCameraOutlined style={{ fontSize: '32px', color: 'white' }} />
                  </ProjectThumbnail>
                  <ProjectInfo>
                    <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                      <Title level={4} style={{ margin: 0, color: isDarkMode ? '#fff' : '#000' }}>
                        {project.title}
                      </Title>
                      <StatusTag color={getStatusColor(project.status)}>
                        {getStatusText(project.status)}
                      </StatusTag>
                    </div>
                    <Paragraph style={{ margin: 0, color: isDarkMode ? '#bfbfbf' : '#666' }}>
                      {project.description}
                    </Paragraph>
                    <div style={{ display: 'flex', gap: '16px', marginTop: '8px' }}>
                      <Text type="secondary">
                        <ClockCircleOutlined /> {project.duration}
                      </Text>
                      <Text type="secondary">
                        <EyeOutlined /> {project.views}
                      </Text>
                      <Text type="secondary">
                        <LikeOutlined /> {project.likes}
                      </Text>
                      <Text type="secondary">
                        创建于 {new Date(project.createdAt).toLocaleDateString()}
                      </Text>
                    </div>
                  </ProjectInfo>
                </div>
                <ProjectActions>
                  <Button
                    type="primary"
                    icon={<EditOutlined />}
                    onClick={(e) => handleEdit(e, project.id)}
                  >
                    编辑
                  </Button>
                  <Button
                    icon={<CopyOutlined />}
                    onClick={(e) => handleDuplicate(e, project.id)}
                  >
                    复制
                  </Button>
                  <Button
                    icon={<ExportOutlined />}
                    onClick={(e) => handleExport(e, project.id)}
                  >
                    导出
                  </Button>
                  <Button
                    danger
                    icon={<DeleteOutlined />}
                    onClick={(e) => handleDelete(e, project.id)}
                  >
                    删除
                  </Button>
                </ProjectActions>
              </ProjectHeader>

              {project.progress < 100 && (
                <div style={{ marginBottom: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <Text type="secondary">进度</Text>
                    <Text type="secondary">{project.progress}%</Text>
                  </div>
                  <Progress percent={project.progress} size="small" />
                </div>
              )}

              <TimelinePreview isDarkMode={isDarkMode}>
                {project.scenes.map((scene, index) => (
                  <TimelineTrack
                    key={scene.id}
                    style={{
                      left: `${(index / project.scenes.length) * 100}%`,
                      width: `${(scene.duration / 945) * 100}%`, // 945 is total duration in seconds
                      backgroundColor: scene.color
                    }}
                  />
                ))}
              </TimelinePreview>
            </ProjectCard>
          ))}
        </div>
      </ProjectContainer>
    </Content>
  )
}

export default ProjectPage