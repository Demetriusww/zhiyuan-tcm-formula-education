import prescriptionData from './prescriptions_all.json'
import herbData from './herbs_all.json'

export interface Prescription {
  id: number
  name: string
  source: string
  functions: string
  indications: string
  category: string
  herbs_raw: string
  herb_names: string[]
}

export interface Herb {
  name: string
  pinyin: string
  latin: string
  property: string
  meridian: string
  functions: string
  indications: string
  dosage: string
  precautions: string
  modernResearch: string
  description: string
}

export type LearningLevel = '入门' | '进阶'

export interface ScienceTopic {
  id: string
  name: string
  category: string
  summary: string
  description: string
  accent: string
  dimensions: {
    fundamentals: number
    application: number
    impact: number
    accessibility: number
    practice: number
    frontier: number
  }
}

export interface PrescriptionCategory extends ScienceTopic {
  count: number
  examples: string[]
}

export interface KnowledgeSection {
  label: string
  content: string
}

export interface KnowledgeArticle {
  id: string
  categoryId: string
  category: string
  group: string
  title: string
  keyword: string
  summary: string
  content: string
  sections?: KnowledgeSection[]
  evidence: string[]
  source: string
  tags: string[]
  readTime: number
  level: LearningLevel
  updatedAt: string
  prescription?: Prescription
  herb?: Herb
  imageUrl?: string
  imageAvailable?: boolean
}

export interface ScienceResource {
  id: number
  title: string
  topic: string
  format: '互动课程' | '图文长读' | '互动工具' | '学习任务' | '图鉴卡片'
  audience: string
  difficulty: LearningLevel
  source: string
  duration: string
  updatedAt: string
  summary: string
  url: string
}

export interface AuthoritySource {
  id: number
  name: string
  shortName: string
  category: string
  region: string
  description: string
  focus: string[]
  url: string
  verifiedAt: string
  accent: string
}

export const PRESCRIPTIONS = prescriptionData.prescriptions as Prescription[]

const herbRecord = herbData.herbs as Record<string, Herb>
export const HERBS = Object.values(herbRecord)

export const EDUCATION_NOTICE =
  '平台内容用于方剂通识教育、文化理解与知识查询，不提供个体诊断、处方或自行用药建议。'

