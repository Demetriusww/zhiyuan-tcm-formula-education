import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  QuestionCircleOutlined,
  FileTextOutlined,
  UserOutlined,
  LoginOutlined,
  CloseOutlined,
  DownOutlined,
  StarOutlined,
  LogoutOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons'
import { App as AntdApp, Avatar, Button, Dropdown, Form, Input, Modal, Tabs } from 'antd'
import { useAuth } from '../../context/AuthContext'
import { authUI } from '../../api/authClient'

const PrototypeHeader: React.FC = () => {
  const navigate = useNavigate()
  const { message } = AntdApp.useApp()
  const { user, login, register, logout } = useAuth()
  const [isLoginModalVisible, setIsLoginModalVisible] = useState(false)
  const [authLoading, setAuthLoading] = useState(false)
  const [loginForm] = Form.useForm()
  const [registerForm] = Form.useForm()

  useEffect(() => {
    authUI.setOpenLogin(() => setIsLoginModalVisible(true))
  }, [])

  const handleLogin = async (values: any) => {
    setAuthLoading(true)
    try {
      await login(values.username, values.password)
      message.success('登录成功')
      setIsLoginModalVisible(false)
      loginForm.resetFields()
    } catch (e: any) {
      message.error(e.message || '登录失败')
    } finally {
      setAuthLoading(false)
    }
  }

  const handleRegister = async (values: any) => {
    setAuthLoading(true)
    try {
      await register({
        username: values.username,
        password: values.password,
        email: values.email,
        nickname: values.username,
      })
      message.success('注册成功，已自动登录')
      setIsLoginModalVisible(false)
      registerForm.resetFields()
    } catch (e: any) {
      message.error(e.message || '注册失败')
    } finally {
      setAuthLoading(false)
    }
  }

  const userMenu = {
    items: [
      ...(user?.role === 'admin'
        ? [{ key: 'admin', icon: <SafetyCertificateOutlined />, label: '科普运营' }]
        : []),
      { key: 'fav', icon: <StarOutlined />, label: '我的收藏' },
      { type: 'divider' as const },
      { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', danger: true },
    ],
    onClick: ({ key }: { key: string }) => {
      if (key === 'admin') navigate('/admin')
      else if (key === 'fav') navigate('/database?fav=1')
      else if (key === 'logout') {
        logout()
        message.success('已退出登录')
      }
    },
  }

  return (
    <header className="prototype-header">
      <div className="brand-lockup" onClick={() => navigate('/')} role="button" tabIndex={0}>
        <div className="brand-mark" aria-hidden="true">
          <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
            <circle cx="16" cy="16" r="4" fill="#F0B43C" />
            <circle cx="16" cy="5" r="2.5" fill="#E96B4C" />
            <circle cx="6" cy="22" r="2.2" fill="#FFFFFF" />
            <circle cx="26" cy="22" r="2.2" fill="#FFFFFF" />
            <g stroke="#FFFFFF" strokeWidth="1.5" opacity="0.9">
              <path d="M16 12V7.5M12.7 18.1 8 20.7M19.3 18.1l4.7 2.6M13.5 5.8 7.5 19.4M18.5 5.8l6 13.6" />
            </g>
          </svg>
        </div>
        <div>
          <div className="brand-title">知源 · 中医方剂通识平台</div>
          <div className="brand-tagline">读懂一味药，理解一首方</div>
        </div>
      </div>

      <div className="header-learning-motto" aria-hidden="true">
        <span className="header-motto-rule" />
        <span className="header-motto-seal">方</span>
        <div className="header-motto-copy">
          <strong>识药 · 读方 · 明配伍</strong>
          <small>君臣佐使 · 方证相应</small>
        </div>
        <span className="header-motto-rule" />
      </div>

      <div className="header-actions">
        <button className="header-text-action" onClick={() => navigate('/help')}>
          <QuestionCircleOutlined />
          <span className="header-action-label">帮助中心</span>
        </button>
        <button className="header-text-action" onClick={() => navigate('/guide')}>
          <FileTextOutlined />
          <span className="header-action-label">使用指南</span>
        </button>

        {user ? (
          <Dropdown menu={userMenu} placement="bottomRight">
            <div className="user-chip">
              <Avatar size={28} style={{ background: '#0B6E69' }} icon={<UserOutlined />} />
              <span>{user.nickname || user.username}</span>
              <DownOutlined style={{ color: '#6B7E85', fontSize: 10 }} />
            </div>
          </Dropdown>
        ) : (
          <Button
            type="primary"
            icon={<LoginOutlined />}
            onClick={() => setIsLoginModalVisible(true)}
            className="login-button"
          >
            登录 / 注册
          </Button>
        )}
      </div>

      <Modal
        title={null}
        open={isLoginModalVisible}
        onCancel={() => setIsLoginModalVisible(false)}
        footer={null}
        width={420}
        centered
        closeIcon={<CloseOutlined style={{ color: '#6B7E85' }} />}
      >
        <div style={{ textAlign: 'center', marginBottom: 20 }}>
          <div
            style={{
              width: 58,
              height: 58,
              background: '#0B6E69',
              borderRadius: 8,
              display: 'grid',
              placeItems: 'center',
              margin: '0 auto 14px',
            }}
          >
            <svg width="34" height="34" viewBox="0 0 32 32" fill="none" aria-hidden="true">
              <circle cx="16" cy="16" r="4" fill="#F0B43C" />
              <circle cx="16" cy="5" r="2.5" fill="#E96B4C" />
              <circle cx="6" cy="22" r="2.2" fill="#FFFFFF" />
              <circle cx="26" cy="22" r="2.2" fill="#FFFFFF" />
              <g stroke="#FFFFFF" strokeWidth="1.5">
                <path d="M16 12V7.5M12.7 18.1 8 20.7M19.3 18.1l4.7 2.6M13.5 5.8 7.5 19.4M18.5 5.8l6 13.6" />
              </g>
            </svg>
          </div>
          <h2 style={{ fontSize: 20, fontWeight: 700, color: '#18303A', margin: 0 }}>
            欢迎来到知源
          </h2>
          <p style={{ color: '#6B7E85', margin: '7px 0 0' }}>
            收藏方剂与中药条目，保存你的中医药学习记录
          </p>
        </div>

        <Tabs
          defaultActiveKey="login"
          centered
          items={[
            {
              key: 'login',
              label: '登录',
              children: (
                <Form form={loginForm} onFinish={handleLogin} layout="vertical">
                  <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
                    <Input
                      prefix={<UserOutlined style={{ color: '#6B7E85' }} />}
                      placeholder="用户名"
                      size="large"
                    />
                  </Form.Item>
                  <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
                    <Input.Password placeholder="密码" size="large" />
                  </Form.Item>
                  <Button
                    type="primary"
                    htmlType="submit"
                    size="large"
                    block
                    loading={authLoading}
                    style={{ height: 44 }}
                  >
                    登录
                  </Button>
                  <div className="login-demo-note">
                    本地体验入口：用户名 <strong>admin</strong>，密码任意填写
                  </div>
                </Form>
              ),
            },
            {
              key: 'register',
              label: '注册',
              children: (
                <Form form={registerForm} onFinish={handleRegister} layout="vertical">
                  <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
                    <Input
                      prefix={<UserOutlined style={{ color: '#6B7E85' }} />}
                      placeholder="用户名"
                      size="large"
                    />
                  </Form.Item>
                  <Form.Item
                    name="email"
                    rules={[
                      { required: true, message: '请输入邮箱' },
                      { type: 'email', message: '请输入有效的邮箱地址' },
                    ]}
                  >
                    <Input prefix={<span style={{ color: '#6B7E85' }}>@</span>} placeholder="邮箱" size="large" />
                  </Form.Item>
                  <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
                    <Input.Password placeholder="密码" size="large" />
                  </Form.Item>
                  <Form.Item
                    name="confirmPassword"
                    dependencies={['password']}
                    rules={[
                      { required: true, message: '请确认密码' },
                      ({ getFieldValue }) => ({
                        validator(_, value) {
                          if (!value || getFieldValue('password') === value) return Promise.resolve()
                          return Promise.reject(new Error('两次输入的密码不一致'))
                        },
                      }),
                    ]}
                  >
                    <Input.Password placeholder="确认密码" size="large" />
                  </Form.Item>
                  <Button
                    type="primary"
                    htmlType="submit"
                    size="large"
                    block
                    loading={authLoading}
                    style={{ height: 44 }}
                  >
                    注册
                  </Button>
                </Form>
              ),
            },
          ]}
        />
      </Modal>
    </header>
  )
}

export default PrototypeHeader
