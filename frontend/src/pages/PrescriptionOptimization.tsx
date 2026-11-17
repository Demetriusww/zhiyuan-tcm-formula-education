import { useMemo, useState } from 'react'
import {
  AuditOutlined,
  CheckCircleOutlined,
  EditOutlined,
  FileTextOutlined,
  ReadOutlined,
  SafetyCertificateOutlined,
  SendOutlined,
} from '@ant-design/icons'
import { App as AntdApp, Button, Card, Col, Input, Progress, Row, Select, Tabs, Tag } from 'antd'
import {
  EDUCATION_NOTICE,
  PRESCRIPTIONS,
  PRESCRIPTION_CATEGORIES,
  getHerbsForPrescription,
  getPrescriptionByName,
  getPrescriptionsByCategory,
} from '../data/scienceContent'

const { TextArea } = Input

const AUDIENCE_OPTIONS = [
  '中小学生',
  '普通公众',
  '教师与家长',
  '中医药文化爱好者',
  '社区科普志愿者',
].map((value) => ({ value, label: value }))

const FORMAT_OPTIONS = ['短图文', '长文章', '三分钟讲稿', '课堂互动脚本', '短视频文案'].map(
  (value) => ({ value, label: value }),
)

const TONE_OPTIONS = ['清晰平实', '故事化', '严谨克制', '轻量活泼'].map((value) => ({
  value,
  label: value,
}))

const SAMPLE_DRAFT =
  '四君子汤为什么叫“四君子”？可以把四味药想象成四位分工不同的搭档：人参补气，白术健脾，茯苓渗湿，甘草调和。资料记载它出自《太平惠民和剂局方》，传统功用为益气健脾。读这首方时，不能只记“补气”两个字，还要看每味药如何互相配合。需要注意的是，方剂知识不能替代辨证和个体用药建议，古籍剂量也不能直接照搬。'

const RISK_PATTERN = /包治|根治|无副作用|千人一方|替代医生|秘方|百分百|药到病除|绝对有效/

interface WorkshopResult {
  title: string
  outline: Array<{ heading: string; detail: string }>
  opening: string
  checks: Array<{ label: string; status: 'good' | 'improve'; note: string }>
  score: number
}

const scoreDraft = (draft: string) => {
  let score = 30
  if (draft.length > 80) score += 12
  if (draft.length > 180) score += 8
  if (/《|出处|出自|方源/.test(draft)) score += 12
  if (/组成|药味|配伍|君药|臣药|佐药|使药/.test(draft)) score += 12
  if (/不能|不提供|禁忌|专业|辨证|剂量|安全/.test(draft)) score += 14
  if (/例如|比如|想象|可以把/.test(draft)) score += 10
  if (/[？?]/.test(draft)) score += 4
  if (RISK_PATTERN.test(draft)) score -= 18
  return Math.max(25, Math.min(96, score))
}

