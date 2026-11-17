import React from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ApartmentOutlined,
  ArrowLeftOutlined,
  BookOutlined,
  BulbOutlined,
  CameraOutlined,
  CheckCircleOutlined,
  EditOutlined,
  ExperimentOutlined,
  FileSearchOutlined,
  FileTextOutlined,
  MessageOutlined,
  SafetyCertificateOutlined,
  ShareAltOutlined,
} from '@ant-design/icons'
import { Alert, Button, Card, List, Steps } from 'antd'

const quickStartSteps = [
  {
    title: '选择方剂或中药',
    description: '从经典名方、十五类方剂或中药图鉴中选择一个学习对象。',
    icon: <MessageOutlined />,
  },
  {
    title: '核对出处与组成',
    description: '先确认方名、方源、类别和完整组成，再继续阅读功用与主治。',
    icon: <ExperimentOutlined />,
  },
  {
    title: '理解配伍与传统解说',
    description: '把药味放回全方，结合君臣佐使、性味归经和传统语境理解。',
    icon: <SafetyCertificateOutlined />,
  },
  {
    title: '查看安全边界',
    description: '区分古籍资料、公众科普与个人诊疗，保留剂量、炮制和用药提示。',
    icon: <BookOutlined />,
  },
]

const featureGuides = [
  {
    title: '方剂 AI 问答',
    icon: <MessageOutlined />,
    accent: '#0B6E69',
    steps: [
      '输入方名、药名或“君臣佐使”等通识问题，也可点击示例快速开始。',
      'DeepSeek 会结合平台随附的方剂资料，围绕方源、组成、传统功用、主治语境和安全边界讲解。',
      'AI 回答用于通识学习；复杂或个体化问题应继续查阅权威来源并咨询专业人员。',
    ],
  },
  {
    title: '方剂学习任务',
    icon: <BulbOutlined />,
    accent: '#E96B4C',
    steps: [
      '填写想了解的方剂、学习阶段、活动场景和可用时长。',
      '生成方源核对、组成梳理、配伍观察与分享成果等学习步骤。',
      '可把任务用于课堂、家庭共读或中医药文化科普活动。',
    ],
  },
  {
    title: '方剂拆解实验室',
    icon: <ExperimentOutlined />,
    accent: '#B48725',
    steps: [
      '从 118 首方剂中选择学习对象，先看方源、类别和完整组成。',
      '点击药味查看单味药资料，再对照传统功用、主治与同类方。',
      '页面只做资料化拆解，不预测疗效，也不判断方剂是否适合某个人。',
    ],
  },
  {
    title: '中药图鉴辨识',
    icon: <CameraOutlined />,
    accent: '#3C8A62',
    steps: [
      '从 52 张内置中药样片中选择一味药，查看名称、性味归经和关联方剂。',
      '也可在浏览器本地观察自己的图片，单张不超过 8 MB。',
      '页面不生成识别置信度；图片不能用于真伪鉴定、品质判断或实际用药决策。',
    ],
  },
  {
    title: '方剂与中药知识库',
    icon: <BookOutlined />,
    accent: '#2F7E88',
    steps: [
      '按十五类方剂或中药功能分组浏览，也可搜索方名、药名、出处和功用。',
      '打开条目查看方源、组成、传统功用、主治、配伍和资料线索。',
      '方药之间可以相互跳转，帮助从一首方认识其组成中药，再回到相关方剂。',
    ],
  },
  {
    title: '方剂知识图谱',
    icon: <ShareAltOutlined />,
    accent: '#486F91',
    steps: [
      '拖动和缩放关系网络，从方剂类别进入代表方与组成中药。',
      '结合类别构成、代表方和学习难度，发现不同方剂的关联入口。',
      '图谱呈现平台内的学习关系，不代表临床分类、疗效排序或用药推荐。',
    ],
  },
  {
    title: '方剂科普创作与评估',
    icon: <EditOutlined />,
    accent: '#C76A2A',
    steps: [
      '在创作工坊选择方剂、受众、形式和语气，再输入草稿或核心想法。',
      '根据结构建议补足方源、组成、传统功用、配伍解释和安全提示。',
      '在内容评估页比较草稿，定位夸大疗效、千人一方和缺少边界的表达。',
    ],
  },
  {
    title: '中医药权威来源核验',
    icon: <FileSearchOutlined />,
    accent: '#8E3F2C',
    steps: [
      '按机构、标准、古籍与资料领域筛选已整理的来源入口。',
      '访问原始机构或标准页面，核对发布者、版本、日期和适用范围。',
      '把古籍原文、药典标准、专业教材与公众科普放在各自的语境中理解。',
    ],
  },
]