export const PRESCRIPTION_CATEGORIES: PrescriptionCategory[] = [
  {
    id: 'tonifying',
    name: '补益剂',
    category: '补益类方剂',
    summary: '从补气、补血、补阴、补阳理解扶助正气的配伍思路。',
    description:
      '补益剂常用于传统理论中的气血阴阳不足。学习时应先看虚在何处、兼有何证，再看补益药如何与健脾、理气、渗湿等药味配合。代表方有四君子汤、四物汤和六味地黄丸。',
    accent: '#0B6E69',
    count: 26,
    examples: ['四君子汤', '四物汤', '六味地黄丸'],
    dimensions: { fundamentals: 75, application: 78, impact: 88, accessibility: 86, practice: 92, frontier: 94 },
  },
  {
    id: 'exterior',
    name: '解表剂',
    category: '解表类方剂',
    summary: '认识辛温解表与辛凉解表的组方差异。',
    description:
      '解表剂围绕外感表证展开，常以发散药为主，并根据寒热、汗出、兼夹证进行配伍。桂枝汤、麻黄汤与银翘散适合用来比较不同解表路径。',
    accent: '#B85C3E',
    count: 16,
    examples: ['桂枝汤', '麻黄汤', '银翘散'],
    dimensions: { fundamentals: 88, application: 90, impact: 86, accessibility: 82, practice: 88, frontier: 86 },
  },
  {
    id: 'harmonizing',
    name: '和解剂',
    category: '和解类方剂',
    summary: '理解表里、寒热、虚实之间的协调与转枢。',
    description:
      '和解剂常用于传统理论中的少阳证、肝脾不和或寒热错杂。小柴胡汤、逍遥散与半夏泻心汤展示了调和、疏解与寒热并用的不同方式。',
    accent: '#8C6A31',
    count: 7,
    examples: ['小柴胡汤', '逍遥散', '半夏泻心汤'],
    dimensions: { fundamentals: 87, application: 82, impact: 90, accessibility: 78, practice: 84, frontier: 89 },
  },
  {
    id: 'warming',
    name: '温里剂',
    category: '温里类方剂',
    summary: '从温中散寒、回阳救逆理解温法与药味配伍。',
    description:
      '温里剂以温热药味为主体，常用于传统理论中的里寒证。理中丸、四逆汤与吴茱萸汤可帮助观察温中、回阳与降逆等不同配伍重点。',
    accent: '#A66A2B',
    count: 8,
    examples: ['理中丸', '四逆汤', '吴茱萸汤'],
    dimensions: { fundamentals: 82, application: 85, impact: 84, accessibility: 76, practice: 78, frontier: 82 },
  },
  {
    id: 'heat-clearing',
    name: '清热剂',
    category: '清热类方剂',
    summary: '比较清气、凉血、解毒与清脏腑之热的配伍层次。',
    description:
      '清热剂覆盖气分热、血分热、湿热与脏腑热等不同学习场景。白虎汤、黄连解毒汤和龙胆泻肝汤可以帮助理解热邪部位与药味选择之间的关系。',
    accent: '#3B7F89',
    count: 16,
    examples: ['白虎汤', '黄连解毒汤', '龙胆泻肝汤'],
    dimensions: { fundamentals: 88, application: 90, impact: 86, accessibility: 75, practice: 82, frontier: 88 },
  },
  {
    id: 'purging',
    name: '泻下剂',
    category: '泻下类方剂',
    summary: '认识寒下、温下、润下与攻补兼施的差异。',
    description:
      '泻下剂是方剂学习中安全边界尤其重要的一类。大承气汤、温脾汤与麻子仁丸展示了攻下、温下和润下的不同思路，实际使用必须由专业人员判断。',
    accent: '#60706E',
    count: 6,
    examples: ['大承气汤', '温脾汤', '麻子仁丸'],
    dimensions: { fundamentals: 76, application: 82, impact: 80, accessibility: 70, practice: 68, frontier: 78 },
  },
  {
    id: 'phlegm',
    name: '祛痰剂',
    category: '祛痰类方剂',
    summary: '从燥湿、清热、润燥与化痰止咳理解配伍。',
    description:
      '祛痰剂涉及湿痰、热痰、燥痰和风痰等不同传统分类。二陈汤、温胆汤与清气化痰丸可用于比较痰的性质、病位和兼证如何影响组方。',
    accent: '#447A68',
    count: 6,
    examples: ['二陈汤', '温胆汤', '清气化痰丸'],
    dimensions: { fundamentals: 70, application: 74, impact: 76, accessibility: 72, practice: 78, frontier: 80 },
  },
  {
    id: 'dampness',
    name: '祛湿剂',
    category: '祛湿类方剂',
    summary: '理解化湿、燥湿、利水与健脾之间的关系。',
    description:
      '祛湿剂把水湿停聚与脾胃运化、三焦水道联系起来。五苓散、平胃散和茵陈蒿汤分别呈现利水、燥湿与清利湿热的典型思路。',
    accent: '#2F7E88',
    count: 11,
    examples: ['五苓散', '平胃散', '茵陈蒿汤'],
    dimensions: { fundamentals: 78, application: 80, impact: 78, accessibility: 74, practice: 76, frontier: 82 },
  },
  {
    id: 'blood',
    name: '理血剂',
    category: '理血类方剂',
    summary: '从活血化瘀与止血的配伍中理解气血关系。',
    description:
      '理血剂关注血液运行与出血问题，但传统“活血”不等同于现代某一项药理作用。血府逐瘀汤、补阳还五汤与桂枝茯苓丸适合比较组方侧重点。',
    accent: '#8F4A57',
    count: 6,
    examples: ['血府逐瘀汤', '补阳还五汤', '桂枝茯苓丸'],
    dimensions: { fundamentals: 84, application: 84, impact: 86, accessibility: 76, practice: 82, frontier: 88 },
  },
  {
    id: 'calming',
    name: '安神剂',
    category: '安神类方剂',
    summary: '认识重镇安神、养心安神与交通心肾的思路。',
    description:
      '安神剂围绕传统理论中的心神不宁展开。天王补心丹、酸枣仁汤与朱砂安神丸可用于理解滋养、重镇和清心等不同配伍方式。',
    accent: '#5E6F91',
    count: 5,
    examples: ['天王补心丹', '酸枣仁汤', '朱砂安神丸'],
    dimensions: { fundamentals: 76, application: 80, impact: 82, accessibility: 70, practice: 80, frontier: 78 },
  },
  {
    id: 'digestion',
    name: '消食剂',
    category: '消食类方剂',
    summary: '从食积停滞理解消食导滞与健脾和胃的配合。',
    description:
      '消食剂多以消食药与理气、和胃药同用。保和丸和枳实导滞丸适合用来观察单纯食积与食积兼湿热时，组方重点如何变化。',
    accent: '#B48725',
    count: 2,
    examples: ['保和丸', '枳实导滞丸'],
    dimensions: { fundamentals: 68, application: 72, impact: 66, accessibility: 62, practice: 86, frontier: 74 },
  },
  {
    id: 'qi-regulating',
    name: '理气剂',
    category: '理气类方剂',
    summary: '理解行气、降逆、疏肝与和胃的配伍关系。',
    description:
      '理气剂围绕气机不畅的传统认识展开。越鞠丸、半夏厚朴汤与柴胡疏肝散可以帮助比较行气解郁、降逆化痰与疏肝理气的不同路径。',
    accent: '#766A3E',
    count: 4,
    examples: ['越鞠丸', '半夏厚朴汤', '柴胡疏肝散'],
    dimensions: { fundamentals: 78, application: 80, impact: 82, accessibility: 70, practice: 76, frontier: 84 },
  },
  {
    id: 'astringent',
    name: '固涩剂',
    category: '固涩类方剂',
    summary: '理解固表、涩肠、固精与止遗的传统用药思路。',
    description:
      '固涩剂用于传统理论中的正气耗散、滑脱不禁等情况。牡蛎散与四神丸展示了固表止汗、涩肠止泻等不同侧重，学习时应特别注意邪气未尽时不宜盲目固涩。',
    accent: '#6C6950',
    count: 2,
    examples: ['牡蛎散', '四神丸'],
    dimensions: { fundamentals: 62, application: 68, impact: 72, accessibility: 56, practice: 68, frontier: 66 },
  },
  {
    id: 'wind',
    name: '治风剂',
    category: '治风类方剂',
    summary: '区分外风与内风，理解疏散、息风与扶正的配合。',
    description:
      '治风剂涉及传统理论中的外风、内风与风痰等概念。半夏白术天麻汤与桂枝芍药知母汤可用于观察化痰息风、通阳和营等不同组方方法。',
    accent: '#73808A',
    count: 2,
    examples: ['半夏白术天麻汤', '桂枝芍药知母汤'],
    dimensions: { fundamentals: 66, application: 72, impact: 68, accessibility: 58, practice: 70, frontier: 72 },
  },
  {
    id: 'summerheat',
    name: '祛暑剂',
    category: '祛暑类方剂',
    summary: '从暑邪特点理解清暑、益气与利湿的配伍。',
    description:
      '祛暑剂围绕暑热、暑湿与气津耗伤展开。六一散是认识清暑利湿思路的基础入口，学习时应结合季节、环境和兼证理解，不把通识知识当作中暑处置方案。',
    accent: '#8A6D36',
    count: 1,
    examples: ['六一散'],
    dimensions: { fundamentals: 58, application: 64, impact: 60, accessibility: 48, practice: 74, frontier: 64 },
  },
]

