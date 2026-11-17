import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  BulbOutlined,
  ClearOutlined,
  LoadingOutlined,
  RobotOutlined,
  SendOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { App as AntdApp, Avatar, Button, Input, Spin, Tag } from 'antd'
import {
  EDUCATION_NOTICE,
  HERBS,
  HOME_QUESTIONS,
  PRESCRIPTIONS,
  PRESCRIPTION_CATEGORIES,
  getArticleByName,
  getHerbsForPrescription,
  getPrescriptionsContainingHerb,
  type Herb,
  type Prescription,
} from '../data/scienceContent'
import { chatApi } from '../api/client'

const { TextArea } = Input
const CHAT_SESSION_KEY = 'zhiyuan-chat-session'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  loading?: boolean
}

const WELCOME_CONTENT = `你好，我是知源方剂科普助手。

我会结合平台整理的方剂与中药资料，由 DeepSeek 按“出处与类别、组成药味、传统功用与主治语境、配伍观察、安全边界”为你讲解。这里不进行疾病诊断，也不提供个体处方、剂量或自行用药建议。

你可以试试：四君子汤为什么由四味药组成？桂枝汤与麻黄汤有什么不同？君臣佐使如何帮助我们理解一首方？`

const createWelcome = (): Message => ({
  id: 'welcome',
  role: 'assistant',
  content: WELCOME_CONTENT,
  timestamp: Date.now(),
})

