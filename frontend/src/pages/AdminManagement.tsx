import React from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowLeftOutlined,
  AuditOutlined,
  BookOutlined,
  CameraOutlined,
  CheckCircleOutlined,
  DatabaseOutlined,
  FileSearchOutlined,
  SafetyCertificateOutlined,
  SettingOutlined,
  TeamOutlined,
} from '@ant-design/icons'
import {
  Alert,
  Button,
  Card,
  Progress,
  Statistic,
  Table,
  Tag,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  AUTHORITY_SOURCES,
  HERBS,
  HERB_IMAGE_COUNT,
  KNOWLEDGE_ARTICLES,
  PRESCRIPTIONS,
  PRESCRIPTION_CATEGORIES,
  SCIENCE_RESOURCES,
} from '../data/scienceContent'

interface OperationRecord {
  key: string
  updatedAt: string
  content: string
  topic: string
  type: string
  status: '已发布' | '待复核' | '已更新'
}

const USAGE_TREND = [
  { day: '周一', value: 58 },
  { day: '周二', value: 72 },
  { day: '周三', value: 64 },
  { day: '周四', value: 86 },
  { day: '周五', value: 78 },
  { day: '周六', value: 94 },
  { day: '周日', value: 88 },
]

const HEALTH_ITEMS = [
  { label: '组成完整率', value: 100, note: '方剂条目均记录全部组成药味' },
  { label: '方源标注率', value: 100, note: '方剂条目均标注项目资料中的古籍方源' },
  { label: '图片覆盖率', value: 44, note: `118 味中药中有 ${HERB_IMAGE_COUNT} 味配有本地图鉴图片` },
  { label: '安全提示覆盖率', value: 100, note: '方药条目均包含剂量、禁忌或专业指导边界' },
]

const OPERATION_RECORDS: OperationRecord[] = [
  {
    key: '1',
    updatedAt: '2026-11-15',
    content: '完成四君子汤方剂档案与关联中药复核',
    topic: '补益剂',
    type: '方剂复核',
    status: '已发布',
  },
  {
    key: '2',
    updatedAt: '2026-11-12',
    content: '补充桂枝汤与麻黄汤组成对照说明',
    topic: '解表剂',
    type: '内容更新',
    status: '已更新',
  },
  {
    key: '3',
    updatedAt: '2026-11-08',
    content: `核对 ${HERB_IMAGE_COUNT} 张中药图鉴图片与药名对应关系`,
    topic: '中药图鉴',
    type: '来源核验',
    status: '已发布',
  },
  {
    key: '4',
    updatedAt: '2026-11-05',
    content: '更新十五类方剂与知识图谱学习关联',
    topic: '方剂通识',
    type: '结构优化',
    status: '已发布',
  },
  {
    key: '5',
    updatedAt: '2026-11-02',
    content: '复核中医药机构、药典与标准资料入口',
    topic: '权威来源',
    type: '资源更新',
    status: '待复核',
  },
]

const columns: ColumnsType<OperationRecord> = [
  {
    title: '更新时间',
    dataIndex: 'updatedAt',
    width: 120,
  },
  {
    title: '运营内容',
    dataIndex: 'content',
    render: (value: string) => <strong>{value}</strong>,
  },
  {
    title: '类别/资料域',
    dataIndex: 'topic',
    width: 140,
    render: (value: string) => <Tag>{value}</Tag>,
  },
  {
    title: '类型',
    dataIndex: 'type',
    width: 120,
  },
  {
    title: '状态',
    dataIndex: 'status',
    width: 110,
    render: (value: OperationRecord['status']) => (
      <Tag color={value === '已发布' ? 'success' : value === '待复核' ? 'warning' : 'cyan'}>
        {value}
      </Tag>
    ),
  },
]

