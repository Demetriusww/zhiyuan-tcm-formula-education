import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  ArrowRightOutlined,
  BookOutlined,
  ClockCircleOutlined,
  CompassOutlined,
  FileSearchOutlined,
  LinkOutlined,
  ReadOutlined,
  SafetyCertificateOutlined,
  SearchOutlined,
} from '@ant-design/icons'
import { Button, Card, Empty, Input, Tag } from 'antd'
import HerbCategoryTree, {
  type KnowledgeTreeNode,
} from '../components/HerbCategoryTree'
import {
  HERBS,
  HERB_IMAGE_COUNT,
  KNOWLEDGE_ARTICLES,
  PRESCRIPTIONS,
  PRESCRIPTION_CATEGORIES,
  getArticleByName,
  getHerbsForPrescription,
  getPrescriptionsContainingHerb,
  hasHerbImage,
  type KnowledgeArticle,
} from '../data/scienceContent'

const { Search } = Input

const flattenNodeIds = (item: KnowledgeTreeNode): string[] => {
  if (!item.children?.length) return [item.id]
  return item.children.flatMap(flattenNodeIds)
}

const buildCategoryTree = (): KnowledgeTreeNode[] => {
  const formulaArticles = KNOWLEDGE_ARTICLES.filter((article) => article.prescription)
  const herbArticles = KNOWLEDGE_ARTICLES.filter((article) => article.herb)
  const herbGroups = Array.from(new Set(herbArticles.map((article) => article.group)))

  return [
    {
      id: 'formula-root',
      name: '经典名方',
      description: '按十五类方剂组织',
      meta: `${PRESCRIPTIONS.length} 首`,
      children: PRESCRIPTION_CATEGORIES.map((topic) => {
        const categoryArticles = formulaArticles.filter(
          (article) => article.prescription?.category === topic.name,
        )
        return {
          id: `topic-${topic.id}`,
          name: topic.name,
          description: topic.summary,
          meta: `${categoryArticles.length} 首`,
          children: categoryArticles.map((article) => ({
            id: article.id,
            name: article.title,
            description: `《${article.prescription?.source}》`,
            meta: `${article.prescription?.herb_names.length || 0} 味`,
          })),
        }
      }),
    },
    {
      id: 'herb-root',
      name: '中药图鉴',
      description: '按传统功能分类',
      meta: `${HERBS.length} 味`,
      children: herbGroups.map((group) => {
        const groupArticles = herbArticles.filter((article) => article.group === group)
        return {
          id: `herb-group-${group}`,
          name: group,
          description: '性味归经、功能与使用注意',
          meta: `${groupArticles.length} 味`,
          children: groupArticles.map((article) => ({
            id: article.id,
            name: article.title,
            description: article.herb?.pinyin,
            meta: article.imageAvailable ? '有图' : '文字',
          })),
        }
      }),
    },
  ]
}

const ArticleCard: React.FC<{
  article: KnowledgeArticle
  onOpen: () => void
}> = ({ article, onOpen }) => (
  <button type="button" className="knowledge-article-card" onClick={onOpen}>
    {article.imageAvailable && article.imageUrl && (
      <span className="knowledge-article-image">
        <img
          src={article.imageUrl}
          alt={`${article.herb?.name || article.title}本地图鉴图片`}
          loading="lazy"
        />
      </span>
    )}
    <div className="knowledge-article-meta">
      <Tag>{article.category}</Tag>
      <span><ClockCircleOutlined /> {article.readTime} 分钟</span>
    </div>
    <h3>{article.title}</h3>
    <p>{article.summary}</p>
    <div className="knowledge-article-footer">
      <span>{article.level} · {article.group}</span>
      <ArrowRightOutlined />
    </div>
  </button>
)