const Guide: React.FC = () => {
  const navigate = useNavigate()

  return (
    <div className="page-shell guide-page">
      <div className="page-heading">
        <Button
          className="page-back-button"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/')}
        >
          返回首页
        </Button>
        <div className="page-eyebrow">
          <FileTextOutlined />
          HOW TO EXPLORE
        </div>
        <h1 className="page-title">使用指南</h1>
        <p className="page-description">
          从一首方或一味药出发，先核对资料，再理解方源、组成、配伍与安全边界。
          这份指南帮助你使用现有工具完成一次方剂通识学习。
        </p>
      </div>

      <section className="guide-quick-start">
        <div className="home-section-heading">
          <div>
            <span className="section-caption">四步开始学习</span>
            <h2>把一首方读成一份完整知识档案</h2>
          </div>
          <span className="eyebrow-chip">方剂通识 · AI 辅助</span>
        </div>
        <Steps
          current={-1}
          responsive
          items={quickStartSteps.map((step) => ({
            title: step.title,
            description: step.description,
            icon: step.icon,
          }))}
        />
      </section>

      <div className="guide-feature-grid">
        {featureGuides.map((feature) => (
          <Card
            className="guide-feature-card"
            key={feature.title}
            style={{ '--guide-accent': feature.accent } as React.CSSProperties}
          >
            <div className="guide-feature-heading">
              <span className="guide-feature-icon">{feature.icon}</span>
              <h2>{feature.title}</h2>
            </div>
            <List
              size="small"
              dataSource={feature.steps}
              renderItem={(item, index) => (
                <List.Item>
                  <span className="guide-step-number">{String(index + 1).padStart(2, '0')}</span>
                  <span>{item}</span>
                </List.Item>
              )}
            />
          </Card>
        ))}
      </div>

      <section className="guide-boundary">
        <div className="guide-boundary-heading">
          <span><CheckCircleOutlined /></span>
          <div>
            <h2>如何判断一次探索是否可靠</h2>
            <p>读懂一首方，既要看资料从哪里来，也要明确传统表述与现代诊疗之间的边界。</p>
          </div>
        </div>
        <div className="guide-boundary-grid">
          <div>
            <strong>来源可追溯</strong>
            <p>核对发布机构、古籍版本、药典标准与资料日期，避免只看二手转述。</p>
          </div>
          <div>
            <strong>组成要完整</strong>
            <p>先确认方名、方源、类别和全部药味，再阅读功用、主治与配伍解释。</p>
          </div>
          <div>
            <strong>放回辨证语境</strong>
            <p>传统功用和主治不能直接对应现代病名，也不能脱离证候与体质单独使用。</p>
          </div>
          <div>
            <strong>守住用药边界</strong>
            <p>剂量、炮制、禁忌、妊娠和特殊人群问题必须由中医师或药师判断。</p>
          </div>
        </div>
        <div className="guide-next-actions">
          <Button type="primary" icon={<ApartmentOutlined />} onClick={() => navigate('/analysis')}>
            开始方剂问答
          </Button>
          <Button icon={<FileSearchOutlined />} onClick={() => navigate('/evidence')}>
            核对权威来源
          </Button>
        </div>
      </section>

      <Alert
        className="guide-demo-alert"
        type="info"
        showIcon
        message="方剂 AI 问答已接入 DeepSeek"
        description="问答会结合平台随附的方剂与中药资料生成科普解释，适合公众阅读、课堂活动和中医药文化科普。平台不提供诊断、处方、个体剂量或自行用药建议；中药图片只用于学习辨识，不能用于真伪鉴定或品质判断。"
      />
    </div>
  )
}

export default Guide
