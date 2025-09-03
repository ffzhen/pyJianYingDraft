import React from 'react'
import { Layout, Typography, Row, Col, Space, Divider } from 'antd'
import { Link } from 'react-router-dom'
import {
  VideoCameraOutlined,
  MailOutlined,
  PhoneOutlined,
  LocationOutlined,
  GithubOutlined,
  TwitterOutlined,
  WechatOutlined
} from '@ant-design/icons'
import styled from 'styled-components'

const { Footer: AntFooter } = Layout
const { Title, Paragraph } = Typography

const StyledFooter = styled(AntFooter)`
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 60px 0 20px;
  margin-top: auto;
`

const FooterContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
`

const FooterSection = styled.div`
  margin-bottom: 40px;
`

const FooterTitle = styled(Title)`
  color: white !important;
  font-size: 18px !important;
  margin-bottom: 20px !important;
`

const FooterLink = styled(Link)`
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  display: block;
  padding: 4px 0;
  transition: color 0.3s ease;
  
  &:hover {
    color: #667eea;
  }
`

const SocialIcon = styled.a`
  color: rgba(255, 255, 255, 0.8);
  font-size: 24px;
  margin-right: 16px;
  transition: color 0.3s ease;
  
  &:hover {
    color: #667eea;
  }
`

const FooterBottom = styled.div`
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-top: 20px;
  text-align: center;
  color: rgba(255, 255, 255, 0.6);
`

const Footer: React.FC = () => {
  return (
    <StyledFooter>
      <FooterContainer>
        <Row gutter={[32, 32]}>
          <Col xs={24} sm={12} lg={6}>
            <FooterSection>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '16px' }}>
                <VideoCameraOutlined style={{ fontSize: '32px', color: '#667eea', marginRight: '12px' }} />
                <FooterTitle level={3}>视频草稿</FooterTitle>
              </div>
              <Paragraph style={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                专业的视频编辑工具，让创作变得简单。支持多平台协作，云端存储，为您提供最佳的视频编辑体验。
              </Paragraph>
              <Space size="large">
                <SocialIcon href="#" aria-label="GitHub">
                  <GithubOutlined />
                </SocialIcon>
                <SocialIcon href="#" aria-label="Twitter">
                  <TwitterOutlined />
                </SocialIcon>
                <SocialIcon href="#" aria-label="WeChat">
                  <WechatOutlined />
                </SocialIcon>
              </Space>
            </FooterSection>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <FooterSection>
              <FooterTitle level={4}>产品</FooterTitle>
              <FooterLink to="/features">功能特色</FooterLink>
              <FooterLink to="/pricing">价格方案</FooterLink>
              <FooterLink to="/download">下载应用</FooterLink>
              <FooterLink to="/updates">更新日志</FooterLink>
              <FooterLink to="/roadmap">开发路线</FooterLink>
            </FooterSection>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <FooterSection>
              <FooterTitle level={4}>支持</FooterTitle>
              <FooterLink to="/help">帮助中心</FooterLink>
              <FooterLink to="/tutorials">视频教程</FooterLink>
              <FooterLink to="/community">社区论坛</FooterLink>
              <FooterLink to="/contact">联系我们</FooterLink>
              <FooterLink to="/feedback">意见反馈</FooterLink>
            </FooterSection>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <FooterSection>
              <FooterTitle level={4}>公司</FooterTitle>
              <FooterLink to="/about">关于我们</FooterLink>
              <FooterLink to="/careers">加入我们</FooterLink>
              <FooterLink to="/privacy">隐私政策</FooterLink>
              <FooterLink to="/terms">服务条款</FooterLink>
              <FooterLink to="/press">媒体资源</FooterLink>
            </FooterSection>
          </Col>
        </Row>

        <Row gutter={[32, 32]} style={{ marginTop: '40px' }}>
          <Col xs={24} md={12}>
            <FooterSection>
              <FooterTitle level={4}>联系信息</FooterTitle>
              <div style={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                <p><MailOutlined /> contact@videodraft.com</p>
                <p><PhoneOutlined /> +86 400-123-4567</p>
                <p><LocationOutlined /> 北京市朝阳区xxx大厦</p>
              </div>
            </FooterSection>
          </Col>

          <Col xs={24} md={12}>
            <FooterSection>
              <FooterTitle level={4}>订阅更新</FooterTitle>
              <Paragraph style={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                订阅我们的邮件列表，获取最新的产品更新和优惠信息。
              </Paragraph>
              <div style={{ display: 'flex', gap: '8px' }}>
                <input
                  type="email"
                  placeholder="输入您的邮箱"
                  style={{
                    flex: 1,
                    padding: '8px 12px',
                    border: '1px solid rgba(255, 255, 255, 0.3)',
                    borderRadius: '4px',
                    background: 'rgba(255, 255, 255, 0.1)',
                    color: 'white'
                  }}
                />
                <button
                  style={{
                    padding: '8px 16px',
                    background: '#667eea',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  订阅
                </button>
              </div>
            </FooterSection>
          </Col>
        </Row>

        <FooterBottom>
          <Paragraph style={{ margin: 0 }}>
            © 2024 视频草稿. 保留所有权利. | 
            <Link to="/privacy" style={{ color: 'rgba(255, 255, 255, 0.6)', marginLeft: '8px' }}>
              隐私政策
            </Link> | 
            <Link to="/terms" style={{ color: 'rgba(255, 255, 255, 0.6)', marginLeft: '8px' }}>
              服务条款
            </Link>
          </Paragraph>
        </FooterBottom>
      </FooterContainer>
    </StyledFooter>
  )
}

export default Footer