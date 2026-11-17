import { useState, type CSSProperties, type KeyboardEvent, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AppstoreOutlined,
  ArrowRightOutlined,
  BookOutlined,
  CameraOutlined,
  CompassOutlined,
  ExperimentOutlined,
  FileTextOutlined,
  MedicineBoxOutlined,
  PictureOutlined,
  QuestionCircleOutlined,
  ReadOutlined,
  SafetyCertificateOutlined,
  SearchOutlined,
  ShareAltOutlined,
} from '@ant-design/icons'
import { Button, Card, Col, Input, Row } from 'antd'
import {
  EDUCATION_NOTICE,
  HERBS,
  HERB_IMAGE_COUNT,
  HOME_QUESTIONS,
  PRESCRIPTIONS,
  PRESCRIPTION_CATEGORIES,
  SCIENCE_RESOURCES,
  getHerbByName,
  getHerbImageUrl,
  getPrescriptionByName,
  getPrescriptionsContainingHerb,
  hasHerbImage,
} from '../data/scienceContent'

const { Search } = Input

const SPECIMEN_NAMES = ['人参', '桂枝', '当归', '陈皮']

interface FormulaRole {
  herbName: string
  role: '君' | '臣' | '佐' | '使'
  description: string
}

interface FormulaStudy {
  name: string
  focus: string
  roles: FormulaRole[]
}

const FORMULA_STUDIES: FormulaStudy[] = [
  {
    name: '四君子汤',
    focus: '四味药如何共同完成益气健脾',
    roles: [
      ['人参', '君', '甘温益气，针对脾胃气虚的核心病机。'],
      ['白术', '臣', '健脾燥湿，帮助人参增强益气健脾之力。'],
      ['茯苓', '佐', '渗湿健脾，兼顾脾虚运化失常。'],
      ['甘草', '使', '益气和中，并调和方中诸药。'],
    ].map(([herbName, role, description]) => ({
      herbName,
      role: role as FormulaRole['role'],
      description,
    })),
  },
  {
    name: '桂枝汤',
    focus: '解表与和营如何在一首方中协同',
    roles: [
      ['桂枝', '君', '解肌发表，散外感风寒。'],
      ['白芍', '臣', '益阴敛营，与桂枝相配调和营卫。'],
      ['生姜', '佐', '助桂枝解表散寒，兼和胃止呕。'],
      ['大枣', '佐', '益气和中，滋脾生津。'],
      ['甘草', '使', '调和诸药，与桂枝、白芍相合。'],
    ].map(([herbName, role, description]) => ({
      herbName,
      role: role as FormulaRole['role'],
      description,
    })),
  },
  {
    name: '六味地黄丸',
    focus: '补与泻怎样形成有层次的配伍',
    roles: [
      ['熟地黄', '君', '滋肾填精，是滋补肾阴的主体药味。'],
      ['山茱萸', '臣', '养肝涩精，辅助熟地黄补益肝肾。'],
      ['山药', '臣', '补脾固精，兼顾脾肾。'],
      ['泽泻', '佐', '泻肾浊，与熟地黄相配体现补泻兼施。'],
      ['牡丹皮', '佐', '清虚热，制约温补药的偏性。'],
      ['茯苓', '佐', '渗脾湿，帮助脾运。'],
    ].map(([herbName, role, description]) => ({
      herbName,
      role: role as FormulaRole['role'],
      description,
    })),
  },
]

const TOOLS: Array<{
  title: string
  description: string
  path: string
  icon: ReactNode
  seal: string
  accent: string
}> = [
  {
    title: '方剂 AI 问答',
    description: '从出处、组成、功用与配伍关系提问，让大模型用通俗语言解释陌生术语。',
    path: '/analysis',
    icon: <QuestionCircleOutlined />,
    seal: '问',
    accent: '#0B6E69',
  },
  {
    title: '方剂拆解实验室',
    description: '逐味查看药味角色、药性依据与配伍层次，理解一首方为何这样组合。',
    path: '/efficacy',
    icon: <ExperimentOutlined />,
    seal: '拆',
    accent: '#B85C3E',
  },
  {
    title: '中药图鉴辨识',
    description: '结合现有 52 张本地药材图片，从外观、性味归经与关联方剂建立学习线索。',
    path: '/recognize',
    icon: <CameraOutlined />,
    seal: '识',
    accent: '#A66A2B',
  },
  {
    title: '方剂知识图谱',
    description: '沿类别、经典方与组成中药之间的关系浏览，形成可继续探索的知识地图。',
    path: '/visualization',
    icon: <ShareAltOutlined />,
    seal: '图',
    accent: '#3B7F89',
  },
]

