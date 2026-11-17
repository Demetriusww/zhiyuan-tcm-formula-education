import React from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowLeftOutlined,
  BookOutlined,
  CameraOutlined,
  DatabaseOutlined,
  ExperimentOutlined,
  FileSearchOutlined,
  MessageOutlined,
  QuestionCircleOutlined,
  SafetyCertificateOutlined,
  SwapOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Alert, Button, Collapse } from 'antd'

const faqData = [
  {
    category: '账号与收藏',
    icon: <UserOutlined />,
    questions: [
      {
        q: '使用平台需要注册真实账号吗？',
        a: '不需要。当前版本的登录与收藏状态保存在浏览器本地，不连接真实用户数据库。',
      },
      {
        q: '管理入口如何使用？',
        a: '用户名填写 admin、密码任意填写即可进入本地科普运营看板。平台不会校验密码，也不会把账号信息发送到服务器。',
      },
      {
        q: '收藏内容保存在哪里？',
        a: '方剂、中药和学习资源收藏保存在当前浏览器的 localStorage 中。清除浏览器站点数据或更换浏览器后，收藏记录不会自动同步。',
      },
    ],
  },
  {
    category: '方剂 AI 问答',
    icon: <MessageOutlined />,
    questions: [
      {
        q: '回答是怎样生成的？',
        a: '方剂 AI 问答由 DeepSeek 结合平台随附的方剂与中药资料生成。系统会先识别问题涉及的方名或药名，再把相关资料作为回答依据，用于讲解方源、组成、传统功用、主治语境和安全边界。',
      },
      {
        q: '为什么回答都强调出处和用药边界？',
        a: '方剂资料可能来自古籍、教材、药典或现代科普整理，版本、剂量和适用范围并不完全相同。流畅的表达不等于适合个人使用，仍需核对原始资料和专业意见。',
      },
      {
        q: '可以询问自己的症状该吃什么方吗？',
        a: '平台不提供个体诊断、处方或剂量建议。可以学习某首方的方源、组成与传统主治表述，但不能据此判断自己是否适用；实际用药应咨询中医师或药师。',
      },
    ],
  },
  {
    category: '学习任务与方剂拆解',
    icon: <ExperimentOutlined />,
    questions: [
      {
        q: '方剂学习任务会生成什么？',
        a: '系统会根据方剂、学习阶段、活动场景和时长，生成方源核对、组成梳理、配伍观察、分享成果与自查清单，适合课堂和家庭共读。',
      },
      {
        q: '方剂拆解实验室会预测疗效吗？',
        a: '不会。页面把方源、组成、传统功用、主治、药味资料和同类方放在一起，帮助建立阅读框架；不计算疗效，也不判断某首方是否适合某个人。',
      },
      {
        q: '怎样比较两首同类方？',
        a: '先核对各自方源和完整组成，再找共同药味、特有药味与传统主治表述的差异，最后把配伍差异放回具体证候语境，不能只按功效标签排序。',
      },
    ],
  },
  {
    category: '中药图鉴辨识',
    icon: <CameraOutlined />,
    questions: [
      {
        q: '上传的图片会被保存吗？',
        a: '不会上传。文件只在当前浏览器中生成预览，刷新页面后预览和本次查看记录会消失。',
      },
      {
        q: '上传药材图片后会自动识别吗？',
        a: '不会。当前版本只显示本地图片并提供观察清单，不生成药材名称、识别置信度、真伪或品质结论，需要时请交由具备资质的机构或专业人员鉴定。',
      },
      {
        q: '为什么图片不能用于判断药材品质？',
        a: '药材鉴别还可能涉及质地、断面、气味、炮制、显微与理化检查。单张图片受光线、角度、部位和加工方式影响，不能替代标准对照与专业检验。',
      },
      {
        q: '支持哪些图片？',
        a: '支持浏览器能够预览的 JPG、PNG、WebP 等图片，单张最大 8 MB。内置的 52 张中药图片和本地观察图片都只用于学习辨识。',
      },
    ],
  },
  {
    category: '方药知识库与资源库',
    icon: <BookOutlined />,
    questions: [
      {
        q: '知识条目中包含哪些信息？',
        a: '方剂条目包含方源、类别、组成、传统功用、主治、配伍与安全说明；中药条目包含性味、归经、功能、传统主治、参考用量、使用注意与关联方剂。',
      },
      {
        q: '资源库支持哪些内容形式？',
        a: '当前包含互动课程、图文长读、互动工具、学习任务和图鉴卡片，可按方剂类别、内容形式、学习阶段与收藏状态筛选。',
      },
      {
        q: '新增的资源会长期保存吗？',
        a: '新增和移除只影响当前页面会话，不会写入服务器。若需要保留资源清单，可以使用导出按钮下载当前筛选结果为 JSON。',
      },
    ],
  },
  {
    category: '方剂知识图谱',
    icon: <DatabaseOutlined />,
    questions: [
      {
        q: '知识图谱中的连线代表什么？',
        a: '连线呈现方剂类别、代表方、组成中药和学习条目之间的组织关系，用于帮助发现学习入口，不代表临床辨证关系、疗效排序或处方推荐。',
      },
      {
        q: '类别学习推荐是一种临床排名吗？',
        a: '不是。推荐依据平台内的类别、组成和阅读维度生成，用于内容发现与教学策划，不评价方剂优劣，也不说明某首方适合某位使用者。',
      },
    ],
  },
  {
    category: '来源核验与内容评估',
    icon: <FileSearchOutlined />,
    questions: [
      {
        q: '权威来源列表会自动更新吗？',
        a: '不会。当前来源信息为静态整理，页面会展示平台核验日期。访问来源后仍应检查最新版本、发布日期、古籍版本和具体适用范围。',
      },
      {
        q: '内容评估分数能证明内容正确吗？',
        a: '不能。评估只检查方源、组成完整性、公众表达、安全边界和措辞风险，不会自动验证方剂内容。事实审核仍需核对古籍、药典、教材和机构资料。',
      },
      {
        q: '为什么“绝对”“百分百”等词会被标出？',
        a: '这类措辞容易把有明确证候和适用条件的方剂知识说成对所有人有效。平台会提示删除或弱化，并补上辨证、剂量和专业指导边界。',
      },
    ],
  },
  {
    category: '平台边界与数据',
    icon: <SafetyCertificateOutlined />,
    questions: [
      {
        q: '需要启动后端服务吗？',
        a: '方剂 AI 问答需要启动本项目的 FastAPI 后端，并在 backend/.env 配置 DeepSeek API Key。方剂知识库、学习任务、图鉴观察和内容自查等页面仍可使用随项目提供的本地资料。',
      },
      {
        q: '页面数据会发送到第三方吗？',
        a: '使用方剂 AI 问答时，当前问题及最近对话会发送给 DeepSeek 以生成科普回答；中药图片不会随问答发送。API Key 只保存在后端环境变量中，不会写入前端。外部来源只有在点击“访问来源”时才会打开对应网站。',
      },
      {
        q: '目前适合哪些科普场景？',
        a: '适合方剂通识课堂、家庭共读、中医药文化活动和公众自主学习。对外正式发布前，仍需完善专业内容审校、来源版本管理、隐私保护、无障碍与安全监测机制。',
      },
    ],
  },
]