export const SCIENCE_TOPICS: PrescriptionCategory[] = PRESCRIPTION_CATEGORIES

const CATEGORY_ID_BY_NAME = new Map(PRESCRIPTION_CATEGORIES.map((item) => [item.name, item.id]))
const CATEGORY_BY_ID = new Map(PRESCRIPTION_CATEGORIES.map((item) => [item.id, item]))

const HERB_IMAGE_STEMS = new Set([
  'baishao',
  'baizhu',
  'baiziren',
  'banlangen',
  'banxia',
  'beishashen',
  'bohe',
  'chenpi',
  'chenxiang',
  'chuanbeimu',
  'chuanxiong',
  'danggui',
  'danshen',
  'fangfeng',
  'fuling',
  'gancao',
  'gualou',
  'guizhi',
  'honghua',
  'huangbo',
  'huanglian',
  'huangqi',
  'huangqin',
  'jingjie',
  'jinqiancao',
  'jinyinhua',
  'juhua',
  'lianqiao',
  'longgu',
  'mahuang',
  'maidong',
  'muli',
  'muxiang',
  'niubangzi',
  'renshen',
  'sangye',
  'shengjiang',
  'shigao',
  'shihu',
  'shudihuang',
  'suanzaoren',
  'taoren',
  'tiannanxing',
  'xiangfu',
  'yinchen',
  'yiyiren',
  'yujin',
  'zexie',
  'zhimu',
  'zhishi',
  'zhizi',
  'zisu',
])