const AdminManagement: React.FC = () => {
  const navigate = useNavigate()

  const sourceCategories = Array.from(
    AUTHORITY_SOURCES.reduce((map, source) => {
      map.set(source.category, (map.get(source.category) || 0) + 1)
      return map
    }, new Map<string, number>()),
  )

  return (
    <div className="page-shell admin-page">
      <div className="page-heading page-heading-row">
        <div>
          <Button
            className="page-back-button"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/')}
          >
            返回首页
          </Button>
          <div className="page-eyebrow">
            <SettingOutlined />
            PLATFORM OPERATIONS
          </div>
          <h1 className="page-title">方剂科普运营看板</h1>
          <p className="page-description">
            从方药覆盖、学习工具、来源结构和内容健康检查四个角度观察平台，
            为下一轮方剂通识教育与公众服务优化提供依据。
          </p>
        </div>
        <Tag color="cyan">资料观察指标</Tag>
      </div>

      <Alert
        className="admin-demo-alert"
        type="info"
        showIcon
        message="看板展示平台内置资料指标"
        description="本页不读取真实访问日志，也不包含用户管理或审计功能。指标用于说明方剂、中药、图片和来源的资料整理状态。"
      />

      <div className="admin-metric-grid">
        <Card>
          <Statistic
            title="经典方剂"
            value={PRESCRIPTIONS.length}
            suffix="首"
            prefix={<BookOutlined />}
          />
          <span className="admin-metric-note">覆盖 {PRESCRIPTION_CATEGORIES.length} 个方剂类别</span>
        </Card>
        <Card>
          <Statistic
            title="中药图鉴"
            value={HERBS.length}
            suffix="味"
            prefix={<DatabaseOutlined />}
          />
          <span className="admin-metric-note">{HERB_IMAGE_COUNT} 张本地图片，缺图显示文字占位</span>
        </Card>
        <Card>
          <Statistic
            title="本地中药图片"
            value={HERB_IMAGE_COUNT}
            suffix="张"
            prefix={<CameraOutlined />}
          />
          <span className="admin-metric-note">用于学习辨识，不用于真伪或品质判断</span>
        </Card>
        <Card>
          <Statistic
            title="权威来源"
            value={AUTHORITY_SOURCES.length}
            suffix="家"
            prefix={<FileSearchOutlined />}
          />
          <span className="admin-metric-note">已整理 {KNOWLEDGE_ARTICLES.length} 个方药条目与 {SCIENCE_RESOURCES.length} 项学习资源</span>
        </Card>
      </div>

      <div className="admin-main-grid">
        <Card
          title={
            <span className="card-title-with-icon">
              <AuditOutlined /> 近七日方药学习热度
            </span>
          }
          extra={<Tag>相对指数</Tag>}
          className="admin-trend-card"
        >
          <div className="admin-trend-chart" aria-label="近七日方药学习趋势示意">
            {USAGE_TREND.map((item) => (
              <div className="admin-trend-column" key={item.day}>
                <span>{item.value}</span>
                <div>
                  <i style={{ height: `${item.value}%` }} />
                </div>
                <small>{item.day}</small>
              </div>
            ))}
          </div>
          <p className="chart-footnote">
            柱形为资料整理后的相对示意值，用于比较一周内的学习主题活跃度，不代表真实访问量。
          </p>
        </Card>

        <Card
          title={
            <span className="card-title-with-icon">
              <TeamOutlined /> 权威来源结构
            </span>
          }
        >
          <div className="admin-source-list">
            {sourceCategories.map(([category, count]) => (
              <div key={category}>
                <div>
                  <span>{category}</span>
                  <strong>{count} 家</strong>
                </div>
                <Progress
                  percent={Math.round((count / AUTHORITY_SOURCES.length) * 100)}
                  showInfo={false}
                  strokeColor="#0B6E69"
                  size="small"
                />
              </div>
            ))}
          </div>
          <Button
            block
            icon={<FileSearchOutlined />}
            onClick={() => navigate('/evidence')}
          >
            查看权威来源
          </Button>
        </Card>

        <Card
          title={
            <span className="card-title-with-icon">
              <SafetyCertificateOutlined /> 内容健康度
            </span>
          }
          extra={<Tag color="success">整体稳定</Tag>}
        >
          <div className="admin-health-list">
            {HEALTH_ITEMS.map((item) => (
              <div key={item.label}>
                <div>
                  <strong>{item.label}</strong>
                  <span>{item.value}%</span>
                </div>
                <Progress
                  percent={item.value}
                  showInfo={false}
                  strokeColor={item.value >= 90 ? '#3C8A62' : '#B48725'}
                  size="small"
                />
                <p>{item.note}</p>
              </div>
            ))}
          </div>
        </Card>

        <Card
          title={
            <span className="card-title-with-icon">
              <CheckCircleOutlined /> 下一轮优化重点
            </span>
          }
        >
          <div className="admin-focus-list">
            <div>
              <span>01</span>
              <div>
                <strong>补充进阶方剂的配伍解释</strong>
                <p>优先检查药味较多方剂中的组方层次与传统配伍表述。</p>
              </div>
            </div>
            <div>
              <span>02</span>
              <div>
                <strong>扩展中药图片覆盖</strong>
                <p>逐步补齐暂无本地图片的中药图鉴资料。</p>
              </div>
            </div>
            <div>
              <span>03</span>
              <div>
                <strong>建立版本与来源核对记录</strong>
                <p>区分古籍版本、药典标准、教材表述与公众科普改写。</p>
              </div>
            </div>
            <div>
              <span>04</span>
              <div>
                <strong>强化专业审校与安全边界</strong>
                <p>重点检查毒性药、炮制、妊娠禁忌与特殊人群提示。</p>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <Card
        className="admin-records-card"
        title={
          <span className="card-title-with-icon">
            <DatabaseOutlined /> 近期内容运营记录
          </span>
        }
        extra={<Tag color="cyan">{OPERATION_RECORDS.length} 条内容记录</Tag>}
      >
        <Table
          rowKey="key"
          columns={columns}
          dataSource={OPERATION_RECORDS}
          pagination={false}
          scroll={{ x: 760 }}
        />
      </Card>
    </div>
  )
}

export default AdminManagement
