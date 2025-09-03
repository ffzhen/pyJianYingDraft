import React from 'react'
import { Form, Input, Button, Card, Typography, message } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { Link, useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import { motion } from 'framer-motion'
import { useAuth } from '../hooks/useAuth'

const { Title, Paragraph } = Typography

const LoginContainer = styled.div`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
`

const LoginCard = styled(motion(Card))`
  width: 100%;
  max-width: 400px;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
`

const LoginPage: React.FC = () => {
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const { loginMutation } = useAuth()

  const onFinish = (values: { email: string; password: string }) => {
    loginMutation.mutate(values, {
      onSuccess: () => {
        navigate('/dashboard')
      }
    })
  }

  return (
    <LoginContainer>
      <LoginCard
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <Title level={2} style={{ color: '#667eea' }}>
            欢迎回来
          </Title>
          <Paragraph type="secondary">
            登录您的账户以继续
          </Paragraph>
        </div>

        <Form
          form={form}
          name="login"
          onFinish={onFinish}
          layout="vertical"
          size="large"
        >
          <Form.Item
            name="email"
            label="邮箱"
            rules={[
              { required: true, message: '请输入邮箱地址' },
              { type: 'email', message: '请输入有效的邮箱地址' }
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="请输入邮箱地址"
            />
          </Form.Item>

          <Form.Item
            name="password"
            label="密码"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6个字符' }
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="请输入密码"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loginMutation.isLoading}
              style={{ width: '100%', height: '45px' }}
            >
              {loginMutation.isLoading ? '登录中...' : '登录'}
            </Button>
          </Form.Item>

          <div style={{ textAlign: 'center' }}>
            <span style={{ color: '#666' }}>还没有账户？</span>
            <Link to="/register" style={{ marginLeft: '8px', color: '#667eea' }}>
              立即注册
            </Link>
          </div>
        </Form>
      </LoginCard>
    </LoginContainer>
  )
}

export default LoginPage