export const HERB_IMAGE_COUNT = HERB_IMAGE_STEMS.size

const herbImageStem = (herb: Herb) => herb.pinyin.toLowerCase().replace(/\s+/g, '')

export const hasHerbImage = (herb: Herb) => HERB_IMAGE_STEMS.has(herbImageStem(herb))

export const getHerbImageUrl = (herb: Herb) =>
  `/images/herbs/${herbImageStem(herb)}.jpg`

export const getHerbByName = (name: string) =>
  herbRecord[name] ||
  HERBS.find(
    (herb) =>
      herb.name === name ||
      herb.pinyin.toLowerCase() === name.toLowerCase() ||
      herb.latin.toLowerCase() === name.toLowerCase(),
  )

export const getPrescriptionByName = (name: string) =>
  PRESCRIPTIONS.find(
    (prescription) =>
      prescription.name === name ||
      String(prescription.id) === name ||
      `prescription-${prescription.id}` === name,
  )

export const getPrescriptionsByCategory = (category: string) =>
  PRESCRIPTIONS.filter((prescription) => prescription.category === category)

export const getHerbsForPrescription = (prescription: Prescription) =>
  prescription.herb_names
    .map((name) => getHerbByName(name))
    .filter((herb): herb is Herb => Boolean(herb))

export const getPrescriptionsContainingHerb = (herbName: string) =>
  PRESCRIPTIONS.filter((prescription) => prescription.herb_names.includes(herbName))

const herbFunctionGroup = (functions: string) => {
  if (/解表|发汗|疏散|解肌/.test(functions)) return '解表药'
  if (/清热|泻火|解毒|凉血|清暑/.test(functions)) return '清热药'
  if (/补气|补血|补阴|补阳|益气|养血|滋阴|温阳|健脾|补肾/.test(functions)) return '补益药'
  if (/化痰|止咳|平喘|润肺|消痰/.test(functions)) return '化痰止咳平喘药'
  if (/活血|化瘀|止血|通经/.test(functions)) return '活血化瘀药'
  if (/利水|渗湿|化湿|祛湿|利湿|燥湿/.test(functions)) return '祛湿药'
  if (/理气|行气|疏肝|降逆|解郁/.test(functions)) return '理气药'
  if (/安神|宁心|养心/.test(functions)) return '安神药'
  if (/收涩|固表|涩肠|止遗|固精/.test(functions)) return '收涩药'
  return '其他常用中药'
}