const getOrCreateSessionId = () => {
  try {
    const saved = localStorage.getItem(CHAT_SESSION_KEY)
    if (saved) return saved
    const next = `web-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
    localStorage.setItem(CHAT_SESSION_KEY, next)
    return next
  } catch {
    return `web-${Date.now()}`
  }
}

const findPrescriptionMentions = (question: string) =>
  PRESCRIPTIONS.filter((item) => question.includes(item.name)).sort(
    (a, b) => b.name.length - a.name.length,
  )

const findHerbMentions = (question: string) =>
  HERBS.filter((item) => question.includes(item.name)).sort(
    (a, b) => b.name.length - a.name.length,
  )

const prescriptionAnswer = (prescription: Prescription) => {
  const herbs = getHerbsForPrescription(prescription)
  const sameCategory = PRESCRIPTIONS.filter(
    (item) =>
      item.category === prescription.category &&
      item.id !== prescription.id,
  ).slice(0, 4)

  return `**${prescription.name} · 方剂档案**

类别：${prescription.category}
出处线索：《${prescription.source}》
组成：${prescription.herbs_raw}

**功用与主治**

传统功用表述为“${prescription.functions}”，传统主治表述为“${prescription.indications}”。这些术语来自中医辨证体系，不能直接对应某一个现代疾病名称。

**配伍观察**

方中共有 ${prescription.herb_names.length} 味药。可以先观察哪些药味围绕核心病机，哪些兼顾兼证，哪些用于制约偏性。关联中药包括：${herbs.slice(0, 8).map((herb) => herb.name).join('、')}${herbs.length > 8 ? '等' : ''}。

**同类方延伸**

${sameCategory.length ? `同属${prescription.category}的条目还有：${sameCategory.map((item) => item.name).join('、')}。可结合出处、组成和主治表述比较组方侧重点。` : '当前资料库中暂无可继续比较的同类别条目。'}

**安全边界**

${EDUCATION_NOTICE}

古籍剂量、现代教学剂量与实际临床用量不能直接等同。涉及毒性药、炮制、妊娠禁忌、十八反十九畏、儿童或慢病人群时，必须由中医师或药师判断，请勿照方自行抓药。`
}

const comparePrescriptions = (first: Prescription, second: Prescription) => {
  const shared = first.herb_names.filter((name) => second.herb_names.includes(name))
  const onlyFirst = first.herb_names.filter((name) => !second.herb_names.includes(name))
  const onlySecond = second.herb_names.filter((name) => !first.herb_names.includes(name))

  return `**${first.name} 与 ${second.name}：比较阅读**

类别：${first.category} / ${second.category}
出处：《${first.source}》 / 《${second.source}》
药味数：${first.herb_names.length} 味 / ${second.herb_names.length} 味

**功用与主治**

- ${first.name}：${first.functions}；传统主治为${first.indications}。
- ${second.name}：${second.functions}；传统主治为${second.indications}。

**共同药味**

${shared.length ? shared.join('、') : '当前资料中未记录共同药味。'}

**各自特有药味**

- ${first.name}：${onlyFirst.length ? onlyFirst.join('、') : '无'}
- ${second.name}：${onlySecond.length ? onlySecond.join('、') : '无'}

**怎样理解差异**

比较方剂不能只看“功效关键词”是否相似，还要回到证候语境、药物分工、剂量比例和炮制要求。两首方即使共享药味，也可能因主次与配伍不同而形成不同思路。

${EDUCATION_NOTICE}`
}

const herbAnswer = (herb: Herb) => {
  const related = getPrescriptionsContainingHerb(herb.name).slice(0, 8)

  return `**${herb.name} · 中药档案**

性味：${herb.property}
归经：${herb.meridian}
拼音：${herb.pinyin}

**功能与主治**

资料记载功能为“${herb.functions}”，传统主治表述为“${herb.indications}”。

**用法与注意**

资料参考用量为${herb.dosage}。使用注意：${herb.precautions}。
实际用量、炮制、配伍与疗程必须由专业人员判断，不能把资料中的参考用量直接当作自行用药方案。

**含此药的方剂**

${related.length ? related.map((item) => `${item.name}（${item.category}）`).join('、') : '当前方剂资料中暂未检索到明确关联。'}

**现代研究提示**

${herb.modernResearch}

现代研究通常针对特定成分、提取物或实验条件，不能直接推导为日常自行使用中药的依据。中药图片仅用于学习辨识，不能用于真伪鉴定、品质判断或采购决策。`
}

const categoryAnswer = (categoryName: string) => {
  const category = PRESCRIPTION_CATEGORIES.find((item) => item.name === categoryName)
  if (!category) return ''
  const formulas = PRESCRIPTIONS.filter((item) => item.category === category.name)

  return `**${category.name} · 学习导览**

${category.description}

**收录情况**

当前资料库收录 ${formulas.length} 首${category.name}方剂，包括：${formulas.slice(0, 8).map((item) => item.name).join('、')}${formulas.length > 8 ? '等' : ''}。

**建议的读方顺序**

1. 先确认方剂类别与出处。
2. 再梳理组成药味和药味数量。
3. 对照功用、主治的传统表述理解配伍重点。
4. 与同类别方剂比较，找出共同药味和关键差异。

${EDUCATION_NOTICE}`
}

const buildAnswer = (question: string) => {
  const trimmed = question.trim()
  const prescriptionMentions = findPrescriptionMentions(trimmed)
  const herbMentions = findHerbMentions(trimmed)
  const categoryMention = PRESCRIPTION_CATEGORIES.find((item) => trimmed.includes(item.name))

  if (prescriptionMentions.length >= 2) {
    return comparePrescriptions(prescriptionMentions[0], prescriptionMentions[1])
  }
  if (prescriptionMentions.length === 1) {
    return prescriptionAnswer(prescriptionMentions[0])
  }
  if (herbMentions.length >= 1) {
    return herbAnswer(herbMentions[0])
  }

  const article = getArticleByName(trimmed)
  if (article?.prescription) return prescriptionAnswer(article.prescription)
  if (article?.herb) return herbAnswer(article.herb)
  if (categoryMention) return categoryAnswer(categoryMention.name)

  if (/君臣佐使|配伍|组方|方解/.test(trimmed)) {
    return `**把一首方当作一个协作结构来读**

“君臣佐使”是传统方剂配伍的分析框架，用来说明不同药味在方中的主次与分工。学习时可以从四个问题入手：

1. 哪味药最贴近方剂的核心病机？
2. 哪些药味帮助增强主要方向？
3. 哪些药味兼顾兼证、制约偏性或调和药性？
4. 药味之间的关系，如何共同形成这首方的特点？

**重要提醒**

不同教材、版本与医家对具体方剂君臣佐使的标注可能存在差异。它是理解配伍的学习工具，不是可以脱离证候语境机械套用的公式。

${EDUCATION_NOTICE}`
  }

  if (/辨证|千人一方|对症|是否适合|能不能吃/.test(trimmed)) {
    return `**方剂强调辨证使用**

中医方剂不是按一个现代病名直接“对号入座”。传统上需要综合证候、体质、病程、兼证、年龄、妊娠状态、正在使用的药物与炮制要求等因素。

同一首方在不同人、不同阶段是否适合，不能仅凭症状名称或网络问答判断。尤其不能把“别人吃了有效”的方照搬给自己。

${EDUCATION_NOTICE}`
  }

  if (/剂量|几克|多少克|抓药|自己煮|自制|服用|吃多久/.test(trimmed)) {
    return `**古籍剂量不能直接照搬**

古籍中的度量衡、炮制方法、药材品种和煎服方式与今天并不完全相同。网页中的“参考用量”也只适合作为资料阅读，不能替代辨证、处方和药师审核。

**平台不会提供**

- 针对个人的药物剂量
- 自行抓药或煎服方案
- 用方剂替代医生诊疗的建议
- 针对儿童、孕妇、哺乳期或慢病人群的个体处方

如果你正在考虑使用中药，请携带具体药物与处方信息咨询中医师或药师，并说明正在使用的其他药物。

${EDUCATION_NOTICE}`
  }

  if (/性味归经|四气五味|归经/.test(trimmed)) {
    return `**性味归经是什么**

性味归经是传统中药理论描述药性的一种语言。四气通常指寒、热、温、凉；五味包括辛、甘、酸、苦、咸等；归经用于表达药物作用与脏腑经络之间的传统关联。

**应该怎样学**

不要把性味归经当成孤立的标签，需要与具体功效、主治、炮制、配伍和禁忌一起理解。同一味药在不同方剂中的角色也可能不同。

可以进入“方剂与中药知识库”，搜索具体中药查看资料，再查看含该药的方剂。

${EDUCATION_NOTICE}`
  }

  if (/十八反|十九畏|妊娠|孕妇|毒性|副作用|安全/.test(trimmed)) {
    return `**方剂学习中的安全边界**

中药并非“天然就等于安全”。需要关注药物品种、炮制、剂量、配伍禁忌、妊娠用药、肝肾功能、儿童与老年人群，以及与其他药物的相互作用。

十八反、十九畏、妊娠禁忌和毒性药管理都属于专业用药范畴。平台可用于理解概念与查找线索，但不会提供自行配伍、加减或服用方案。

${EDUCATION_NOTICE}`
  }

  return `**这个问题可以怎样继续查**

当前本地知识库没有直接匹配到“${trimmed}”。你可以改用具体的方名或药名继续检索，例如“四君子汤”“桂枝汤”“当归”“茯苓”，也可以从十五类方剂中按主题进入。

**推荐的学习路径**

1. 在“方剂与中药知识库”查找具体条目。
2. 在“方剂拆解实验室”查看组成与关联药味。
3. 在“方剂关联推荐”比较同类别方剂。
4. 在“中医药权威来源”核对教材、药典与机构资料。

${EDUCATION_NOTICE}`
}

const formatContent = (content: string) =>
  content.split('\n').map((line, index) => {
    const isBullet = line.startsWith('- ') || /^\d+\.\s/.test(line)
    const parts = line.split(/(\*\*.*?\*\*)/g)
    return (
      <div key={`${line}-${index}`} className={isBullet ? 'chat-bullet' : 'chat-line'}>
        {parts.map((part, partIndex) =>
          part.startsWith('**') && part.endsWith('**') ? (
            <strong key={partIndex}>{part.slice(2, -2)}</strong>
          ) : (
            <span key={partIndex}>{part}</span>
          ),
        )}
      </div>
    )
  })

const PrescriptionAnalysis: React.FC = () => {
  const { message } = AntdApp.useApp()
  const [params] = useSearchParams()
  const initialQuestion = params.get('q') || ''
  const [messages, setMessages] = useState<Message[]>([createWelcome()])
  const [inputText, setInputText] = useState(initialQuestion)
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId] = useState(getOrCreateSessionId)
  const endRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<any>(null)

  useEffect(() => {
    if (initialQuestion) {
      setInputText(initialQuestion)
      window.setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [initialQuestion])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages])

  const send = async () => {
    const content = inputText.trim()
    if (!content || isLoading) return
    const history = messages
      .filter((item) => item.id !== 'welcome' && !item.loading)
      .slice(-12)
      .map((item) => ({ role: item.role, content: item.content }))
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: Date.now(),
    }
    const loadingMessage: Message = {
      id: `loading-${Date.now()}`,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      loading: true,
    }
    setMessages((current) => [...current, userMessage, loadingMessage])
    setInputText('')
    setIsLoading(true)

    try {
      const result = await chatApi.analyze({
        message: content,
        sessionId,
        history,
      })
      if (!result.response?.trim()) throw new Error('AI 返回了空内容')
      setMessages((current) => [
        ...current.filter((item) => item.id !== loadingMessage.id),
        {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: result.response,
          timestamp: Date.now(),
        },
      ])
    } catch {
      setMessages((current) => [
        ...current.filter((item) => item.id !== loadingMessage.id),
        {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: `**DeepSeek 暂时不可用**\n\n当前先使用平台本地资料回答；检查后端服务和 API Key 后可重试。\n\n${buildAnswer(content)}`,
          timestamp: Date.now(),
        },
      ])
      message.warning('DeepSeek 暂时不可用，已切换为本地资料回答')
    } finally {
      setIsLoading(false)
      window.setTimeout(() => inputRef.current?.focus(), 80)
    }
  }

  const clear = () => {
    setMessages([createWelcome()])
    void chatApi.clearHistory(sessionId).catch(() => undefined)
    message.success('对话已清空')
  }

  return (
    <div className="page-shell chat-page">
      <div className="chat-shell">
        <div className="chat-toolbar">
          <div className="chat-heading">
            <span className="chat-robot-mark"><RobotOutlined /></span>
            <div>
              <h1>方剂 AI 问答</h1>
              <p>查方剂出处、组成、功用、主治、关联中药与安全边界</p>
            </div>
          </div>
          <div className="chat-toolbar-actions">
            <Tag color="success">DeepSeek · 方剂通识</Tag>
            <Button icon={<ClearOutlined />} onClick={clear} disabled={messages.length <= 1}>
              清空
            </Button>
          </div>
        </div>

        <div className="chat-messages">
          <div className="chat-messages-inner">
            {messages.map((msg) => (
              <div className={`chat-message ${msg.role}`} key={msg.id}>
                {msg.role === 'assistant' && (
                  <Avatar size={38} icon={<RobotOutlined />} className="assistant-avatar" />
                )}
                <div className="chat-bubble">
                  {msg.loading ? (
                    <div className="chat-loading">
                      <Spin indicator={<LoadingOutlined spin />} />
                      <span>AI 正在结合方剂资料整理回答…</span>
                    </div>
                  ) : (
                    formatContent(msg.content)
                  )}
                </div>
                {msg.role === 'user' && (
                  <Avatar size={38} icon={<UserOutlined />} className="user-avatar" />
                )}
              </div>
            ))}
            <div ref={endRef} />
          </div>
        </div>

        <div className="chat-composer">
          <div className="chat-composer-inner">
            {messages.length <= 1 && (
              <div className="chat-examples">
                <span><BulbOutlined /> 试试这些问题</span>
                <div>
                  {HOME_QUESTIONS.slice(0, 4).map((item) => (
                    <button type="button" key={item} onClick={() => setInputText(item)}>
                      {item}
                    </button>
                  ))}
                </div>
              </div>
            )}
            <div className="composer-row">
              <TextArea
                ref={inputRef}
                value={inputText}
                onChange={(event) => setInputText(event.target.value)}
                onPressEnter={(event) => {
                  if (!event.shiftKey) {
                    event.preventDefault()
                    send()
                  }
                }}
                autoSize={{ minRows: 1, maxRows: 4 }}
                placeholder="输入方名、药名或方剂学习问题…（Shift + Enter 换行）"
                disabled={isLoading}
              />
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={send}
                loading={isLoading}
                disabled={!inputText.trim() || isLoading}
                aria-label="发送问题"
              />
            </div>
            <p className="chat-disclaimer">
              {EDUCATION_NOTICE} 古籍剂量仅作历史资料说明，请勿据此自行抓药。
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PrescriptionAnalysis
