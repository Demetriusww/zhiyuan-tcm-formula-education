import { useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  ArrowRightOutlined,
  ClockCircleOutlined,
  DatabaseOutlined,
  DeleteOutlined,
  DownloadOutlined,
  EyeOutlined,
  FileTextOutlined,
  LinkOutlined,
  PlusOutlined,
  SearchOutlined,
  StarFilled,
  StarOutlined,
  TeamOutlined,
} from '@ant-design/icons'
import {
  App as AntdApp,
  Button,
  Card,
  Descriptions,
  Form,
  Input,
  Modal,
  Select,
  Switch,
  Tag,
} from 'antd'
import {
  PRESCRIPTION_CATEGORIES,
  SCIENCE_RESOURCES,
  type ScienceResource,
} from '../data/scienceContent'

const { Search, TextArea } = Input
const FAVORITES_KEY = 'zhiyuan-formula-learning-favorites'

const FORMAT_OPTIONS: ScienceResource['format'][] = [
  '互动课程',
  '图文长读',
  '互动工具',
  '学习任务',
  '图鉴卡片',
]

const DIFFICULTY_OPTIONS: ScienceResource['difficulty'][] = ['入门', '进阶']

const TOPIC_OPTIONS = [
  ...PRESCRIPTION_CATEGORIES.map((category) => category.name),
  '方剂通识',
  '中药图鉴',
]

const readFavorites = (): number[] => {
  try {
    const value = localStorage.getItem(FAVORITES_KEY)
    return value ? (JSON.parse(value) as number[]) : [1, 9]
  } catch {
    return [1, 9]
  }
}