const prescriptionArticle = (prescription: Prescription): KnowledgeArticle => {
  const herbs = getHerbsForPrescription(prescription)
  const categoryId = CATEGORY_ID_BY_NAME.get(prescription.category) || 'prescription-basics'
  const safetyEvidence = [
    '组成、功用与主治为传统方剂知识的学习性整理，不能替代辨证与个体诊疗。',
    '古籍剂量、现代教学剂量与实际临床用量不能直接等同，请勿据此自行抓药。',
    '涉及毒性药、炮制、妊娠禁忌、十八反十九畏或特殊人群时，必须咨询中医师或药师。',
  ]

  return {
    id: `prescription-${prescription.id}`,
    categoryId,
    category: prescription.category,
    group: prescription.source,
    title: prescription.name,
    keyword: prescription.name,
    summary: `出自《${prescription.source}》。功用为${prescription.functions}，传统主治表述为${prescription.indications}。`,
    content: `${prescription.name}是${prescription.category}中的学习条目。原资料记载其功用为“${prescription.functions}”，主治表述为“${prescription.indications}”。学习一首方，不宜只记住功效标签，还要回到组成、出处、证候语境和药物之间的配合关系。`,
    sections: [
      {
        label: '出处与源流',
        content: `本方资料标注出自《${prescription.source}》。阅读古籍方名时，可进一步核对版本、原文与后世方书之间的差异，不把现代简化表述直接等同于古籍原文。`,
      },
      {
        label: '组成与药味',
        content: `教材式组成记录为：${prescription.herbs_raw}。共 ${prescription.herb_names.length} 味药，可结合药味关联继续查看每味中药的性味、归经、功用和使用注意。`,
      },
      {
        label: '功用与主治',
        content: `传统功用表述为“${prescription.functions}”，传统主治表述为“${prescription.indications}”。这些术语来自中医辨证体系，需要结合具体语境理解，不能直接对应现代疾病名称或个体治疗方案。`,
      },
      {
        label: '怎样理解配伍',
        content: `可以先观察主药与辅助药的分工：哪些药味针对核心病机，哪些药味兼顾兼证，哪些药味用于制约偏性。再把${herbs.slice(0, 4).map((herb) => herb.name).join('、')}等药味放回全方结构，而不是孤立记忆单味药功效。`,
      },
      {
        label: '安全边界',
        content: `${EDUCATION_NOTICE} 方中药物是否适合某个人，需要由专业人员结合体质、病程、兼病、正在使用的药物和特殊生理状态判断。`,
      },
    ],
    evidence: [
      `出处：${prescription.source}。`,
      `组成：${prescription.herbs_raw}。`,
      `功用：${prescription.functions}；主治：${prescription.indications}。`,
      ...safetyEvidence,
    ],
    source: `项目内置方剂资料 · 《${prescription.source}》出处线索`,
    tags: [prescription.category, prescription.functions, ...prescription.herb_names.slice(0, 4)],
    readTime: 3 + Math.ceil(prescription.herb_names.length / 2),
    level: prescription.herb_names.length >= 7 ? '进阶' : '入门',
    updatedAt: '2026-11-15',
    prescription,
  }
}

