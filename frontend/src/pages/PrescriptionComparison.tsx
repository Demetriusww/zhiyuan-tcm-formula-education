import { useMemo, useState } from 'react'
import {
  AuditOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  PlusOutlined,
  SwapOutlined,
} from '@ant-design/icons'
import {
  App as AntdApp,
  Alert,
  Button,
  Card,
  Col,
  Input,
  Progress,
  Row,
  Tag,
} from 'antd'

const { TextArea } = Input

const RISK_TERMS = [
  '根治',
  '包治',
  '绝对',
  '无副作用',
  '千人一方',
  '替代医生',
  '秘方',
  '百分百',
  '药到病除',
  '永不复发',
]

interface Draft {
  id: number
  name: string
  text: string
}

interface DimensionScore {
  key: 'accuracy' | 'clarity' | 'evidence' | 'appeal' | 'accessibility'
  label: string
  score: number
  note: string
}

interface ReviewResult {
  overall: number
  dimensions: DimensionScore[]
  risks: string[]
  suggestions: string[]
}

const INITIAL_DRAFTS: Draft[] = [
  {
    id: 1,
    name: '草稿 A · 夸大表达',
    text:
      '这是祖传秘方，绝对适合所有人，千人一方，坚持服用就能根治失眠，而且无副作用。照着古籍抓药即可，也可以替代医生，不必再辨证。',
  },
  {
    id: 2,
    name: '草稿 B · 通识解释',
    text:
      '酸枣仁汤是《金匮要略》中的经典名方，组成包括酸枣仁、甘草、知母、茯苓和川芎。学习时可以观察酸枣仁与茯苓、知母、川芎之间如何围绕“虚劳虚烦不得眠”的传统表述配合。这里的功用和主治是中医证候语境中的文献表述，不能直接等同于现代疾病诊断。古籍剂量、炮制方法和是否适合某个人，都需要由中医师或药师结合具体情况判断，不能照着文字自行抓药。',
  },
]

const countMatches = (text: string, pattern: RegExp) => (text.match(pattern) || []).length

const reviewDraft = (text: string): ReviewResult => {
  const value = text.trim()
  const sentences = value.split(/[。！？!?；;]/).map((item) => item.trim()).filter(Boolean)
  const averageSentence = sentences.length
    ? Math.round(value.length / sentences.length)
    : value.length
  const risks = RISK_TERMS.filter((term) => value.includes(term))
  const hasSource = /出处|方源|出自|《.+》|版本/.test(value)
  const hasComposition = /组成|药味|味药|药材/.test(value)
  const hasPairing = /配伍|君臣佐使|主药|辅药|相须|相使|药对|配合/.test(value)
  const hasBoundary = /不等于|仍需|不能|不应|禁忌|炮制|辨证|专业|边界|个体/.test(value)
  const hasIndicationContext = /证候|传统|主治|功用|文献|语境/.test(value)
  const hasAudienceCue = /我们|公众|学习|理解|可以/.test(value)
  const jargonCount = countMatches(value, /君臣佐使|性味归经|辨证论治|炮制|证候|渊源/g)

  const accuracy = Math.max(
    30,
    Math.min(
      96,
      38 +
        (hasSource ? 24 : 0) +
        (hasIndicationContext ? 15 : 0) +
        (hasBoundary ? 12 : 0) -
        risks.length * 9,
    ),
  )
  const clarity = Math.max(
    28,
    Math.min(
      96,
      44 +
        (hasComposition ? 26 : 0) +
        (hasPairing ? 18 : 0) -
        Math.max(0, averageSentence - 48) * 0.55,
    ),
  )
  const evidence = Math.max(
    25,
    Math.min(
      96,
      34 +
        (hasSource ? 25 : 0) +
        (hasComposition ? 18 : 0) +
        (hasPairing ? 15 : 0),
    ),
  )
  const appeal = Math.max(
    30,
    Math.min(
      96,
      44 +
        (hasAudienceCue ? 18 : 0) +
        (hasPairing ? 14 : 0) +
        (/[？?]/.test(value) ? 6 : 0) -
        risks.length * 5,
    ),
  )
  const accessibility = Math.max(
    28,
    Math.min(
      96,
      40 +
        (hasBoundary ? 28 : 0) +
        (hasIndicationContext ? 14 : 0) +
        (hasAudienceCue ? 10 : 0) -
        Math.max(0, value.length - 420) * 0.05 -
        Math.max(0, jargonCount - 5) * 2,
    ),
  )

  const dimensions: DimensionScore[] = [
    {
      key: 'accuracy',
      label: '出处与表述',
      score: Math.round(accuracy),
      note: hasSource ? '已出现方源或文献线索。' : '建议补充方名、方源与文献线索。',
    },
    {
      key: 'clarity',
      label: '组成完整度',
      score: Math.round(clarity),
      note: hasComposition ? '已交代组成或药味信息。' : '建议列出组成，并说明药味数量。',
    },
    {
      key: 'evidence',
      label: '配伍解释',
      score: Math.round(evidence),
      note: hasPairing
        ? '已尝试解释药味之间的配合。'
        : '建议说明核心药味、辅助药味与配伍关系。',
    },
    {
      key: 'appeal',
      label: '公众可读性',
      score: Math.round(appeal),
      note: hasAudienceCue
        ? '语言面向学习与理解，而非诊疗指令。'
        : '可使用更清楚的公众解释语言。',
    },
    {
      key: 'accessibility',
      label: '安全边界',
      score: Math.round(accessibility),
      note: hasBoundary
        ? '已提示辨证、炮制或专业判断边界。'
        : '建议补充剂量、炮制、禁忌与专业指导提示。',
    },
  ]

  const suggestions: string[] = []
  if (risks.length) suggestions.push(`删除或弱化风险措辞：${risks.join('、')}。`)
  if (!hasSource) suggestions.push('补充方名、时代背景、方源与可核对的文献版本。')
  if (!hasComposition) suggestions.push('列出方剂组成，并区分原文、教材整理与通俗转写。')
  if (!hasPairing) suggestions.push('选择一个核心药味，解释它与其他药味的配伍关系。')
  if (!hasBoundary) {
    suggestions.push('补充辨证使用、古籍剂量、炮制、禁忌和特殊人群的安全边界。')
  }
  if (averageSentence > 60) suggestions.push('把长句拆分，先解释术语，再说明方剂结构。')
  if (!suggestions.length) suggestions.push('结构较完整，可继续核对古籍原文、药典标准与专业资料。')

  return {
    overall: Math.round(
      dimensions.reduce((sum, dimension) => sum + dimension.score, 0) / dimensions.length,
    ),
    dimensions,
    risks,
    suggestions,
  }
}