const PrescriptionOptimization: React.FC = () => {
  const { message } = AntdApp.useApp()
  const [topic, setTopic] = useState('补益剂')
  const [formulaName, setFormulaName] = useState('四君子汤')
  const [audience, setAudience] = useState('普通公众')
  const [format, setFormat] = useState('短图文')
  const [tone, setTone] = useState('清晰平实')
  const [draft, setDraft] = useState(SAMPLE_DRAFT)
  const [result, setResult] = useState<WorkshopResult | null>(null)

  const qualityScore = useMemo(() => scoreDraft(draft), [draft])
  const categoryFormulas = useMemo(() => getPrescriptionsByCategory(topic), [topic])
  const selectedPrescription = getPrescriptionByName(formulaName) || categoryFormulas[0] || PRESCRIPTIONS[0]

  const changeTopic = (value: string) => {
    setTopic(value)
    const first = getPrescriptionsByCategory(value)[0]
    if (first) setFormulaName(first.name)
    setResult(null)
  }

  const generate = () => {
    const trimmed = draft.trim()
    if (!trimmed) {
      message.warning('请先输入一段方剂科普草稿或核心想法')
      return
    }

    const mentioned = PRESCRIPTIONS.find((item) => trimmed.includes(item.name))
    const target = mentioned || selectedPrescription
    const herbs = getHerbsForPrescription(target)
    const peers = getPrescriptionsByCategory(target.category)
      .filter((item) => item.id !== target.id)
      .slice(0, 3)
    const hasSource = /《|出处|出自|方源/.test(trimmed)
    const hasComposition =
      /组成|药味|配伍/.test(trimmed) ||
      target.herb_names.filter((herb) => trimmed.includes(herb)).length >= 2
    const hasSafety = /不能|不提供|禁忌|专业|辨证|剂量|安全/.test(trimmed)
    const hasPublicCue = /例如|比如|想象|可以把|[？?]/.test(trimmed)
    const hasRisk = RISK_PATTERN.test(trimmed)
    const score = scoreDraft(trimmed)

    setTopic(target.category)
    setFormulaName(target.name)
    setResult({
      title: `${target.name}｜给${audience}的方剂通识解读`,
      outline: [
        {
          heading: '从一个可理解的问题开始',
          detail: `可以从方名、生活化疑问或“为什么四味药能组成一首方”切入，先让${audience}知道这篇内容要解决什么阅读问题。`,
        },
        {
          heading: '交代方源与类别',
          detail: `说明${target.name}属于${target.category}，项目资料标注出自《${target.source}》。古籍出处仍需进一步核对版本与原文语境。`,
        },
        {
          heading: '完整呈现组成',
          detail: `按资料记录列出${target.herb_names.length}味药：${target.herbs_raw}。不要只写功效标签而省略组成。`,
        },
        {
          heading: '解释功用、主治与配伍',
          detail: `用“${target.functions}”和“${target.indications}”解释传统语境，并讨论${herbs.slice(0, 4).map((herb) => herb.name).join('、')}等药味在方中的分工。`,
        },
        {
          heading: '加入同类方比较',
          detail: peers.length
            ? `可将${target.name}与${peers.map((item) => item.name).join('、')}比较共同药味和组方重点，帮助读者理解“同类不等于同方”。`
            : '可补充同类别其他方剂，比较出处、组成与主治表述。',
        },
        {
          heading: '把安全边界放在结尾前',
          detail: '明确不诊断、不开方，提醒古籍剂量、炮制、妊娠禁忌、毒性药与十八反十九畏等必须由专业人员判断。',
        },
      ],
      opening:
        tone === '故事化'
          ? `如果四味药也有分工，${target.name}里的它们会怎样协作？理解一首方，可以从这个问题开始。`
          : tone === '轻量活泼'
            ? `${target.name}听起来像一张古方，其实也可以把它看成一份关于“药味如何配合”的学习说明书。`
            : `读懂${target.name}，可以从方源、组成和配伍三个问题开始。先看它由什么组成，再理解这些药味为什么放在同一首方里。`,
      checks: [
        {
          label: '方源与出处',
          status: hasSource ? 'good' : 'improve',
          note: hasSource ? '草稿已有方源或出处线索。' : '建议补充古籍、教材或权威资料线索。',
        },
        {
          label: '组成完整性',
          status: hasComposition ? 'good' : 'improve',
          note: hasComposition ? '草稿已涉及组成或配伍。' : `建议列出${target.name}的${target.herb_names.length}味组成药。`,
        },
        {
          label: '公众表达',
          status: hasPublicCue ? 'good' : 'improve',
          note: hasPublicCue ? '已有问题、例子或解释入口。' : '可以增加一个具体问题或生活化解释。',
        },
        {
          label: '安全边界',
          status: hasSafety ? 'good' : 'improve',
          note: hasSafety ? '已提醒专业指导或用药边界。' : '需要补充辨证、剂量和专业指导提示。',
        },
        {
          label: '风险措辞',
          status: hasRisk ? 'improve' : 'good',
          note: hasRisk ? '发现绝对化或包治式表达，建议删除。' : '未发现明显夸大疗效或千人一方表述。',
        },
      ],
      score,
    })
    message.success(`已围绕${target.name}生成结构与自查建议`)
  }

  return (
    <div className="page-shell formula-workshop-page">
      <div className="page-heading page-heading-row">
        <div>
          <div className="page-eyebrow">
            <EditOutlined />
            FORMULA STORYTELLING
          </div>
          <h1 className="page-title">方剂科普创作工坊</h1>
          <p className="page-description">
            围绕真实方剂的方源、组成、功用、主治、配伍与安全边界，组织面向公众的通识解读。
            平台提供结构和自查建议，不代替专业审稿。
          </p>
        </div>
        <Tag color="gold">内容结构助手</Tag>
      </div>

      <Row gutter={[20, 20]}>
        <Col xs={24} xl={10}>
          <Card title="创作设置">
            <div className="form-grid-two">
              <div>
                <div className="field-label">方剂类别</div>
                <Select
                  value={topic}
                  onChange={changeTopic}
                  options={PRESCRIPTION_CATEGORIES.map((item) => ({
                    value: item.name,
                    label: `${item.name} · ${item.count}首`,
                  }))}
                  style={{ width: '100%' }}
                />
              </div>
              <div>
                <div className="field-label">核心方剂</div>
                <Select
                  showSearch
                  value={selectedPrescription.name}
                  onChange={(value) => {
                    setFormulaName(value)
                    setResult(null)
                  }}
                  optionFilterProp="label"
                  options={categoryFormulas.map((item) => ({ value: item.name, label: item.name }))}
                  style={{ width: '100%' }}
                />
              </div>
            </div>

            <div className="form-grid-two">
              <div>
                <div className="field-label">目标受众</div>
                <Select value={audience} onChange={setAudience} options={AUDIENCE_OPTIONS} style={{ width: '100%' }} />
              </div>
              <div>
                <div className="field-label">内容形式</div>
                <Select value={format} onChange={setFormat} options={FORMAT_OPTIONS} style={{ width: '100%' }} />
              </div>
            </div>

            <div className="field-label">表达语气</div>
            <Select value={tone} onChange={setTone} options={TONE_OPTIONS} style={{ width: '100%' }} />

            <div className="workshop-formula-brief">
              <div>
                <span>{selectedPrescription.category}</span>
                <strong>{selectedPrescription.name}</strong>
                <p>{selectedPrescription.functions}；{selectedPrescription.indications}</p>
              </div>
              <Tag>{selectedPrescription.herb_names.length} 味</Tag>
            </div>

            <div className="field-label">草稿或核心想法</div>
            <TextArea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              autoSize={{ minRows: 8, maxRows: 14 }}
              maxLength={1000}
              showCount
              placeholder="写下你想怎样向公众解释一首方，例如方名由来、组成、配伍或安全边界…"
            />
            <div className="draft-score-row">
              <span>实时完整度</span>
              <Progress percent={qualityScore} size="small" strokeColor="#0B6E69" />
            </div>
            <Button type="primary" block size="large" icon={<SendOutlined />} onClick={generate}>
              生成方剂解读结构
            </Button>
          </Card>
        </Col>

        <Col xs={24} xl={14}>
          {!result ? (
            <Card className="workshop-empty">
              <div className="empty-plan-visual">
                <ReadOutlined />
              </div>
              <h2>把一首古方讲成一段可理解的通识内容</h2>
              <p>
                先交代它从哪里来、由什么组成，再解释传统功用与主治，最后讲清配伍关系和使用边界。
                当前将以{selectedPrescription.name}为示例。
              </p>
              <div className="plan-preview-list">
                <span>方源</span>
                <span>组成</span>
                <span>配伍</span>
                <span>同类方</span>
                <span>安全边界</span>
              </div>
            </Card>
          ) : (
            <Card
              title="创作建议"
              extra={
                <span className="result-score-inline">
                  <strong>{result.score}</strong>/100
                </span>
              }
            >
              <Tabs
                items={[
                  {
                    key: 'structure',
                    label: (
                      <span><FileTextOutlined /> 结构预览</span>
                    ),
                    children: (
                      <div className="article-preview">
                        <span className="preview-kicker">{format} · {audience}</span>
                        <h2>{result.title}</h2>
                        <p className="preview-opening">{result.opening}</p>
                        <div className="outline-list">
                          {result.outline.map((item, index) => (
                            <div key={item.heading}>
                              <span>{String(index + 1).padStart(2, '0')}</span>
                              <div>
                                <strong>{item.heading}</strong>
                                <p>{item.detail}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ),
                  },
                  {
                    key: 'review',
                    label: (
                      <span><AuditOutlined /> 质量自查</span>
                    ),
                    children: (
                      <div className="quality-check-list">
                        {result.checks.map((item) => (
                          <div key={item.label} className={`quality-check ${item.status}`}>
                            <CheckCircleOutlined />
                            <div>
                              <strong>{item.label}</strong>
                              <p>{item.note}</p>
                            </div>
                            <Tag color={item.status === 'good' ? 'success' : 'warning'}>
                              {item.status === 'good' ? '已覆盖' : '可加强'}
                            </Tag>
                          </div>
                        ))}
                      </div>
                    ),
                  },
                ]}
              />
            </Card>
          )}
          <div className="science-note">
            <SafetyCertificateOutlined />
            <span>
              {EDUCATION_NOTICE} 剂量、炮制、妊娠禁忌、毒性药和十八反十九畏等内容，
              应回到药典、专业教材和机构资料核对。
            </span>
          </div>
        </Col>
      </Row>
    </div>
  )
}

export default PrescriptionOptimization