const herbArticle = (herb: Herb): KnowledgeArticle => {
  const imageAvailable = hasHerbImage(herb)

  return {
    id: `herb-${herb.name}`,
    categoryId: 'herb-atlas',
    category: '中药图鉴',
    group: herbFunctionGroup(herb.functions),
    title: herb.name,
    keyword: `${herb.name} ${herb.pinyin} ${herb.latin}`,
    summary: `${herb.property}，${herb.meridian}。功能为${herb.functions}。`,
    content: herb.description,
    sections: [
      {
        label: '性味归经',
        content: `${herb.property}；${herb.meridian}。性味归经是传统药性理论的表达方式，学习时应与功效、主治和禁忌一起理解。`,
      },
      {
        label: '功能与主治',
        content: `资料记载功能为“${herb.functions}”，传统主治表述为“${herb.indications}”。这些内容用于通识学习，不对应现代疾病诊断或个体用药建议。`,
      },
      {
        label: '用法与注意',
        content: `资料参考用量为${herb.dosage}。注意：${herb.precautions}。实际用量、炮制、配伍和疗程需由专业人员判断。`,
      },
      {
        label: '现代研究提示',
        content: `${herb.modernResearch}。现代研究结果通常针对提取物、成分或特定实验条件，不能直接推导为日常自行使用中药的依据。`,
      },
      {
        label: '图片使用边界',
        content: imageAvailable
          ? '本页图片用于中药通识辨识和学习展示，不能作为真伪鉴定、品质判断、采购或用药依据。'
          : '当前项目尚无该药的本地图片，页面以文字图鉴展示。缺少图片不代表该药不重要，也不能据此推断药材特征。',
      },
    ],
    evidence: [
      `性味：${herb.property}；归经：${herb.meridian}。`,
      `功能：${herb.functions}。`,
      `传统主治：${herb.indications}。`,
      `资料参考用量：${herb.dosage}。`,
      `使用注意：${herb.precautions}。`,
      '图片仅用于学习辨识，不能用于真伪鉴定、品质判断或实际用药决策。',
    ],
    source: '项目内置中药资料 · 建议结合《中华人民共和国药典》与专业教材核验',
    tags: [herbFunctionGroup(herb.functions), herb.property, herb.meridian],
    readTime: 3,
    level: '入门',
    updatedAt: '2026-11-15',
    herb,
    imageUrl: getHerbImageUrl(herb),
    imageAvailable,
  }
}

export const KNOWLEDGE_ARTICLES: KnowledgeArticle[] = [
  ...PRESCRIPTIONS.map(prescriptionArticle),
  ...HERBS.map(herbArticle),
]

