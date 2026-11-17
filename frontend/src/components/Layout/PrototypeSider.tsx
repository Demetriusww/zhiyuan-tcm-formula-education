import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  HomeOutlined,
  ApartmentOutlined,
  ExperimentOutlined,
  SwapOutlined,
  BookOutlined,
  DatabaseOutlined,
  FileSearchOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  ThunderboltOutlined,
  RadarChartOutlined,
  ShareAltOutlined,
  CameraOutlined,
  SafetyCertificateOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { Tooltip } from 'antd'
import { useAuth } from '../../context/AuthContext'

interface MenuItem {
  key: string
  icon: React.ReactNode
  label: string
  path: string
}

interface PrototypeSiderProps {
  collapsed?: boolean
  onCollapsedChange?: (collapsed: boolean) => void
}

const PrototypeSider: React.FC<PrototypeSiderProps> = ({
  collapsed = false,
  onCollapsedChange,
}) => {
  const navigate = useNavigate()
  const location = useLocation()
  const { user } = useAuth()

  const mainMenuItems: MenuItem[] = [
    { key: 'home', icon: <HomeOutlined />, label: '首页', path: '/' },
    { key: 'smart', icon: <ThunderboltOutlined />, label: '方剂学习任务', path: '/smart' },
    { key: 'analysis', icon: <ApartmentOutlined />, label: '方剂 AI 问答', path: '/analysis' },
    { key: 'efficacy', icon: <ExperimentOutlined />, label: '方剂拆解实验室', path: '/efficacy' },
    { key: 'optimization', icon: <SafetyCertificateOutlined />, label: '方剂科普创作工坊', path: '/optimization' },
    { key: 'similarity', icon: <RadarChartOutlined />, label: '方剂关联推荐', path: '/similarity' },
    { key: 'visualization', icon: <ShareAltOutlined />, label: '方剂知识图谱', path: '/visualization' },
    { key: 'recognize', icon: <CameraOutlined />, label: '中药图鉴辨识', path: '/recognize' },
    { key: 'comparison', icon: <SwapOutlined />, label: '方剂科普内容评估', path: '/comparison' },
    { key: 'knowledge', icon: <BookOutlined />, label: '方剂与中药知识库', path: '/herbs' },
    { key: 'database', icon: <DatabaseOutlined />, label: '方剂学习资源库', path: '/database' },
    { key: 'literature', icon: <FileSearchOutlined />, label: '中医药权威来源', path: '/evidence' },
    ...(user?.role === 'admin'
      ? [{ key: 'admin', icon: <SettingOutlined />, label: '科普运营', path: '/admin' }]
      : []),
  ]

  const activeKey =
    mainMenuItems.find((item) => item.path === location.pathname)?.key || 'home'

  const handleMenuClick = (item: MenuItem) => navigate(item.path)

  return (
    <aside
      className="prototype-sider"
      style={{
        width: collapsed ? 64 : 200,
        top: 68,
        height: 'calc(100vh - 68px)',
      }}
    >
      <div className="sider-orbit" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>

      <nav className="sider-menu-list" aria-label="主导航">
        {mainMenuItems.map((item) => (
          <Tooltip key={item.key} title={collapsed ? item.label : undefined} placement="right">
            <button
              type="button"
              onClick={() => handleMenuClick(item)}
              className={`sider-menu-item ${activeKey === item.key ? 'is-active' : ''}`}
              style={{ justifyContent: collapsed ? 'center' : 'flex-start' }}
            >
              <span className="sider-menu-icon">{item.icon}</span>
              {!collapsed && <span className="sider-menu-label">{item.label}</span>}
            </button>
          </Tooltip>
        ))}
      </nav>

      <button
        type="button"
        className="sider-collapse-button"
        onClick={() => onCollapsedChange?.(!collapsed)}
        aria-label={collapsed ? '展开导航' : '收起导航'}
      >
        {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
        {!collapsed && <span>收起导航</span>}
      </button>
    </aside>
  )
}

export default PrototypeSider
