import React from 'react'
import { Layout, Typography, Card, Row, Col, Button, List, Tag, Divider } from 'antd'
import {
  WindowsOutlined,
  AppleOutlined,
  LinuxOutlined,
  DownloadOutlined,
  SafetyOutlined,
  ThunderboltOutlined,
  CloudDownloadOutlined
} from '@ant-design/icons'
import styled from 'styled-components'
import { motion } from 'framer-motion'

const { Content } = Layout
const { Title, Paragraph } = Typography

const DownloadContainer = styled.div`
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

const DownloadCard = styled(motion(Card))`
  height: 100%;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
  
  &:hover {
    transform: translateY(-5px);
  }
`

const PlatformIcon = styled.div`
  font-size: 64px;
  color: #667eea;
  margin-bottom: 20px;
  text-align: center;
`

const SystemRequirements = styled.div`
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 40px;
  margin-top: 60px;
`

const DownloadPage: React.FC = () => {
  const platforms = [
    {
      name: 'Windows',
      icon: <WindowsOutlined />,
      version: 'v2.0.0',
      size: '156 MB',
      releaseDate: '2024-01-15',
      requirements: [
        'Windows 10 或更高版本',
        '64 位处理器',
        '4GB RAM (推荐 8GB)',
        '2GB 可用磁盘空间',
        'DirectX 11 或更高版本'
      ],
      downloadUrl: '/downloads/video-draft-windows-x64.exe',
      buttonText: '下载 Windows 版'
    },
    {
      name: 'macOS',
      icon: <AppleOutlined />,
      version: 'v2.0.0',
      size: '142 MB',
      releaseDate: '2024-01-15',
      requirements: [
        'macOS 10.14 或更高版本',
        '64 位处理器',
        '4GB RAM (推荐 8GB)',
        '2GB 可用磁盘空间',
        '支持 Metal 的 Mac'
      ],
      downloadUrl: '/downloads/video-draft-macos-x64.dmg',
      buttonText: '下载 macOS 版'
    },
    {
      name: 'Linux',
      icon: <LinuxOutlined />,
      version: 'v2.0.0',
      size: '138 MB',
      releaseDate: '2024-01-15',
      requirements: [
        'Ubuntu 18.04 或更高版本',
        '64 位处理器',
        '4GB RAM (推荐 8GB)',
        '2GB 可用磁盘空间',
        'GTK 3.0 或更高版本'
      ],
      downloadUrl: '/downloads/video-draft-linux-x64.AppImage',
      buttonText: '下载 Linux 版'
    }
  ]

  const features = [
    {
      icon: <ThunderboltOutlined style={{ fontSize: '32px', color: '#667eea' }} />,
      title: '快速安装',
      description: '一键安装，自动更新，无需复杂配置'
    },
    {
      icon: <SafetyOutlined style={{ fontSize: '32px', color: '#667eea' }} />,
      title: '安全可靠',
      description: '数字签名认证，无恶意软件，定期安全更新'
    },
    {
      icon: <CloudDownloadOutlined style={{ fontSize: '32px', color: '#667eea' }} />,
      title: '云端同步',
      description: '自动同步项目文件，多设备无缝协作'
    }
  ]

  const handleDownload = (url: string) => {
    // 这里可以实现实际的下载逻辑
    console.log('下载文件:', url)
    // window.open(url, '_blank')
  }

  return (
    <Content style={{ background: 'transparent' }}>
      <DownloadContainer>
        <SectionTitle level={1}>下载视频草稿</SectionTitle>
        <SectionSubtitle>
          选择您的操作系统，开始您的视频创作之旅
        </SectionSubtitle>

        <Row gutter={[32, 32]} style={{ marginBottom: '80px' }}>
          {platforms.map((platform, index) => (
            <Col xs={24} md={8} key={index}>
              <DownloadCard
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
              >
                <div style={{ textAlign: 'center', marginBottom: '32px' }}>
                  <PlatformIcon>{platform.icon}</PlatformIcon>
                  <Title level={2}>{platform.name}</Title>
                  <Tag color="blue">{platform.version}</Tag>
                  <Paragraph type="secondary">
                    {platform.size} • {platform.releaseDate}
                  </Paragraph>
                </div>

                <div style={{ marginBottom: '32px' }}>
                  <Title level={4}>系统要求</Title>
                  <List
                    dataSource={platform.requirements}
                    renderItem={(req) => (
                      <List.Item>
                        <span style={{ fontSize: '14px' }}>• {req}</span>
                      </List.Item>
                    )}
                  />
                </div>

                <Button
                  type="primary"
                  size="large"
                  icon={<DownloadOutlined />}
                  style={{ width: '100%' }}
                  onClick={() => handleDownload(platform.downloadUrl)}
                >
                  {platform.buttonText}
                </Button>
              </DownloadCard>
            </Col>
          ))}
        </Row>

        <div style={{ marginBottom: '80px' }}>
          <Title level={2} style={{ color: 'white', textAlign: 'center', marginBottom: '40px' }}>
            为什么选择视频草稿？
          </Title>
          <Row gutter={[32, 32]}>
            {features.map((feature, index) => (
              <Col xs={24} md={8} key={index}>
                <Card
                  style={{ 
                    background: 'rgba(255, 255, 255, 0.1)', 
                    border: 'none',
                    textAlign: 'center',
                    height: '100%'
                  }}
                >
                  <div style={{ marginBottom: '20px' }}>
                    {feature.icon}
                  </div>
                  <Title level={3}>{feature.title}</Title>
                  <Paragraph>{feature.description}</Paragraph>
                </Card>
              </Col>
            ))}
          </Row>
        </div>

        <SystemRequirements>
          <Title level={2} style={{ color: 'white', textAlign: 'center', marginBottom: '40px' }}>
            最低系统要求
          </Title>
          <Row gutter={[32, 32]}>
            <Col xs={24} md={8}>
              <Card title="处理器" style={{ background: 'rgba(255,255,255,0.1)', border: 'none' }}>
                <List
                  dataSource={[
                    '64 位处理器',
                    '2 GHz 或更快',
                    '多核处理器推荐'
                  ]}
                  renderItem={(item) => (
                    <List.Item>
                      <span style={{ color: 'white' }}>{item}</span>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
            <Col xs={24} md={8}>
              <Card title="内存" style={{ background: 'rgba(255,255,255,0.1)', border: 'none' }}>
                <List
                  dataSource={[
                    '最低 4GB RAM',
                    '推荐 8GB RAM',
                    '16GB RAM 用于 4K 编辑'
                  ]}
                  renderItem={(item) => (
                    <List.Item>
                      <span style={{ color: 'white' }}>{item}</span>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
            <Col xs={24} md={8}>
              <Card title="存储" style={{ background: 'rgba(255,255,255,0.1)', border: 'none' }}>
                <List
                  dataSource={[
                    '2GB 可用空间',
                    'SSD 推荐用于最佳性能',
                    '额外空间用于项目文件'
                  ]}
                  renderItem={(item) => (
                    <List.Item>
                      <span style={{ color: 'white' }}>{item}</span>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          </Row>
        </SystemRequirements>
      </DownloadContainer>
    </Content>
  )
}

export default DownloadPage