export const SCIENCE_RESOURCES: ScienceResource[] = [
  {
    id: 1,
    title: '四君子汤：四味药如何组成补气基础方',
    topic: '补益剂',
    format: '图文长读',
    audience: '普通公众与初学者',
    difficulty: '入门',
    source: '方剂与中药知识库',
    duration: '8 分钟',
    updatedAt: '2026-11-15',
    summary: '从出处、组成、功用和配伍关系理解经典补气方。',
    url: '/herbs?name=四君子汤',
  },
  {
    id: 2,
    title: '桂枝汤与麻黄汤：同为解表，配伍为何不同',
    topic: '解表剂',
    format: '互动工具',
    audience: '中医药文化学习者',
    difficulty: '进阶',
    source: '方剂拆解实验室',
    duration: '12 分钟',
    updatedAt: '2026-11-14',
    summary: '并排观察组成、药味侧重与适用证候的传统表述。',
    url: '/efficacy?prescription=桂枝汤',
  },
  {
    id: 3,
    title: '从君臣佐使拆解一首方',
    topic: '方剂通识',
    format: '互动课程',
    audience: '普通公众与学生',
    difficulty: '入门',
    source: '方剂 AI 问答',
    duration: '10 分钟',
    updatedAt: '2026-11-13',
    summary: '用层次化问题理解组方角色，而不是孤立背诵药味。',
    url: '/analysis?q=君臣佐使如何帮助我们理解一首方？',
  },
  {
    id: 4,
    title: '中药图鉴观察与辨识',
    topic: '中药图鉴',
    format: '互动工具',
    audience: '公众与课堂',
    difficulty: '入门',
    source: '中药图鉴辨识',
    duration: '6 分钟',
    updatedAt: '2026-11-12',
    summary: '从图片外观、性味归经、关联方剂和来源核验四个角度建立学习性辨识。',
    url: '/recognize',
  },
  {
    id: 5,
    title: '三分钟读懂一首经典名方',
    topic: '方剂通识',
    format: '学习任务',
    audience: '家庭与课堂',
    difficulty: '入门',
    source: '方剂学习任务',
    duration: '20 分钟',
    updatedAt: '2026-11-11',
    summary: '按出处、组成、功用、主治和配伍生成学习卡。',
    url: '/smart',
  },
  {
    id: 6,
    title: '方剂类别与药味关联图谱',
    topic: '方剂通识',
    format: '互动工具',
    audience: '公众与内容策划者',
    difficulty: '进阶',
    source: '方剂知识图谱',
    duration: '自主探索',
    updatedAt: '2026-11-10',
    summary: '从类别进入代表方，再查看组成中药与知识条目。',
    url: '/visualization',
  },
  {
    id: 7,
    title: '如何把方剂知识讲给公众',
    topic: '方剂通识',
    format: '互动课程',
    audience: '科普创作者与教师',
    difficulty: '入门',
    source: '方剂科普创作工坊',
    duration: '15 分钟',
    updatedAt: '2026-11-09',
    summary: '围绕源流、组成、配伍与安全边界组织通俗解释。',
    url: '/optimization',
  },
  {
    id: 8,
    title: '方剂科普内容风险自查',
    topic: '方剂通识',
    format: '互动工具',
    audience: '内容创作者',
    difficulty: '入门',
    source: '方剂科普内容评估',
    duration: '8 分钟',
    updatedAt: '2026-11-08',
    summary: '识别夸大疗效、千人一方和缺少安全边界的表达。',
    url: '/comparison',
  },
  {
    id: 9,
    title: '中药图片能用来鉴定药材吗',
    topic: '中药图鉴',
    format: '图文长读',
    audience: '普通公众',
    difficulty: '入门',
    source: '中药图鉴辨识',
    duration: '5 分钟',
    updatedAt: '2026-11-07',
    summary: '理解图片学习、真伪鉴定和品质判断之间的边界。',
    url: '/recognize',
  },
  {
    id: 10,
    title: '十五类方剂快速导览',
    topic: '方剂通识',
    format: '图文长读',
    audience: '方剂初学者',
    difficulty: '入门',
    source: '方剂关联推荐',
    duration: '12 分钟',
    updatedAt: '2026-11-06',
    summary: '按补益、解表、清热、祛湿等类别建立学习地图。',
    url: '/similarity?topic=补益剂',
  },
  {
    id: 11,
    title: '中医药权威来源核验清单',
    topic: '方剂通识',
    format: '图文长读',
    audience: '教师、家长与创作者',
    difficulty: '进阶',
    source: '权威来源检索',
    duration: '9 分钟',
    updatedAt: '2026-11-05',
    summary: '核对发布机构、古籍版本、标准文件与专业适用范围。',
    url: '/evidence',
  },
  {
    id: 12,
    title: '方剂学习六步法',
    topic: '方剂通识',
    format: '学习任务',
    audience: '所有学习者',
    difficulty: '入门',
    source: '平台使用指南',
    duration: '7 分钟',
    updatedAt: '2026-11-04',
    summary: '选方、看组成、解配伍、查出处、看边界、做收藏。',
    url: '/guide',
  },
]

