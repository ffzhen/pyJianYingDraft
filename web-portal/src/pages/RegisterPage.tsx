import React, { useState } from 'react'
import { Form, Input, Button, Card, Typography, message } from 'antd'
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons'
import { Link, useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import { motion } from 'framer-motion'
import { useMutation } from 'react-query'
import { authService, RegisterRequest } from '@/services/auth'

const { Title, Paragraph } = Typography

const RegisterContainer = styled.div`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
`

const RegisterCard = styled(motion(Card))`
  width: 100%;
  max-width: 400px;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
`

const LoginPage: React.FC = () => {
  const navigate = useNavigate()
  const [form] = Form.useForm()

  const registerMutation = useMutation(authService.register, {
    onSuccess: (data) => {
      localStorage.setItem('token', data.token)
      localStorage.setItem('user', JSON.stringify(data.user))
      message.success('注册成功！')
      navigate('/dashboard')
    },
    onError: (error: any) => {
      message.error(error.response?.data?.error || '注册失败')
    }
  })

  const onFinish = (values: RegisterRequest) => {
    registerMutation.mutate(values)
  }

  return (
    <RegisterContainer>
      <RegisterCard
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <Title level={2} style={{ color: '#667eea' }}>
            创建账户
          </Title>
          <Paragraph type="secondary">
            填写以下信息以创建您的账户
          </Paragraph>
        </div>

        <Form
          form={form}
          name="register"
          onFinish={onFinish}
          layout="vertical"
          size="large"
        >
          <Form.Item
            name="username"
            label="用户名"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, max: 30, message: '用户名长度为3-30个字符' }
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="请输入用户名"
            />
          </Form.Item>

          <Form.Item
            name="email"
            label="邮箱"
            rules={[
              { required: true, message: '请输入邮箱地址' },
              { type: 'email', message: '请输入有效的邮箱地址' }
            ]}
          >
            <Input
              prefix={<MailOutlined />}
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

          <Form.Item
            name="confirmPassword"
            label="确认密码"
            dependencies={['password']}
            rules={[
              { required: true, message: '请确认密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'))
                },
              }),
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="请确认密码"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={registerMutation.isLoading}
              style={{ width: '100%', height: '45px' }}
            >
              {registerMutation.isLoading ? '注册中...' : '注册'}
            </Button>
          </Form.Item>

          <div style={{ textAlign: 'center' }}>
            <span style={{ color: '#666' }}>已有账户？</span>
            <Link to="/login" style={{ marginLeft: '8px', color: '#667eea' }}>
              立即登录
            </Link>
          </div>
        </Form>
      </RegisterCard>
    </RegisterContainer>
  )
}

export default LoginPage