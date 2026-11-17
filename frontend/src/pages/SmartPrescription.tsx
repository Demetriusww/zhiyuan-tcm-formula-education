import { useState } from 'react'
import {
  BulbOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExperimentOutlined,
  FileTextOutlined,
  RocketOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons'
import { App as AntdApp, Button, Card, Col, Input, Progress, Row, Select, Slider, Tag } from 'antd'
import {
  EDUCATION_NOTICE,
  PRESCRIPTIONS,
  PRESCRIPTION_CATEGORIES,
  getPrescriptionsByCategory,
} from '../data/scienceContent'

const { TextArea } = Input

interface TaskPlan {
  title: string
  question: string
  hypothesis: string
  steps: string[]
  activity: string
  output: string
  checks: string[]
}

const LEVEL_OPTIONS = [
  { value: '入门学习者', label: '入门学习者' },
  { value: '进阶学习者', label: '进阶学习者' },
  { value: '教师与传播者', label: '教师与传播者' },
]

const MODE_OPTIONS = [
  { value: '方剂通识', label: '方剂通识' },
  { value: '经典名方解读', label: '经典名方解读' },
  { value: '中药关联学习', label: '中药关联学习' },
  { value: '安全边界复习', label: '安全边界复习' },
]

const SmartPrescription: React.FC = () => {
  const { message } = AntdApp.useApp()
  const [question, setQuestion] = useState('四君子汤为什么被称为补气基础方？')
  const [topic, setTopic] = useState('补益剂')
  const [level, setLevel] = useState('入门学习者')
  const [minutes, setMinutes] = useState(30)
  const [mode, setMode] = useState('经典名方解读')
  const [plan, setPlan] = useState<TaskPlan | null>(null)

  const generatePlan = () => {
    const value = question.trim()
    if (!value) {
      message.warning('请先输入一个方剂学习问题')
      return
    }

    const mentioned = PRESCRIPTIONS.find((item) => value.includes(item.name))
    const categoryFormulas = getPrescriptionsByCategory(topic)
    const target = mentioned || categoryFormulas[0]
    if (!target) {
      message.warning('当前主题暂无方剂资料，请选择其他方剂类别')
      return
    }

    const categoryPeers = getPrescriptionsByCategory(target.category)
      .filter((item) => item.id !== target.id)
      .slice(0, 3)
    setPlan({
      title: `${mode}：${target.name}`,
      question: value,
      hypothesis: `${target.name}属于${target.category}，资料标注出自《${target.source}》，记录组成共 ${target.herb_names.length} 味。任务不预设诊疗结论，而是检验“原文线索、组成、功用、主治与安全边界”能否相互对应。`,
      steps: [
        `先核对方名、类别与出处，记录《${target.source}》这一线索需要进一步查证的版本信息。`,
        `列出组成：${target.herbs_raw}。把每味药放回全方，而不是只背单味药功效。`,
        `用“${target.functions}”和“${target.indications}”梳理传统功用与主治的语境，标记不懂的术语。`,
        categoryPeers.length
          ? `与${categoryPeers.map((item) => item.name).join('、')}比较类别、共同药味与关键差异。`
          : '查找同类别其他方剂，尝试比较组成与主治表述。',
        '整理剂量、炮制、妊娠用药、配伍禁忌和特殊人群提示，区分资料阅读与个体用药建议。',
        `用 ${minutes <= 20 ? '一张学习卡' : '一份短讲稿'} 向${level}解释这首方，并保留至少一条待查证问题。`,
      ],
      activity: `打开“方剂拆解实验室”，选择${target.name}查看组成药味、类别、出处、同类方与安全边界；也可在知识库搜索关联中药。`,
      output:
        minutes <= 20
          ? `一张${target.name}学习卡：出处、组成、功用、主治、一个配伍观察和一条安全提示`
          : `一份${target.name}公众解读稿：源流、组成、配伍、同类方比较、适用边界与参考资料`,
      checks: [
        `是否把${target.name}的${target.herb_names.length}味组成药完整列出？`,
        '是否区分了传统功用主治表述与现代疾病、药效概念？',
        '是否至少比较了一首同类别方剂？',
        '是否明确没有提供个体诊断、剂量或自行用药建议？',
        '是否指出古籍版本、剂量与炮制仍需专业核验？',
      ],
    })
    setTopic(target.category)
    message.success(`已生成${target.name}的方剂学习任务`)
  }

  return (
    <div className="page-shell">
      <div className="page-heading page-heading-row">
        <div>
          <div className="page-eyebrow">
            <RocketOutlined />
            FORMULA LEARNING TASK
          </div>
          <h1 className="page-title">方剂学习任务</h1>
          <p className="page-description">
            从方名或学习问题出发，生成一份围绕出处、组成、功用、主治、同类方与安全边界的学习路径。
            适合课堂、家庭共读和中医药文化科普活动。
          </p>
        </div>
        <Tag color="cyan">本地资料 · 规则生成</Tag>
      </div>

      <Row gutter={[20, 20]}>
        <Col xs={24} lg={9}>
          <Card title="设置读方任务" className="sticky-card">
            <div className="field-label">想理解哪首方或哪个问题？</div>
            <TextArea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              autoSize={{ minRows: 3, maxRows: 5 }}
              maxLength={120}
              showCount
              placeholder="例如：桂枝汤与麻黄汤同为解表，配伍有什么不同？"
            />

            <div className="form-grid-two">
              <div>
                <div className="field-label">方剂类别</div>
                <Select
                  value={topic}
                  onChange={setTopic}
                  options={PRESCRIPTION_CATEGORIES.map((item) => ({
                    value: item.name,
                    label: item.name,
                  }))}
                  style={{ width: '100%' }}
                />
              </div>
              <div>
                <div className="field-label">学习对象</div>
                <Select value={level} onChange={setLevel} options={LEVEL_OPTIONS} style={{ width: '100%' }} />
              </div>
            </div>

            <div className="field-label">任务类型</div>
            <Select value={mode} onChange={setMode} options={MODE_OPTIONS} style={{ width: '100%' }} />

            <div className="slider-label-row">
              <span className="field-label">可用时长</span>
              <strong>{minutes} 分钟</strong>
            </div>
            <Slider min={10} max={60} step={5} value={minutes} onChange={setMinutes} />

            <Button type="primary" block size="large" icon={<BulbOutlined />} onClick={generatePlan}>
              生成学习任务
            </Button>
            <p className="form-hint">
              未在问题中识别到方名时，默认从所选类别中选取第一首方剂。
            </p>
          </Card>
        </Col>

        <Col xs={24} lg={15}>
          {!plan ? (
            <Card className="empty-plan-card">
              <div className="empty-plan-visual">
                <ExperimentOutlined />
              </div>
              <h2>从一首方开始，建立完整读方框架</h2>
              <p>
                不只记住功效标签，还要回到出处、组成药味、传统主治与安全边界。
                填写左侧信息后，平台会围绕真实方剂资料生成学习任务。
              </p>
              <div className="plan-preview-list">
                <span>01 核对方源</span>
                <span>02 拆解组成</span>
                <span>03 比较同类方</span>
                <span>04 讲清边界</span>
              </div>
            </Card>
          ) : (
            <div className="plan-result">
              <Card>
                <div className="plan-result-header">
                  <div>
                    <div className="page-eyebrow">FORMULA STUDY PLAN</div>
                    <h2>{plan.title}</h2>
                    <p>{plan.question}</p>
                  </div>
                  <Progress
                    type="circle"
                    percent={Math.min(96, 58 + Math.round(minutes / 2))}
                    size={82}
                    strokeColor="#0B6E69"
                    format={(value) => <span className="plan-score">{value}<small>%</small></span>}
                  />
                </div>
                <div className="plan-tags">
                  <Tag>{topic}</Tag>
                  <Tag>{level}</Tag>
                  <Tag icon={<ClockCircleOutlined />}>{minutes} 分钟</Tag>
                  <Tag>{mode}</Tag>
                </div>
              </Card>

              <Row gutter={[16, 16]} className="result-row">
                <Col xs={24} md={12}>
                  <Card title="读方线索" size="small">
                    <div className="hypothesis-box">
                      <BulbOutlined />
                      <p>{plan.hypothesis}</p>
                    </div>
                  </Card>
                </Col>
                <Col xs={24} md={12}>
                  <Card title="推荐学习入口" size="small">
                    <div className="activity-box">
                      <ExperimentOutlined />
                      <p>{plan.activity}</p>
                    </div>
                  </Card>
                </Col>
              </Row>

              <Card title="学习步骤" className="result-card">
                <div className="investigation-steps">
                  {plan.steps.map((step, index) => (
                    <div className="investigation-step" key={step}>
                      <span>{String(index + 1).padStart(2, '0')}</span>
                      <p>{step}</p>
                    </div>
                  ))}
                </div>
              </Card>

              <Row gutter={[16, 16]} className="result-row">
                <Col xs={24} md={14}>
                  <Card title="成果形式" size="small">
                    <div className="output-format">
                      <FileTextOutlined />
                      <span>{plan.output}</span>
                    </div>
                  </Card>
                </Col>
                <Col xs={24} md={10}>
                  <Card title="完成前自查" size="small">
                    <div className="check-list">
                      {plan.checks.map((check) => (
                        <div key={check}>
                          <CheckCircleOutlined />
                          <span>{check}</span>
                        </div>
                      ))}
                    </div>
                  </Card>
                </Col>
              </Row>

              <div className="science-note">
                <SafetyCertificateOutlined />
                <span>
                  {EDUCATION_NOTICE} 学习任务用于理解方剂知识，
                  不生成处方、剂量或针对个人的治疗方案。
                </span>
              </div>
            </div>
          )}
        </Col>
      </Row>
    </div>
  )
}

export default SmartPrescription
