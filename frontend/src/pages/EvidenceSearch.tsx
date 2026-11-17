import { useMemo, useState } from 'react'
import {
  CalendarOutlined,
  CheckCircleOutlined,
  FileSearchOutlined,
  GlobalOutlined,
  LinkOutlined,
  SafetyCertificateOutlined,
  SearchOutlined,
} from '@ant-design/icons'
import { Alert, App as AntdApp, Button, Card, Empty, Input, Select, Tag } from 'antd'
import { AUTHORITY_SOURCES, type AuthoritySource } from '../data/scienceContent'

const { Search } = Input

const unique = (values: string[]) => Array.from(new Set(values))

const EvidenceSearch: React.FC = () => {
  const { message } = AntdApp.useApp()
  const [searchText, setSearchText] = useState('')
  const [keyword, setKeyword] = useState('')
  const [category, setCategory] = useState('')
  const [region, setRegion] = useState('')

  const categories = useMemo(
    () => unique(AUTHORITY_SOURCES.map((source) => source.category)),
    [],
  )
  const regions = useMemo(
    () => unique(AUTHORITY_SOURCES.map((source) => source.region)),
    [],
  )

  const results = AUTHORITY_SOURCES.filter((source) => {
    const query = keyword.toLowerCase()
    const matchesKeyword =
      !query ||
      [
        source.name,
        source.shortName,
        source.description,
        source.category,
        source.region,
        ...source.focus,
      ]
        .join(' ')
        .toLowerCase()
        .includes(query)
    return (
      matchesKeyword &&
      (!category || source.category === category) &&
      (!region || source.region === region)
    )
  })

  const openSource = (source: AuthoritySource) => {
    window.open(source.url, '_blank', 'noopener,noreferrer')
  }

  const copySource = async (source: AuthoritySource) => {
    try {
      await navigator.clipboard.writeText(source.url)
      message.success('来源链接已复制')
    } catch {
      message.info(source.url)
    }
  }

  return (
    <div className="page-shell evidence-page">
      <div className="page-heading page-heading-row">
        <div>
          <div className="page-eyebrow">
            <SafetyCertificateOutlined />
            VERIFIED TCM SOURCES
          </div>
          <h1 className="page-title">中医药权威来源核验</h1>
          <p className="page-description">
            从中医药主管部门、药典与标准、专业机构和公开资料入口开始核验。
            先确认发布主体，再核对古籍版本、术语语境与适用范围。
          </p>
        </div>
        <Tag color="success">{AUTHORITY_SOURCES.length} 个已整理来源</Tag>
      </div>

      <Alert
        type="info"
        showIcon
        className="source-method-alert"
        message="方剂与中药信息需要放回来源、版本和语境中理解"
        description="核对机构或作者、古籍版本与原文、药典标准及专业适用范围。图片、短视频和二次转述可以作为学习线索，但不能替代原文核对与专业判断。"
      />

      <Card className="source-search-card">
        <Search
          value={searchText}
          onChange={(event) => setSearchText(event.target.value)}
          onSearch={(value) => setKeyword(value.trim())}
          allowClear
          size="large"
          enterButton={<Button type="primary" icon={<SearchOutlined />}>检索来源</Button>}
          placeholder="搜索中医药机构、方剂主题、标准文件或资料领域"
        />
        <div className="source-filter-row">
          <Select
            value={category || undefined}
            onChange={(value) => setCategory(value || '')}
            allowClear
            placeholder="来源类型"
            options={categories.map((value) => ({ value, label: value }))}
          />
          <Select
            value={region || undefined}
            onChange={(value) => setRegion(value || '')}
            allowClear
            placeholder="地区或组织类型"
            options={regions.map((value) => ({ value, label: value }))}
          />
          <span>当前显示 {results.length} 个来源</span>
        </div>
      </Card>

      {results.length > 0 ? (
        <div className="source-card-grid">
          {results.map((source) => (
            <Card className="source-card" key={source.id}>
              <div className="source-card-header">
                <span className="source-mark" style={{ background: source.accent }}>
                  {source.shortName.slice(0, 2)}
                </span>
                <div>
                  <span>{source.category}</span>
                  <h2>{source.shortName}</h2>
                </div>
                <Tag>{source.region}</Tag>
              </div>
              <h3>{source.name}</h3>
              <p>{source.description}</p>
              <div className="source-focus-tags">
                {source.focus.map((item) => <Tag key={item}>{item}</Tag>)}
              </div>
              <div className="source-verified">
                <CalendarOutlined />
                <span>平台整理核验：{source.verifiedAt}</span>
              </div>
              <div className="source-card-actions">
                <Button icon={<LinkOutlined />} onClick={() => void copySource(source)}>
                  复制链接
                </Button>
                <Button type="primary" icon={<GlobalOutlined />} onClick={() => openSource(source)}>
                  访问来源
                </Button>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="source-empty">
          <Empty description="没有找到匹配的权威来源" />
        </Card>
      )}

      <section className="verification-guide">
        <div className="home-section-heading">
          <div>
            <div className="page-eyebrow">
              <FileSearchOutlined />
              VERIFY IN FOUR STEPS
            </div>
            <h2>四步核验一条方药信息</h2>
          </div>
        </div>
        <div className="verification-grid">
          {[
            ['01', '识别机构与作者', '确认内容由谁发布、谁审核，区分原始机构资料、媒体转载与个人解读。'],
            ['02', '核对古籍与版本', '回到方名、卷次、原文语境和版本差异，不把孤立的功效标签当成完整解释。'],
            ['03', '核对标准与范围', '查阅药典、炮制规范、教材或专业标准，确认名称、来源和适用范围。'],
            ['04', '检查用药边界', '区分传统知识、现代研究和个体诊疗，保留剂量、炮制、禁忌与专业指导提示。'],
          ].map(([number, title, detail]) => (
            <div key={number}>
              <span>{number}</span>
              <strong><CheckCircleOutlined /> {title}</strong>
              <p>{detail}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

export default EvidenceSearch