const PrescriptionDatabase: React.FC = () => {
  const navigate = useNavigate()
  const { message } = AntdApp.useApp()
  const [searchParams] = useSearchParams()
  const [form] = Form.useForm()
  const [resources, setResources] = useState<ScienceResource[]>(SCIENCE_RESOURCES)
  const [keyword, setKeyword] = useState('')
  const [formatFilter, setFormatFilter] = useState<string>('')
  const [difficultyFilter, setDifficultyFilter] = useState<string>('')
  const [onlyFavorites, setOnlyFavorites] = useState(searchParams.get('fav') === '1')
  const [favorites, setFavorites] = useState<number[]>(readFavorites)
  const [detail, setDetail] = useState<ScienceResource | null>(null)
  const [addOpen, setAddOpen] = useState(false)

  const visibleResources = useMemo(() => {
    const query = keyword.trim().toLowerCase()
    return resources
      .filter((resource) => {
        const matchesKeyword =
          !query ||
          [
            resource.title,
            resource.topic,
            resource.summary,
            resource.source,
            resource.format,
            resource.audience,
          ]
            .join(' ')
            .toLowerCase()
            .includes(query)
        return (
          matchesKeyword &&
          (!formatFilter || resource.format === formatFilter) &&
          (!difficultyFilter || resource.difficulty === difficultyFilter) &&
          (!onlyFavorites || favorites.includes(resource.id))
        )
      })
      .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))
  }, [difficultyFilter, favorites, formatFilter, keyword, onlyFavorites, resources])

  const persistFavorites = (next: number[]) => {
    setFavorites(next)
    localStorage.setItem(FAVORITES_KEY, JSON.stringify(next))
  }

  const toggleFavorite = (resource: ScienceResource) => {
    const next = favorites.includes(resource.id)
      ? favorites.filter((id) => id !== resource.id)
      : [...favorites, resource.id]
    persistFavorites(next)
    message.success(favorites.includes(resource.id) ? '已取消收藏' : '已加入我的收藏')
  }

  const openResource = (resource: ScienceResource) => {
    if (resource.url.startsWith('/')) {
      navigate(resource.url)
      return
    }
    window.open(resource.url, '_blank', 'noopener,noreferrer')
  }

  const exportResources = () => {
    const blob = new Blob([JSON.stringify(visibleResources, null, 2)], {
      type: 'application/json;charset=utf-8',
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `zhiyuan-formula-learning-resources-${new Date().toISOString().slice(0, 10)}.json`
    link.click()
    URL.revokeObjectURL(url)
    message.success(`已导出 ${visibleResources.length} 条资源`)
  }

  const addResource = async () => {
    try {
      const values = await form.validateFields()
      const next: ScienceResource = {
        id: Date.now(),
        title: values.title.trim(),
        topic: values.topic,
        format: values.format,
        audience: values.audience.trim(),
        difficulty: values.difficulty,
        source: values.source.trim(),
        duration: values.duration.trim(),
        updatedAt: new Date().toISOString().slice(0, 10),
        summary: values.summary.trim(),
        url: values.url?.trim() || '/herbs',
      }
      setResources((current) => [next, ...current])
      setAddOpen(false)
      form.resetFields()
      message.success('方剂学习资源已加入本地学习列表')
    } catch {
      return
    }
  }

  const removeResource = (resource: ScienceResource) => {
    Modal.confirm({
      title: '移除本地资源',
      content: `确定从当前学习列表移除“${resource.title}”吗？`,
      okButtonProps: { danger: true },
      onOk: () => {
        setResources((current) => current.filter((item) => item.id !== resource.id))
      message.success('已从当前学习资源列表移除')
      },
    })
  }

  return (
    <div className="page-shell resource-library-page">
      <div className="page-heading page-heading-row">
        <div>
          <div className="page-eyebrow">
            <DatabaseOutlined />
            FORMULA LEARNING LIBRARY
          </div>
          <h1 className="page-title">方剂学习资源库</h1>
          <p className="page-description">
            汇集方剂通识课程、经典名方解读、互动拆解、学习任务和中药图鉴卡片。
            可按方剂类别、内容形式与学习阶段筛选，建立自己的中医药学习路径。
          </p>
        </div>
        <Tag color="gold">本地学习清单</Tag>
      </div>

      <Card className="resource-filter-card">
        <div className="resource-filter-grid">
          <Search
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
            placeholder="搜索方名、方剂类别、学习主题、受众或来源"
            allowClear
            enterButton={<SearchOutlined />}
          />
          <Select
            value={formatFilter || undefined}
            onChange={(value) => setFormatFilter(value || '')}
            allowClear
            placeholder="内容形式"
            options={FORMAT_OPTIONS.map((value) => ({ value, label: value }))}
          />
          <Select
            value={difficultyFilter || undefined}
            onChange={(value) => setDifficultyFilter(value || '')}
            allowClear
            placeholder="阅读难度"
            options={DIFFICULTY_OPTIONS.map((value) => ({ value, label: value }))}
          />
          <div className="resource-filter-actions">
            <Button icon={<DownloadOutlined />} onClick={exportResources}>
              导出
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setAddOpen(true)}>
              新增资源
            </Button>
          </div>
        </div>
        <div className="resource-filter-footer">
          <Switch
            checked={onlyFavorites}
            onChange={setOnlyFavorites}
            checkedChildren="只看收藏"
            unCheckedChildren="全部资源"
          />
          <span>当前显示 {visibleResources.length} 条资源 · {favorites.length} 条已收藏</span>
          <span><TeamOutlined /> 面向公众、课堂、家庭共读与中医药文化学习场景</span>
        </div>
      </Card>

      <div className="resource-list">
        {visibleResources.map((resource, index) => (
          <Card
            key={resource.id}
            className="resource-library-card"
            styles={{ body: { padding: 0 } }}
          >
            <div className={`resource-library-aside cover-${index % 4}`}>
              <span>{resource.format}</span>
              <strong>{resource.topic}</strong>
            </div>
            <div className="resource-library-main">
              <div className="resource-library-topline">
                <div>
                  <Tag color="cyan">{resource.difficulty}</Tag>
                  <span><ClockCircleOutlined /> {resource.duration}</span>
                  <span>{resource.updatedAt} 更新</span>
                </div>
                <button
                  type="button"
                  className={`resource-favorite${favorites.includes(resource.id) ? ' is-active' : ''}`}
                  onClick={() => toggleFavorite(resource)}
                  aria-label={favorites.includes(resource.id) ? '取消收藏' : '收藏资源'}
                >
                  {favorites.includes(resource.id) ? <StarFilled /> : <StarOutlined />}
                </button>
              </div>
              <h2>{resource.title}</h2>
              <p>{resource.summary}</p>
              <div className="resource-library-tags">
                <Tag>{resource.topic}</Tag>
                <Tag>{resource.audience}</Tag>
                <span>{resource.source}</span>
              </div>
              <div className="resource-library-actions">
                <Button icon={<EyeOutlined />} onClick={() => setDetail(resource)}>
                  查看详情
                </Button>
                <Button type="primary" onClick={() => openResource(resource)}>
                  开始学习 <ArrowRightOutlined />
                </Button>
                <Button
                  type="text"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => removeResource(resource)}
                  aria-label="移除资源"
                />
              </div>
            </div>
          </Card>
        ))}
      </div>

      {visibleResources.length === 0 && (
        <Card className="resource-empty">
          <FileTextOutlined />
          <h3>没有符合条件的学习资源</h3>
          <p>尝试清除筛选条件，或新增一条本方剂学习资源。</p>
        </Card>
      )}

      <Modal
        title={detail?.title}
        open={Boolean(detail)}
        onCancel={() => setDetail(null)}
        footer={
          detail ? (
            <>
              <Button onClick={() => setDetail(null)}>关闭</Button>
              <Button type="primary" onClick={() => openResource(detail)}>
                进入资源
              </Button>
            </>
          ) : null
        }
        width={720}
      >
        {detail && (
          <>
            <p className="resource-detail-summary">{detail.summary}</p>
            <Descriptions bordered column={2} size="small">
              <Descriptions.Item label="学习主题">{detail.topic}</Descriptions.Item>
              <Descriptions.Item label="内容形式">{detail.format}</Descriptions.Item>
              <Descriptions.Item label="目标受众">{detail.audience}</Descriptions.Item>
              <Descriptions.Item label="阅读难度">{detail.difficulty}</Descriptions.Item>
              <Descriptions.Item label="预计时长">{detail.duration}</Descriptions.Item>
              <Descriptions.Item label="更新时间">{detail.updatedAt}</Descriptions.Item>
              <Descriptions.Item label="来源" span={2}>{detail.source}</Descriptions.Item>
              <Descriptions.Item label="资源地址" span={2}>
                <span><LinkOutlined /> {detail.url}</span>
              </Descriptions.Item>
            </Descriptions>
          </>
        )}
      </Modal>

      <Modal
        title="新增方剂学习资源"
        open={addOpen}
        onCancel={() => setAddOpen(false)}
        onOk={() => void addResource()}
        okText="加入学习资源库"
        width={760}
      >
        <Form form={form} layout="vertical" className="resource-add-form">
          <Form.Item name="title" label="资源标题" rules={[{ required: true, message: '请输入标题' }]}>
            <Input maxLength={80} />
          </Form.Item>
          <div className="form-grid-two">
            <Form.Item name="topic" label="学习主题" rules={[{ required: true, message: '请选择主题' }]}>
              <Select
                options={TOPIC_OPTIONS.map((value) => ({ value, label: value }))}
                showSearch
                optionFilterProp="label"
              />
            </Form.Item>
            <Form.Item name="format" label="内容形式" rules={[{ required: true, message: '请选择形式' }]}>
              <Select options={FORMAT_OPTIONS.map((value) => ({ value, label: value }))} />
            </Form.Item>
            <Form.Item name="audience" label="目标受众" rules={[{ required: true, message: '请输入受众' }]}>
              <Input placeholder="例如：学生、家庭共读者或中医药文化爱好者" />
            </Form.Item>
            <Form.Item name="difficulty" label="阅读难度" rules={[{ required: true, message: '请选择难度' }]}>
              <Select options={DIFFICULTY_OPTIONS.map((value) => ({ value, label: value }))} />
            </Form.Item>
            <Form.Item name="source" label="来源" rules={[{ required: true, message: '请输入来源' }]}>
              <Input placeholder="例如：方剂与中药知识库" />
            </Form.Item>
            <Form.Item name="duration" label="预计时长" rules={[{ required: true, message: '请输入时长' }]}>
              <Input placeholder="例如：20 分钟" />
            </Form.Item>
          </div>
          <Form.Item name="summary" label="资源简介" rules={[{ required: true, message: '请输入简介' }]}>
            <TextArea rows={3} maxLength={240} showCount />
          </Form.Item>
          <Form.Item name="url" label="站内路径或外部链接">
            <Input placeholder="例如：/analysis 或 https://example.org" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default PrescriptionDatabase