const HerbKnowledge: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const categoryTree = useMemo(buildCategoryTree, [])
  const initialArticle = searchParams.get('name')
    ? getArticleByName(searchParams.get('name') || '')
    : undefined
  const [searchText, setSearchText] = useState('')
  const [selectedKey, setSelectedKey] = useState(initialArticle?.id || '')
  const [selectedArticle, setSelectedArticle] = useState<KnowledgeArticle | null>(
    initialArticle || null,
  )
  const [filterLabel, setFilterLabel] = useState(initialArticle ? '直达知识条目' : '本期精选')
  const [visibleIds, setVisibleIds] = useState<string[]>(
    initialArticle
      ? [initialArticle.id]
      : KNOWLEDGE_ARTICLES.slice(0, 12).map((article) => article.id),
  )

  useEffect(() => {
    const name = searchParams.get('name')
    if (!name) return
    const article = getArticleByName(name)
    if (article) {
      setSelectedArticle(article)
      setSelectedKey(article.id)
      setVisibleIds([article.id])
      setFilterLabel('直达知识条目')
    }
  }, [searchParams])

  const visibleArticles = KNOWLEDGE_ARTICLES.filter((article) =>
    visibleIds.includes(article.id),
  )
  const relatedArticles = useMemo(() => {
    if (!selectedArticle) return []
    if (selectedArticle.prescription) {
      const formulaHerbs = new Set(selectedArticle.prescription.herb_names)
      return KNOWLEDGE_ARTICLES.filter(
        (article) =>
          article.id !== selectedArticle.id &&
          (article.prescription?.category === selectedArticle.prescription?.category ||
            (article.herb && formulaHerbs.has(article.herb.name))),
      ).slice(0, 4)
    }
    if (selectedArticle.herb) {
      const linkedPrescriptionIds = new Set(
        getPrescriptionsContainingHerb(selectedArticle.herb.name).map((item) => item.id),
      )
      return KNOWLEDGE_ARTICLES.filter(
        (article) =>
          article.id !== selectedArticle.id &&
          ((article.prescription && linkedPrescriptionIds.has(article.prescription.id)) ||
            (article.herb && article.group === selectedArticle.group)),
      ).slice(0, 4)
    }
    return []
  }, [selectedArticle])

  const openArticle = (article: KnowledgeArticle) => {
    setSelectedArticle(article)
    setSelectedKey(article.id)
    window.history.replaceState(null, '', `/herbs?name=${encodeURIComponent(article.title)}`)
  }

  const handleTreeSelect = (_key: string, item: KnowledgeTreeNode) => {
    setSelectedKey(item.id)
    const ids = flattenNodeIds(item)
    setVisibleIds(ids)
    setFilterLabel(item.name)
    const article = KNOWLEDGE_ARTICLES.find((entry) => entry.id === item.id)
    setSelectedArticle(article || null)
  }

  const handleSearch = (value: string) => {
    const keyword = value.trim().toLowerCase()
    setSearchText(value)
    if (!keyword) {
      setSelectedArticle(null)
      setSelectedKey('')
      setVisibleIds(KNOWLEDGE_ARTICLES.slice(0, 12).map((article) => article.id))
      setFilterLabel('本期精选')
      return
    }

    const results = KNOWLEDGE_ARTICLES.filter((article) =>
      [
        article.title,
        article.keyword,
        article.summary,
        article.content,
        article.category,
        article.group,
        article.source,
        article.prescription?.source || '',
        article.prescription?.functions || '',
        article.prescription?.indications || '',
        article.prescription?.herbs_raw || '',
        article.herb?.property || '',
        article.herb?.meridian || '',
        ...article.tags,
      ]
        .join(' ')
        .toLowerCase()
        .includes(keyword),
    )
    setVisibleIds(results.map((article) => article.id))
    setFilterLabel(`“${value.trim()}”的搜索结果`)
    if (results.length === 1) {
      setSelectedArticle(results[0])
      setSelectedKey(results[0].id)
    } else {
      setSelectedArticle(null)
      setSelectedKey('')
    }
  }

  const selectedPrescription = selectedArticle?.prescription
  const selectedHerb = selectedArticle?.herb
  const selectedFormulaHerbs = selectedPrescription
    ? getHerbsForPrescription(selectedPrescription)
    : []
  const selectedHerbPrescriptions = selectedHerb
    ? getPrescriptionsContainingHerb(selectedHerb.name).slice(0, 4)
    : []

  return (
    <div className="page-shell knowledge-page">
      <div className="page-heading page-heading-row">
        <div>
          <div className="page-eyebrow">
            <BookOutlined />
            FORMULA & HERB LIBRARY
          </div>
          <h1 className="page-title">方剂与中药知识库</h1>
          <p className="page-description">
            浏览十五类经典方剂及组成中药，查看方源、组成、传统功用、主治、
            配伍思路、性味归经与安全边界。内容用于公众通识学习。
          </p>
        </div>
        <Tag color="cyan">
          {PRESCRIPTIONS.length} 方 · {HERBS.length} 药 · {HERB_IMAGE_COUNT} 图
        </Tag>
      </div>

      <Card className="knowledge-search-card">
        <Search
          value={searchText}
          onChange={(event) => setSearchText(event.target.value)}
          onSearch={handleSearch}
          allowClear
          size="large"
          enterButton={
            <Button type="primary" icon={<SearchOutlined />}>
              检索方药
            </Button>
          }
          placeholder="搜索方名、出处、药名、功用、主治或性味归经"
        />
        <div className="knowledge-quick-tags">
          <span>方剂类别</span>
          {PRESCRIPTION_CATEGORIES.slice(0, 8).map((topic) => (
            <button type="button" key={topic.id} onClick={() => handleSearch(topic.name)}>
              {topic.name}
            </button>
          ))}
          <span className="knowledge-count">
            共 {PRESCRIPTIONS.length + HERBS.length} 个方药条目 · 15 类方剂
          </span>
        </div>
      </Card>

      <div className="knowledge-layout">
        <Card className="knowledge-tree-card" styles={{ body: { padding: 0 } }}>
          <HerbCategoryTree
            data={categoryTree}
            selectedKey={selectedKey}
            onSelect={handleTreeSelect}
            defaultExpandedKeys={['formula-root', 'topic-tonifying', 'herb-root']}
          />
        </Card>

        <div className="knowledge-detail-column">
          {selectedArticle ? (
            <Card className="knowledge-detail-card">
              <div className="knowledge-detail-header">
                <div>
                  <div className="knowledge-detail-kicker">
                    <Tag color="cyan">{selectedArticle.category}</Tag>
                    <span>{selectedArticle.group}</span>
                    <span><ClockCircleOutlined /> {selectedArticle.readTime} 分钟</span>
                  </div>
                  <h2>{selectedArticle.title}</h2>
                  <p>{selectedArticle.summary}</p>
                </div>
                <span className="knowledge-level">{selectedArticle.level}</span>
              </div>

              <div className="knowledge-detail-tags">
                {selectedArticle.tags.map((tag) => <Tag key={tag}>{tag}</Tag>)}
              </div>

              {selectedHerb && (
                <div className="formula-herb-panel">
                  <div className="formula-herb-grid is-profile">
                    {hasHerbImage(selectedHerb) && selectedArticle.imageUrl ? (
                      <img
                        className="formula-herb-detail"
                        src={selectedArticle.imageUrl}
                        alt={`${selectedHerb.name}本地图鉴图片`}
                      />
                    ) : (
                      <div className="formula-herb-detail formula-herb-placeholder">
                        <BookOutlined />
                        <strong>{selectedHerb.name} · 文字图鉴</strong>
                        <span>当前暂无本地图片，不使用外部占位图代替药材样貌。</span>
                      </div>
                    )}
                    <div className="formula-knowledge-facts">
                      <div><span>性味</span><strong>{selectedHerb.property}</strong></div>
                      <div><span>归经</span><strong>{selectedHerb.meridian}</strong></div>
                      <div><span>功能</span><strong>{selectedHerb.functions}</strong></div>
                      <div><span>传统主治</span><strong>{selectedHerb.indications}</strong></div>
                      <div><span>使用注意</span><strong>{selectedHerb.precautions}</strong></div>
                    </div>
                  </div>
                  <p className="chart-footnote">
                    图片仅用于学习辨识，不能作为真伪鉴定、品质判断、采购或用药依据。
                  </p>
                </div>
              )}

              {selectedPrescription && (
                <div className="formula-knowledge-facts formula-prescription-facts">
                  <div><span>方源</span><strong>《{selectedPrescription.source}》</strong></div>
                  <div><span>类别</span><strong>{selectedPrescription.category}</strong></div>
                  <div className="is-wide"><span>组成</span><strong>{selectedPrescription.herbs_raw}</strong></div>
                  <div><span>传统功用</span><strong>{selectedPrescription.functions}</strong></div>
                  <div className="is-wide"><span>传统主治</span><strong>{selectedPrescription.indications}</strong></div>
                  <div className="is-wide">
                    <span>关联中药</span>
                    <strong className="knowledge-herb-links">
                      {selectedFormulaHerbs.map((herb) => (
                        <button
                          type="button"
                          key={herb.name}
                          onClick={() => {
                            const article = KNOWLEDGE_ARTICLES.find(
                              (item) => item.herb?.name === herb.name,
                            )
                            if (article) openArticle(article)
                          }}
                        >
                          {herb.name}
                        </button>
                      ))}
                    </strong>
                  </div>
                </div>
              )}

              <div className="formula-reading-grid">
                {(selectedArticle.sections || [
                  { label: '通识说明', content: selectedArticle.content },
                ]).map((section) => (
                  <section
                    key={section.label}
                    className={section.label.includes('安全') ? 'formula-safety-panel' : ''}
                  >
                    <div className="knowledge-section-label">
                      {section.label.includes('安全') ? (
                        <SafetyCertificateOutlined />
                      ) : (
                        <ReadOutlined />
                      )}
                      {section.label}
                    </div>
                    <p>{section.content}</p>
                  </section>
                ))}
              </div>

              {selectedHerbPrescriptions.length > 0 && (
                <section className="formula-herb-prescriptions">
                  <div className="knowledge-section-label">
                    <CompassOutlined />
                    含此药的方剂
                  </div>
                  <div className="related-knowledge-grid">
                    {selectedHerbPrescriptions.map((prescription) => (
                      <button
                        type="button"
                        key={prescription.id}
                        onClick={() => {
                          const article = KNOWLEDGE_ARTICLES.find(
                            (item) => item.prescription?.id === prescription.id,
                          )
                          if (article) openArticle(article)
                        }}
                      >
                        <span>{prescription.category}</span>
                        <strong>{prescription.name}</strong>
                        <ArrowRightOutlined />
                      </button>
                    ))}
                  </div>
                </section>
              )}

              <div className="knowledge-source-row">
                <div>
                  <LinkOutlined />
                  <span>资料线索</span>
                  <strong>{selectedArticle.source}</strong>
                </div>
                <Button icon={<FileSearchOutlined />} onClick={() => navigate('/evidence')}>
                  核对权威来源
                </Button>
              </div>

              {relatedArticles.length > 0 && (
                <div className="related-knowledge">
                  <div className="knowledge-section-label">
                    <CompassOutlined />
                    继续学习
                  </div>
                  <div className="related-knowledge-grid">
                    {relatedArticles.map((article) => (
                      <button type="button" key={article.id} onClick={() => openArticle(article)}>
                        <span>{article.category}</span>
                        <strong>{article.title}</strong>
                        <ArrowRightOutlined />
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          ) : (
            <Card className="knowledge-list-card">
              <div className="knowledge-list-heading">
                <div>
                  <span className="section-caption">方药浏览</span>
                  <h2>{filterLabel}</h2>
                </div>
                <span>{visibleArticles.length} 个条目</span>
              </div>
              {visibleArticles.length > 0 ? (
                <div className="knowledge-article-grid">
                  {visibleArticles.map((article) => (
                    <ArticleCard
                      key={article.id}
                      article={article}
                      onOpen={() => openArticle(article)}
                    />
                  ))}
                </div>
              ) : (
                <Empty description="没有找到对应的方剂或中药，试试更短的方名、药名或出处" />
              )}
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

export default HerbKnowledge