const Help: React.FC = () => {
  const navigate = useNavigate()

  return (
    <div className="page-shell help-page">
      <div className="page-heading">
        <Button
          className="page-back-button"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/')}
        >
          返回首页
        </Button>
        <div className="page-eyebrow">
          <QuestionCircleOutlined />
          HELP CENTER
        </div>
        <h1 className="page-title">帮助中心</h1>
        <p className="page-description">
          了解方剂问答、学习任务、方剂拆解、中药图鉴、方药知识库、来源核验与内容评估，
          以及 AI 方剂通识科普版本的能力边界。
        </p>
      </div>

      <Alert
        className="help-demo-alert"
        type="info"
        showIcon
        message="这是面向公众的中医方剂通识科普平台"
        description="方剂 AI 问答由 DeepSeek 结合随项目提供的方剂与中药资料生成；登录、收藏和部分学习记录保存在当前浏览器本地。平台不提供诊断、处方或个体用药建议。"
      />

      <div className="help-category-grid">
        {faqData.map((item, index) => (
          <button
            type="button"
            className="help-category-card"
            key={item.category}
            onClick={() => {
              document.getElementById(`help-category-${index}`)?.scrollIntoView({
                behavior: 'smooth',
                block: 'start',
              })
            }}
          >
            <span className="help-category-icon">{item.icon}</span>
            <span>
              <strong>{item.category}</strong>
              <small>{item.questions.length} 个常见问题</small>
            </span>
          </button>
        ))}
      </div>

      <section className="help-faq-section">
        <div className="home-section-heading">
          <div>
            <span className="section-caption">常用说明</span>
            <h2>常见问题</h2>
          </div>
          <span className="eyebrow-chip">
            <SwapOutlined />
            AI 辅助学习
          </span>
        </div>
        {faqData.map((category, categoryIndex) => (
          <div
            key={category.category}
            id={`help-category-${categoryIndex}`}
            className="help-faq-group"
          >
            <div className="help-faq-heading">
              <span>{category.icon}</span>
              <h3>{category.category}</h3>
            </div>
            <Collapse
              bordered={false}
              items={category.questions.map((qa, questionIndex) => ({
                key: `${categoryIndex}-${questionIndex}`,
                label: <span className="help-question">{qa.q}</span>,
                children: <p className="help-answer">{qa.a}</p>,
              }))}
            />
          </div>
        ))}
      </section>

      <div className="help-footer-actions">
        <div>
          <strong>第一次使用知源？</strong>
          <span>从使用指南开始，选择一首方或一味药进入学习。</span>
        </div>
        <Button type="primary" onClick={() => navigate('/guide')}>
          打开使用指南
        </Button>
      </div>
    </div>
  )
}

export default Help
