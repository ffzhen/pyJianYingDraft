import React from 'react'
import { Layout, Typography, Card, Button, Space, Form, Input, Switch, Select, Row, Col, message, Divider } from 'antd'
import { useAppContext } from '../contexts/AppContext'
import styled from 'styled-components'

const { Content } = Layout
const { Title, Paragraph, Text } = Typography

const SettingsContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
`

const SettingsCard = styled(Card)`
  margin-bottom: 24px;
`

const SettingsPage: React.FC = () => {
  const { isDarkMode, settings, updateSettings, showNotification } = useAppContext()
  const [form] = Form.useForm()

  useEffect(() => {
    if (settings) {
      form.setFieldsValue(settings)
    }
  }, [settings, form])

  const handleSave = async (values: any) => {
    try {
      // 保存设置到本地存储和后端
      Object.keys(values).forEach(key => {
        updateSettings(key, values[key])
      })
      message.success('设置保存成功')
    } catch (error) {
      message.error('设置保存失败')
    }
  }

  const handleReset = () => {
    form.resetFields()
    message.info('设置已重置')
  }

  return (
    <Content style={{ background: 'transparent' }}>
      <SettingsContainer>
        <Title level={2} style={{ color: isDarkMode ? '#fff' : '#000', marginBottom: '24px' }}>
          设置
        </Title>

        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
          initialValues={settings}
        >
          <SettingsCard title="常规设置">
            <Row gutter={24}>
              <Col xs={24} sm={12} md={8}>
                <Form.Item
                  label="语言"
                  name={['general', 'language']}
                >
                  <Select>
                    <Select.Option value="zh-CN">简体中文</Select.Option>
                    <Select.Option value="zh-TW">繁体中文</Select.Option>
                    <Select.Option value="en-US">English</Select.Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Form.Item
                  label="主题"
                  name={['general', 'theme']}
                >
                  <Select>
                    <Select.Option value="system">跟随系统</Select.Option>
                    <Select.Option value="light">浅色</Select.Option>
                    <Select.Option value="dark">深色</Select.Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Form.Item
                  label="自动更新"
                  name={['general', 'autoUpdate']}
                  valuePropName="checked"
                >
                  <Switch />
                </Form.Item>
              </Col>
            </Row>
          </SettingsCard>

          <SettingsCard title="编辑器设置">
            <Row gutter={24}>
              <Col xs={24} sm={12} md={8}>
                <Form.Item
                  label="自动保存"
                  name={['editor', 'autoSave']}
                  valuePropName="checked"
                >
                  <Switch />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Form.Item
                  label="自动保存间隔（分钟）"
                  name={['editor', 'autoSaveInterval']}
                >
                  <Input type="number" min={1} max={60} />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Form.Item
                  label="备份启用"
                  name={['editor', 'backupEnabled']}
                  valuePropName="checked"
                >
                  <Switch />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Form.Item
                  label="备份文件数量"
                  name={['editor', 'backupCount']}
                >
                  <Input type="number" min={1} max={20} />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Form.Item
                  label="默认导出格式"
                  name={['editor', 'defaultExportFormat']}
                >
                  <Select>
                    <Select.Option value="mp4">MP4</Select.Option>
                    <Select.Option value="mov">MOV</Select.Option>
                    <Select.Option value="avi">AVI</Select.Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Form.Item
                  label="默认导出质量"
                  name={['editor', 'defaultExportQuality']}
                >
                  <Select>
                    <Select.Option value="low">低</Select.Option>
                    <Select.Option value="medium">中</Select.Option>
                    <Select.Option value="high">高</Select.Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>
          </SettingsCard>

          <SettingsCard title="性能设置">
            <Row gutter={24}>
              <Col xs={24} sm={12} md={8}>
                <Form.Item
                  label="硬件加速"
                  name={['performance', 'hardwareAcceleration']}
                  valuePropName="checked"
                >
                  <Switch />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Form.Item
                  label="最大内存使用（MB）"
                  name={['performance', 'maxMemoryUsage']}
                >
                  <Input type="number" min={512} max={8192} step={256} />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Form.Item
                  label="缓存大小（MB）"
                  name={['performance', 'cacheSize']}
                >
                  <Input type="number" min={256} max={4096} step={128} />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Form.Item
                  label="GPU 加速"
                  name={['performance', 'gpuAcceleration']}
                  valuePropName="checked"
                >
                  <Switch />
                </Form.Item>
              </Col>
            </Row>
          </SettingsCard>

          <SettingsCard title="网络设置">
            <Row gutter={24}>
              <Col xs={24} sm={12} md={8}>
                <Form.Item
                  label="API 地址"
                  name={['network', 'apiUrl']}
                >
                  <Input placeholder="http://localhost:5000/api" />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Form.Item
                  label="超时时间（秒）"
                  name={['network', 'timeout']}
                >
                  <Input type="number" min={10} max={120} />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Form.Item
                  label="重试次数"
                  name={['network', 'retryAttempts']}
                >
                  <Input type="number" min={0} max={10} />
                </Form.Item>
              </Col>
            </Row>
          </SettingsCard>

          <SettingsCard title="项目设置">
            <Row gutter={24}>
              <Col xs={24} sm={12} md={8}>
                <Form.Item
                  label="默认项目路径"
                  name={['projects', 'defaultProjectPath']}
                >
                  <Input placeholder="项目保存路径" />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Form.Item
                  label="自动恢复"
                  name={['projects', 'autoRecover']}
                  valuePropName="checked"
                >
                  <Switch />
                </Form.Item>
              </Col>
            </Row>
          </SettingsCard>

          <div style={{ textAlign: 'center' }}>
            <Space size="large">
              <Button type="primary" htmlType="submit" size="large">
                保存设置
              </Button>
              <Button onClick={handleReset} size="large">
                重置
              </Button>
            </Space>
          </div>
        </Form>
      </SettingsContainer>
    </Content>
  )
}

export default SettingsPage