const RESOURCE_IMAGE_NAMES = ['人参', '桂枝', '甘草', '陈皮']

const activateWithKeyboard = (
  event: KeyboardEvent<HTMLElement>,
  action: () => void,
) => {
  if (event.key !== 'Enter' && event.key !== ' ') return
  event.preventDefault()
  action()
}

const PrototypeHome: React.FC = () => {
  const navigate = useNavigate()
  const [searchValue, setSearchValue] = useState('')
  const [activeHerbName, setActiveHerbName] = useState(SPECIMEN_NAMES[0])
  const [activeFormulaName, setActiveFormulaName] = useState(FORMULA_STUDIES[0].name)
  const [activeRoleIndex, setActiveRoleIndex] = useState(0)

  const activeHerb = getHerbByName(activeHerbName)
  const activeHerbFormulas = activeHerb
    ? getPrescriptionsContainingHerb(activeHerb.name).slice(0, 2)
    : []

  const activeFormula =
    FORMULA_STUDIES.find((formula) => formula.name === activeFormulaName) ||
    FORMULA_STUDIES[0]
  const activeFormulaPrescription = getPrescriptionByName(activeFormula.name)
  const activeRole = activeFormula.roles[activeRoleIndex] || activeFormula.roles[0]
  const activeRoleHerb = getHerbByName(activeRole.herbName)

  const handleAsk = (value?: string) => {
    const question = (value ?? searchValue).trim()
    if (!question) return
    navigate(`/analysis?q=${encodeURIComponent(question)}`)
  }

  const openHerb = (herbName: string) => {
    navigate(`/herbs?name=${encodeURIComponent(herbName)}`)
  }

  const openFormula = (formulaName: string) => {
    navigate(`/efficacy?prescription=${encodeURIComponent(formulaName)}`)
  }

  const openFormulaRoleQuestion = () => {
    const question = `请向不了解中医的公众解释${activeFormula.name}中${activeRole.herbName}为什么属于“${activeRole.role}”，以及它与其他药味如何配伍。`
    navigate(`/analysis?q=${encodeURIComponent(question)}`)
  }

  return (
    <div className="home-page">
      <section className="home-hero" aria-labelledby="home-hero-title">
        <div className="home-hero-copy">
          <div className="hero-kicker-row">
            <span className="hero-kicker">
              <MedicineBoxOutlined />
              面向公众的中医方剂通识课堂
            </span>
            <span className="hero-classic-mark" aria-hidden="true">
              方
            </span>
          </div>

          <h1 id="home-hero-title">
            读懂一味药
            <br />
            理解一首方
          </h1>
          <p>
            从身边熟悉的药材出发，沿着出处、组成、君臣佐使与传统主治认识经典方剂。
            以 AI 问答辅助解释，以古籍线索和现有图鉴帮助核验，把专业术语讲成普通人听得懂的配伍逻辑。
          </p>

          <div className="hero-question-box">
            <Search
              value={searchValue}
              onChange={(event) => setSearchValue(event.target.value)}
              onSearch={handleAsk}
              enterButton={
                <Button type="primary" icon={<SearchOutlined />}>
                  开始读方
                </Button>
              }
              placeholder="输入方名、药名或困惑，例如：四君子汤为什么能补气？"
              aria-label="输入方剂或中药问题"
            />
          </div>

          <div className="hero-question-list" aria-label="常见问题">
            {HOME_QUESTIONS.slice(0, 4).map((question) => (
              <button type="button" key={question} onClick={() => handleAsk(question)}>
                {question}
              </button>
            ))}
          </div>

          <div className="hero-boundary-note">
            <SafetyCertificateOutlined />
            <span>只讲方剂通识、文化理解与知识核验，不提供个体诊断和自行用药建议。</span>
          </div>
        </div>

        <aside className="home-herb-showcase" aria-label="今日识药互动样本册">
          <div className="herb-showcase-heading">
            <div>
              <span>DAILY HERB SPECIMEN</span>
              <strong>今日识药</strong>
            </div>
            <span className="herb-seal" aria-hidden="true">
              标本
            </span>
          </div>

          {activeHerb && (
            <>
              <div className="herb-stage">
                <figure className="herb-photo-frame">
                  {hasHerbImage(activeHerb) ? (
                    <img
                      src={getHerbImageUrl(activeHerb)}
                      alt={`${activeHerb.name}本地药材图鉴图片`}
                    />
                  ) : (
                    <div className="herb-photo-placeholder">
                      <PictureOutlined />
                      <span>文字图鉴</span>
                    </div>
                  )}
                  <figcaption>
                    <span>NO. {String(SPECIMEN_NAMES.indexOf(activeHerbName) + 1).padStart(2, '0')}</span>
                    <span>{activeHerb.latin}</span>
                  </figcaption>
                </figure>

                <div className="herb-stage-copy">
                  <div className="herb-name-line">
                    <div>
                      <span>{activeHerb.pinyin}</span>
                      <h2>{activeHerb.name}</h2>
                    </div>
                    <span className="herb-taste-stamp">{activeHerb.property.split('，')[0]}</span>
                  </div>
                  <dl className="herb-nature-list">
                    <div>
                      <dt>性味</dt>
                      <dd>{activeHerb.property}</dd>
                    </div>
                    <div>
                      <dt>归经</dt>
                      <dd>{activeHerb.meridian}</dd>
                    </div>
                    <div>
                      <dt>功用</dt>
                      <dd>{activeHerb.functions}</dd>
                    </div>
                  </dl>
                  <button
                    type="button"
                    className="herb-detail-link"
                    onClick={() => openHerb(activeHerb.name)}
                  >
                    查看完整药材图鉴
                    <ArrowRightOutlined />
                  </button>
                </div>
              </div>

              <div className="herb-specimen-tabs" role="tablist" aria-label="切换识药样本">
                {SPECIMEN_NAMES.map((name, index) => {
                  const herb = getHerbByName(name)
                  if (!herb) return null
                  const active = name === activeHerbName
                  return (
                    <button
                      type="button"
                      role="tab"
                      aria-selected={active}
                      className={active ? 'is-active' : ''}
                      key={name}
                      onClick={() => setActiveHerbName(name)}
                    >
                      <span>{String(index + 1).padStart(2, '0')}</span>
                      <strong>{herb.name}</strong>
                      <small>{herb.pinyin}</small>
                    </button>
                  )
                })}
              </div>

              <div className="herb-formula-strip">
                <span>含此药的代表方</span>
                <div>
                  {activeHerbFormulas.length > 0 ? (
                    activeHerbFormulas.map((formula) => (
                      <button
                        type="button"
                        key={formula.id}
                        onClick={() => openFormula(formula.name)}
                      >
                        {formula.name}
                      </button>
                    ))
                  ) : (
                    <em>暂无关联方剂记录</em>
                  )}
                </div>
              </div>
            </>
          )}
        </aside>
      </section>

      <section className="home-section tool-section">
        <div className="home-section-heading">
          <div>
            <span className="section-eyebrow">AI + TCM LEARNING</span>
            <h2>从识药到读方</h2>
            <p>选择一种学习方式，把方剂知识放回出处、配伍与传统证候语境中理解。</p>
          </div>
          <Button type="link" onClick={() => navigate('/guide')}>
            查看使用指南
            <ArrowRightOutlined />
          </Button>
        </div>

        <Row gutter={[14, 14]}>
          {TOOLS.map((tool) => (
            <Col xs={24} sm={12} xl={6} key={tool.title}>
              <Card
                className="tool-card"
                role="button"
                tabIndex={0}
                aria-label={`进入${tool.title}`}
                onClick={() => navigate(tool.path)}
                onKeyDown={(event) => activateWithKeyboard(event, () => navigate(tool.path))}
                style={{ '--tool-accent': tool.accent } as CSSProperties}
              >
                <div className="tool-card-top">
                  <span className="tool-icon">{tool.icon}</span>
                  <span className="tool-seal" aria-hidden="true">
                    {tool.seal}
                  </span>
                </div>
                <h3>{tool.title}</h3>
                <p>{tool.description}</p>
                <div className="tool-card-foot">
                  <span>进入学习</span>
                  <ArrowRightOutlined className="tool-card-arrow" />
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      </section>

      <section className="home-section formula-anatomy-section">
        <div className="home-section-heading formula-anatomy-heading">
          <div>
            <span className="section-eyebrow">JUN · CHEN · ZUO · SHI</span>
            <h2>君臣佐使互动拆方</h2>
            <p>
              点击方中药味，查看它在传统配伍中的角色。这里展示的是帮助入门的结构解释，
              不是对个人证候的辨证结论。
            </p>
          </div>
          <span className="formula-heading-seal" aria-hidden="true">
            配伍
          </span>
        </div>

        <div className="formula-anatomy-layout">
          <div className="formula-picker" aria-label="选择拆解方剂">
            {FORMULA_STUDIES.map((formula) => {
              const prescription = getPrescriptionByName(formula.name)
              const active = formula.name === activeFormulaName
              return (
                <button
                  type="button"
                  className={active ? 'is-active' : ''}
                  key={formula.name}
                  onClick={() => {
                    setActiveFormulaName(formula.name)
                    setActiveRoleIndex(0)
                  }}
                >
                  <span>{prescription?.category || '经典名方'}</span>
                  <strong>{formula.name}</strong>
                  <small>{formula.focus}</small>
                  <i aria-hidden="true">{formula.roles.length} 味</i>
                </button>
              )
            })}
            <div className="formula-picker-note">
              <BookOutlined />
              <span>方源与组成来自平台现有方剂资料。</span>
            </div>
          </div>

          <div className="formula-stage">
            <div className="formula-stage-header">
              <div>
                <span>当前拆解</span>
                <h3>{activeFormula.name}</h3>
                <p>
                  {activeFormulaPrescription
                    ? `《${activeFormulaPrescription.source}》 · ${activeFormulaPrescription.functions}`
                    : activeFormula.focus}
                </p>
              </div>
              <span className="formula-stage-count">
                <strong>{activeFormula.roles.length}</strong>
                <small>味药</small>
              </span>
            </div>

            <div className="formula-role-grid" aria-label={`${activeFormula.name}药味角色`}>
              {activeFormula.roles.map((role, index) => {
                const herb = getHerbByName(role.herbName)
                const active = index === activeRoleIndex
                return (
                  <button
                    type="button"
                    className={active ? 'is-active' : ''}
                    data-role={role.role}
                    key={`${activeFormula.name}-${role.herbName}`}
                    onClick={() => setActiveRoleIndex(index)}
                    aria-pressed={active}
                  >
                    <span className="role-seal">{role.role}</span>
                    <span className="role-herb-copy">
                      <strong>{role.herbName}</strong>
                      <small>{herb?.property || '查看药性'}</small>
                    </span>
                    <ArrowRightOutlined />
                  </button>
                )
              })}
            </div>

            {activeRoleHerb && (
              <div className="role-inspector">
                <div className="role-inspector-visual">
                  {hasHerbImage(activeRoleHerb) ? (
                    <img
                      src={getHerbImageUrl(activeRoleHerb)}
                      alt={`${activeRoleHerb.name}本地药材图鉴图片`}
                    />
                  ) : (
                    <div className="role-herb-placeholder">
                      <MedicineBoxOutlined />
                      <span>文字图鉴</span>
                    </div>
                  )}
                  <span className="role-inspector-stamp">{activeRole.role}</span>
                </div>
                <div className="role-inspector-copy">
                  <div className="role-inspector-title">
                    <span>{activeRole.role}药</span>
                    <h4>{activeRole.herbName}</h4>
                    <small>{activeRoleHerb.pinyin}</small>
                  </div>
                  <p>{activeRole.description}</p>
                  <div className="role-herb-facts">
                    <span>{activeRoleHerb.property}</span>
                    <span>{activeRoleHerb.meridian}</span>
                  </div>
                  <div className="role-inspector-actions">
                    <Button
                      icon={<BookOutlined />}
                      onClick={() => openHerb(activeRoleHerb.name)}
                    >
                      查看药材
                    </Button>
                    <Button
                      type="primary"
                      icon={<QuestionCircleOutlined />}
                      onClick={openFormulaRoleQuestion}
                    >
                      问 AI
                    </Button>
                  </div>
                </div>
              </div>
            )}

            <div className="formula-safety-note">
              <SafetyCertificateOutlined />
              <span>{EDUCATION_NOTICE} 药味角色用于通识理解，不能脱离原方与辨证语境单独套用。</span>
            </div>
          </div>
        </div>
      </section>

      <section className="home-section topic-section">
        <div className="home-section-heading">
          <div>
            <span className="section-eyebrow">FORMULA CATEGORIES</span>
            <h2>拉开十五格方剂药柜</h2>
            <p>从补益、解表、清热到祛暑，按传统方剂门类建立一张循序渐进的学习地图。</p>
          </div>
          <Button type="link" onClick={() => navigate('/herbs')}>
            进入知识库
            <ArrowRightOutlined />
          </Button>
        </div>

        <div className="topic-grid">
          {PRESCRIPTION_CATEGORIES.map((topic, index) => (
            <button
              type="button"
              className="topic-card"
              key={topic.id}
              onClick={() => navigate(`/similarity?topic=${encodeURIComponent(topic.name)}`)}
              style={{ '--topic-accent': topic.accent } as CSSProperties}
            >
              <div className="topic-card-top">
                <span className="topic-cabinet-handle" aria-hidden="true" />
                <span className="topic-index">{String(index + 1).padStart(2, '0')}</span>
                <span className="topic-count">{topic.count} 方</span>
              </div>
              <span className="topic-category">{topic.category}</span>
              <strong>{topic.name}</strong>
              <p className="topic-summary">{topic.summary}</p>
              <div className="topic-samples">
                {topic.examples.slice(0, 2).map((name) => (
                  <span key={name}>{name}</span>
                ))}
              </div>
              <div className="topic-action">
                抽取这一类
                <ArrowRightOutlined />
              </div>
            </button>
          ))}
        </div>
      </section>

      <section className="home-section metrics-section" aria-label="平台数据">
        <div className="metrics-heading">
          <div>
            <span className="section-eyebrow">LEARNING COLLECTION</span>
            <h2>一套可核验的方药学习资料</h2>
          </div>
          <p>以现有资料为边界，用 AI 辅助解释，用图片、方源和知识关联支持继续阅读。</p>
        </div>
        <div className="home-metrics">
          <div className="metric-item">
            <span className="metric-icon"><BookOutlined /></span>
            <div>
              <strong>{PRESCRIPTIONS.length}<small> 首</small></strong>
              <span>经典方剂</span>
            </div>
          </div>
          <div className="metric-item">
            <span className="metric-icon"><MedicineBoxOutlined /></span>
            <div>
              <strong>{HERBS.length}<small> 味</small></strong>
              <span>常用中药</span>
            </div>
          </div>
          <div className="metric-item">
            <span className="metric-icon"><PictureOutlined /></span>
            <div>
              <strong>{HERB_IMAGE_COUNT}<small> 张</small></strong>
              <span>本地药材图片</span>
            </div>
          </div>
          <div className="metric-item">
            <span className="metric-icon"><AppstoreOutlined /></span>
            <div>
              <strong>{PRESCRIPTION_CATEGORIES.length}<small> 类</small></strong>
              <span>方剂门类</span>
            </div>
          </div>
        </div>
      </section>

      <section className="home-section resource-section">
        <div className="home-section-heading">
          <div>
            <span className="section-eyebrow">CONTINUE LEARNING</span>
            <h2>继续读方与识药</h2>
            <p>从一篇图文、一项互动工具或一个学习任务开始，把零散知识串成完整脉络。</p>
          </div>
          <Button type="link" onClick={() => navigate('/database')}>
            查看全部资源
            <ArrowRightOutlined />
          </Button>
        </div>

        <Row gutter={[14, 14]}>
          {SCIENCE_RESOURCES.slice(0, 4).map((resource, index) => {
            const imageHerb = getHerbByName(RESOURCE_IMAGE_NAMES[index])
            return (
              <Col xs={24} sm={12} xl={6} key={resource.id}>
                <Card
                  className="resource-card"
                  role="button"
                  tabIndex={0}
                  aria-label={`打开资源：${resource.title}`}
                  onClick={() => navigate(resource.url)}
                  onKeyDown={(event) =>
                    activateWithKeyboard(event, () => navigate(resource.url))
                  }
                >
                  <div className="resource-cover">
                    {imageHerb && hasHerbImage(imageHerb) && (
                      <img
                        src={getHerbImageUrl(imageHerb)}
                        alt={`${imageHerb.name}学习资源配图`}
                        loading="lazy"
                      />
                    )}
                    <span className="resource-cover-wash" aria-hidden="true" />
                    <span className="resource-cover-number">
                      {String(index + 1).padStart(2, '0')}
                    </span>
                    <span className="resource-cover-format">{resource.format}</span>
                  </div>
                  <div className="resource-expression">
                    <span className="resource-expression-mark" aria-hidden="true">
                      {index === 0 ? '方' : index === 1 ? '辨' : index === 2 ? '解' : '药'}
                    </span>
                    <div className="resource-meta">
                      <span>{resource.topic}</span>
                      <span>{resource.duration}</span>
                    </div>
                  </div>
                  <h3>{resource.title}</h3>
                  <p>{resource.summary}</p>
                  <div className="resource-footer">
                    <span>{resource.source}</span>
                    <ArrowRightOutlined />
                  </div>
                </Card>
              </Col>
            )
          })}
        </Row>

        <div className="home-reading-note">
          <CompassOutlined />
          <span>建议从一首方进入：先看方源，再读组成，最后追问君臣佐使与安全边界。</span>
          <Button type="link" onClick={() => navigate('/herbs')}>
            <ReadOutlined />
            打开方药知识库
          </Button>
          <FileTextOutlined className="home-reading-note-mark" aria-hidden="true" />
        </div>
      </section>
    </div>
  )
}

export default PrototypeHome