const scoreColor = (score: number) => {
  if (score >= 80) return '#3C8A62'
  if (score >= 60) return '#B48725'
  return '#C9533A'
}

const PrescriptionComparison: React.FC = () => {
  const { message } = AntdApp.useApp()
  const [drafts, setDrafts] = useState<Draft[]>(INITIAL_DRAFTS)
  const [reviewed, setReviewed] = useState(false)

  const results = useMemo(
    () => drafts.map((draft) => ({ draft, result: reviewDraft(draft.text) })),
    [drafts],
  )

  const updateDraft = (id: number, field: 'name' | 'text', value: string) => {
    setDrafts((current) =>
      current.map((draft) => (draft.id === id ? { ...draft, [field]: value } : draft)),
    )
    setReviewed(false)
  }

  const addDraft = () => {
    if (drafts.length >= 3) {
      message.info('一次最多比较三份科普草稿')
      return
    }
    setDrafts((current) => [
      ...current,
      {
        id: Date.now(),
        name: `草稿 ${String.fromCharCode(65 + current.length)}`,
        text: '',
      },
    ])
    setReviewed(false)
  }

  const removeDraft = (id: number) => {
    if (drafts.length <= 2) {
      message.warning('至少保留两份草稿进行比较')
      return
    }
    setDrafts((current) => current.filter((draft) => draft.id !== id))
    setReviewed(false)
  }

  const runComparison = () => {
    if (drafts.some((draft) => !draft.text.trim())) {
      message.warning('请为每份草稿输入内容')
      return
    }
    setReviewed(true)
  }

  const bestDraft = reviewed
    ? [...results].sort((a, b) => b.result.overall - a.result.overall)[0]
    : null

  return (
    <div className="page-shell comparison-page">
      <div className="page-heading page-heading-row">
        <div>
          <div className="page-eyebrow">
            <SwapOutlined />
            CONTENT REVIEW
          </div>
          <h1 className="page-title">科普内容评估</h1>
          <p className="page-description">
            并排比较两份或三份方剂科普草稿，从出处与表述、组成完整度、配伍解释、
            公众可读性和安全边界五个维度自查。评分用于改进表达，不替代文献核验与专业审阅。
          </p>
        </div>
        <Tag color="gold">科普内容自查</Tag>
      </div>

      <Alert
        type="info"
        showIcon
        className="comparison-method-alert"
        message="先比较表达是否守住了方剂通识的安全边界"
        description="平台会识别夸大疗效、千人一方、替代医生等风险说法，并检查方源、组成、配伍和剂量炮制提示。规则评分不能证明内容正确，仍需核对古籍版本、药典标准与专业资料。"
      />

      <Row gutter={[16, 16]}>
        {drafts.map((draft) => (
          <Col xs={24} lg={drafts.length === 3 ? 8 : 12} key={draft.id}>
            <Card
              className="comparison-editor-card"
              title={draft.name}
              extra={
                drafts.length > 2 ? (
                  <Button type="link" danger onClick={() => removeDraft(draft.id)}>
                    移除
                  </Button>
                ) : (
                  <Tag>待比较</Tag>
                )
              }
            >
              <div className="field-label">草稿名称</div>
              <Input
                value={draft.name}
                maxLength={24}
                onChange={(event) => updateDraft(draft.id, 'name', event.target.value)}
              />
              <div className="field-label comparison-text-label">方剂科普正文</div>
              <TextArea
                value={draft.text}
                onChange={(event) => updateDraft(draft.id, 'text', event.target.value)}
                autoSize={{ minRows: 10, maxRows: 16 }}
                maxLength={1200}
                showCount
                placeholder="粘贴一段面向公众的方剂通识草稿，例如介绍方源、组成、配伍和安全边界…"
              />
            </Card>
          </Col>
        ))}
      </Row>

      <div className="comparison-toolbar">
        <Button icon={<PlusOutlined />} onClick={addDraft} disabled={drafts.length >= 3}>
          添加第三份草稿
        </Button>
        <Button type="primary" size="large" icon={<AuditOutlined />} onClick={runComparison}>
          开始比较
        </Button>
      </div>

      {reviewed && (
        <section className="comparison-results">
          <div className="comparison-summary">
            <div>
              <span className="page-eyebrow">REVIEW RESULT</span>
              <h2>方剂科普表达对比</h2>
              <p>
                当前综合得分较高的是「{bestDraft?.draft.name}」。
                优先修复疗效夸大与安全边界缺口，再比较哪种解释更准确、更适合公众理解。
              </p>
            </div>
            <div className="comparison-legend">
              <span><i className="score-good" /> 80–100 较完整</span>
              <span><i className="score-mid" /> 60–79 可改进</span>
              <span><i className="score-low" /> 0–59 需重点修订</span>
            </div>
          </div>

          <Row gutter={[16, 16]}>
            {results.map(({ draft, result }) => (
              <Col xs={24} lg={drafts.length === 3 ? 8 : 12} key={draft.id}>
                <Card className="comparison-result-card">
                  <div className="comparison-score-header">
                    <div>
                      <span>{draft.name}</span>
                      <strong>{bestDraft?.draft.id === draft.id ? '当前较适合公众阅读' : '继续优化'}</strong>
                    </div>
                    <Progress
                      type="circle"
                      percent={result.overall}
                      size={78}
                      strokeColor={scoreColor(result.overall)}
                      format={(value) => <span className="comparison-score">{value}</span>}
                    />
                  </div>

                  <div className="comparison-dimension-list">
                    {result.dimensions.map((dimension) => (
                      <div key={dimension.key} className="comparison-dimension">
                        <div>
                          <span>{dimension.label}</span>
                          <strong>{dimension.score}</strong>
                        </div>
                        <Progress
                          percent={dimension.score}
                          showInfo={false}
                          strokeColor={scoreColor(dimension.score)}
                          size="small"
                        />
                        <small>{dimension.note}</small>
                      </div>
                    ))}
                  </div>

                  <div className={`comparison-risk ${result.risks.length ? 'has-risk' : 'is-clear'}`}>
                    {result.risks.length ? <ExclamationCircleOutlined /> : <CheckCircleOutlined />}
                    <div>
                      <strong>{result.risks.length ? '发现用药风险措辞' : '未发现明显风险措辞'}</strong>
                      <span>
                        {result.risks.length
                          ? result.risks.join('、')
                          : '仍建议核对方源、组成、古籍版本与安全提示。'}
                      </span>
                    </div>
                  </div>

                  <div className="comparison-suggestions">
                    <strong>改进建议</strong>
                    {result.suggestions.map((suggestion) => (
                      <p key={suggestion}>{suggestion}</p>
                    ))}
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        </section>
      )}
    </div>
  )
}

export default PrescriptionComparison