export const AUTHORITY_SOURCES: AuthoritySource[] = [
  {
    id: 1,
    name: '国家中医药管理局',
    shortName: '国家中医药局',
    category: '政策与标准',
    region: '中国',
    description: '发布中医药政策、标准、健康科普与行业公开信息，可作为政策和权威信息的核验入口。',
    focus: ['中医药政策', '行业标准', '公众健康', '文化传播'],
    url: 'https://www.natcm.gov.cn/',
    verifiedAt: '2026-11-15',
    accent: '#0B6E69',
  },
  {
    id: 2,
    name: '中华中医药学会',
    shortName: '中华中医药学会',
    category: '学术团体',
    region: '中国',
    description: '中医药学术团体，公开学术活动、标准工作与专业科普信息。',
    focus: ['学术交流', '标准规范', '中医药科普', '人才培养'],
    url: 'https://www.cacm.org.cn/',
    verifiedAt: '2026-11-15',
    accent: '#8C6A31',
  },
  {
    id: 3,
    name: '中国中医科学院',
    shortName: '中国中医科学院',
    category: '科研机构',
    region: '中国',
    description: '国家级中医药科研机构，公开科研进展、学术资料与专业信息。',
    focus: ['中医药研究', '古籍文献', '临床研究', '学术资源'],
    url: 'https://www.cacms.ac.cn/',
    verifiedAt: '2026-11-15',
    accent: '#3B7F89',
  },
  {
    id: 4,
    name: '国家药典委员会',
    shortName: '国家药典委员会',
    category: '药品标准',
    region: '中国',
    description: '负责国家药品标准相关工作，可查询药典标准、公示与标准解读信息。',
    focus: ['中国药典', '中药标准', '炮制规范', '药品安全'],
    url: 'https://www.chp.org.cn/',
    verifiedAt: '2026-11-15',
    accent: '#60706E',
  },
  {
    id: 5,
    name: '中国中医药出版社',
    shortName: '中国中医药出版社',
    category: '专业出版',
    region: '中国',
    description: '出版中医药教材、古籍整理与公众读物，可用于追踪版本和延伸阅读线索。',
    focus: ['中医药教材', '古籍整理', '方剂学', '公众读物'],
    url: 'https://www.cptcm.com/',
    verifiedAt: '2026-11-15',
    accent: '#B85C3E',
  },
  {
    id: 6,
    name: '北京中医药大学',
    shortName: '北京中医药大学',
    category: '高校与教育',
    region: '中国',
    description: '中医药高等院校，公开课程、学术活动与中医药通识教育资源。',
    focus: ['方剂学', '中药学', '中医药教育', '公众课程'],
    url: 'https://www.bucm.edu.cn/',
    verifiedAt: '2026-11-15',
    accent: '#447A68',
  },
  {
    id: 7,
    name: '中国中医药报',
    shortName: '中国中医药报',
    category: '行业媒体',
    region: '中国',
    description: '中医药行业媒体，可辅助了解政策动态、学术会议与公众科普报道。',
    focus: ['行业动态', '中医药文化', '健康科普', '政策解读'],
    url: 'https://www.cntcm.com.cn/',
    verifiedAt: '2026-11-15',
    accent: '#A66A2B',
  },
  {
    id: 8,
    name: '中国药学会',
    shortName: '中国药学会',
    category: '药学组织',
    region: '中国',
    description: '药学学术组织，公开药学知识、学术活动与合理用药相关科普信息。',
    focus: ['药学知识', '合理用药', '药品安全', '学术资源'],
    url: 'https://www.cpa.org.cn/',
    verifiedAt: '2026-11-15',
    accent: '#5E6F91',
  },
]

export const HOME_QUESTIONS = [
  '四君子汤为什么由四味药组成？',
  '桂枝汤与麻黄汤有什么不同？',
  '君臣佐使如何帮助我们理解一首方？',
  '为什么方剂强调辨证使用？',
  '中药的性味归经是什么意思？',
  '为什么不能照着古籍剂量自行抓药？',
]

export const getTopicByName = (name: string) =>
  SCIENCE_TOPICS.find(
    (topic) =>
      topic.name === name ||
      topic.id === name ||
      CATEGORY_BY_ID.get(name)?.name === name,
  )

export const getArticleByName = (name: string) => {
  const normalized = name.trim().toLowerCase()
  return KNOWLEDGE_ARTICLES.find(
    (article) =>
      article.title.toLowerCase() === normalized ||
      article.keyword.toLowerCase() === normalized ||
      article.id.toLowerCase() === normalized ||
      article.prescription?.name.toLowerCase() === normalized ||
      article.herb?.name.toLowerCase() === normalized ||
      article.herb?.pinyin.toLowerCase() === normalized,
  )
}

export const searchKnowledge = (keyword: string) => {
  const normalized = keyword.trim().toLowerCase()
  if (!normalized) return []

  return KNOWLEDGE_ARTICLES.filter((article) =>
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
      article.herb?.functions || '',
      article.herb?.indications || '',
      article.herb?.pinyin || '',
      ...article.tags,
    ]
      .join(' ')
      .toLowerCase()
      .includes(normalized),
  )
}
