import { useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BookOutlined,
  CameraOutlined,
  CheckCircleOutlined,
  CloudUploadOutlined,
  EyeOutlined,
  HistoryOutlined,
  InfoCircleOutlined,
  PictureOutlined,
  ReloadOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons'
import {
  App as AntdApp,
  Alert,
  Button,
  Card,
  Col,
  Row,
  Tag,
  Upload,
} from 'antd'
import type { UploadProps } from 'antd'
import {
  HERBS,
  getHerbImageUrl,
  getPrescriptionsContainingHerb,
  hasHerbImage,
  type Herb,
} from '../data/scienceContent'

const { Dragger } = Upload

interface HistoryItem {
  id: number
  name: string
  time: string
}

const SAMPLE_HERBS = HERBS.filter(hasHerbImage).sort((a, b) =>
  a.pinyin.localeCompare(b.pinyin),
)

const HerbRecognition: React.FC = () => {
  const navigate = useNavigate()
  const { message } = AntdApp.useApp()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [selectedHerbName, setSelectedHerbName] = useState(SAMPLE_HERBS[0]?.name || '')
  const [uploadPreview, setUploadPreview] = useState('')
  const [fileName, setFileName] = useState('')
  const [history, setHistory] = useState<HistoryItem[]>([])

  const selectedHerb = useMemo(
    () => HERBS.find((herb) => herb.name === selectedHerbName) || SAMPLE_HERBS[0],
    [selectedHerbName],
  )
  const relatedPrescriptions = selectedHerb
    ? getPrescriptionsContainingHerb(selectedHerb.name).slice(0, 4)
    : []
  const isUpload = Boolean(uploadPreview)

  const rememberSample = (herb: Herb) => {
    setHistory((current) => [
      {
        id: Date.now(),
        name: herb.name,
        time: new Date().toLocaleTimeString('zh-CN', {
          hour: '2-digit',
          minute: '2-digit',
        }),
      },
      ...current.filter((item) => item.name !== herb.name),
    ].slice(0, 5))
  }

  const selectSample = (herb: Herb) => {
    setSelectedHerbName(herb.name)
    setUploadPreview('')
    setFileName('')
    if (fileInputRef.current) fileInputRef.current.value = ''
    rememberSample(herb)
  }

  const loadFile = (file: File) => {
    if (!file.type.startsWith('image/')) {
      message.warning('请选择 JPG、PNG、WebP 等图片文件')
      return
    }
    if (file.size > 8 * 1024 * 1024) {
      message.warning('观察图片请控制在 8 MB 以内')
      return
    }
    const reader = new FileReader()
    reader.onload = () => {
      setUploadPreview(String(reader.result || ''))
      setFileName(file.name)
    }
    reader.readAsDataURL(file)
  }

  const uploadProps: UploadProps = {
    accept: 'image/*',
    multiple: false,
    showUploadList: false,
    beforeUpload: (file) => {
      loadFile(file)
      return Upload.LIST_IGNORE
    },
  }

  const clearUpload = () => {
    setUploadPreview('')
    setFileName('')
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const displayImage = uploadPreview || (selectedHerb ? getHerbImageUrl(selectedHerb) : '')

  return (
    <div className="page-shell recognition-page">
      <div className="page-heading page-heading-row">
        <div>
          <div className="page-eyebrow">
            <CameraOutlined />
            HERB OBSERVATION ATLAS
          </div>
          <h1 className="page-title">中药图鉴观察与辨识</h1>
          <p className="page-description">
            通过内置中药样片认识药材外观，并结合性味归经、功能、关联方剂与使用注意学习。
            也支持本地图片观察，但不进行真伪鉴定、品质判断或自动用药判断。
          </p>
        </div>
        <Tag color="gold">{SAMPLE_HERBS.length} 张内置样片</Tag>
      </div>

      <Alert
        type="info"
        showIcon
        className="recognition-notice"
        message="图片只能建立初步外观印象，不能代替专业鉴定"
        description="中药材鉴别通常还需要观察质地、断面、气味，并结合显微、理化或标准对照等方法。平台不生成“识别置信度”，也不宣称上传图片即可判断药材名称、真伪或品质。"
      />

      <Card
        title={
          <span className="card-title-with-icon">
            <PictureOutlined /> 已有中药样片
          </span>
        }
        extra={<Tag color="cyan">本地图片 · 学习展示</Tag>}
        className="herb-sample-library"
      >
        <div className="herb-sample-strip">
          {SAMPLE_HERBS.map((herb) => (
            <button
              type="button"
              key={herb.name}
              className={`herb-sample-card${!isUpload && selectedHerb?.name === herb.name ? ' is-active' : ''}`}
              onClick={() => selectSample(herb)}
            >
              <img src={getHerbImageUrl(herb)} alt={`${herb.name}样片`} loading="lazy" />
              <strong>{herb.name}</strong>
              <span>{herb.pinyin}</span>
            </button>
          ))}
        </div>
      </Card>

      <Row gutter={[18, 18]} className="herb-observation-layout">
        <Col xs={24} xl={14}>
          <Card
            title={
              <span className="card-title-with-icon">
                <CameraOutlined /> {isUpload ? '本地图片观察' : '当前样片'}
              </span>
            }
            extra={
              isUpload ? (
                <Button type="text" icon={<ReloadOutlined />} onClick={clearUpload}>
                  清除上传
                </Button>
              ) : (
                <Tag color="success">内置图鉴图片</Tag>
              )
            }
          >
            {displayImage ? (
              <div className="recognition-image-preview">
                <img
                  src={displayImage}
                  alt={isUpload ? `本地观察图片：${fileName}` : `${selectedHerb?.name}中药样片`}
                />
                <div className="recognition-image-meta">
                  <span>{isUpload ? fileName : `${selectedHerb?.name} · ${selectedHerb?.pinyin}`}</span>
                  <Tag>{isUpload ? '仅本地预览' : '学习样片'}</Tag>
                </div>
              </div>
            ) : null}

            {!isUpload && (
              <div className="recognition-controls recognition-sample-actions">
                <div>
                  <div className="field-label">学习对象</div>
                  <strong>{selectedHerb?.name} · {selectedHerb?.latin}</strong>
                </div>
                <div>
                  <div className="field-label">进入完整图鉴</div>
                  <Button
                    block
                    icon={<BookOutlined />}
                    onClick={() =>
                      navigate(`/herbs?name=${encodeURIComponent(selectedHerb?.name || '')}`)
                    }
                  >
                    查看方药关联
                  </Button>
                </div>
              </div>
            )}
          </Card>

          <Card title="尝试观察自己的图片" className="result-card">
            <div className="recognition-upload-shell">
              <Dragger {...uploadProps}>
                <div className="recognition-placeholder">
                  <span className="recognition-upload-icon">
                    <CloudUploadOutlined />
                  </span>
                  <h3>拖入一张药材或饮片图片</h3>
                  <p>JPG、PNG、WebP，最大 8 MB。图片只在当前浏览器预览。</p>
                  <Button icon={<CameraOutlined />}>选择图片</Button>
                </div>
              </Dragger>
              <input
                ref={fileInputRef}
                className="visually-hidden"
                type="file"
                accept="image/*"
                aria-label="选择本地中药图片"
                onChange={(event) => {
                  const file = event.target.files?.[0]
                  if (file) loadFile(file)
                }}
              />
            </div>
          </Card>
        </Col>

        <Col xs={24} xl={10}>
          <Card
            className="recognition-result-card"
            title={
              <span className="card-title-with-icon">
                {isUpload ? <EyeOutlined /> : <SafetyCertificateOutlined />}
                {isUpload ? '图片观察清单' : `${selectedHerb?.name || '中药'} · 样片资料`}
              </span>
            }
            extra={isUpload ? <Tag color="warning">需专业复核</Tag> : <Tag color="success">文字图鉴</Tag>}
          >
            {isUpload ? (
              <div className="herb-observation-copy">
                <h2>先记录，不急着下结论</h2>
                <p>
                  当前只显示上传图片，不生成药材名称或识别分数。可以按以下清单观察，
                  但任何结论都需要对照标准药材、专业图谱和实物复核。
                </p>
                <div className="herb-observation-list">
                  {[
                    '图片是否清楚展示了完整形态、边缘与表面纹理？',
                    '是否记录了拍摄部位、大小参照和光线条件？',
                    '是否能观察断面、质地、气味等图片之外的信息？',
                    '是否有待核对的标准名称、来源批次或炮制方式？',
                    '是否把图片观察与真伪、品质和用药决策明确分开？',
                  ].map((item) => (
                    <div key={item}>
                      <CheckCircleOutlined />
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
                <div className="recognition-boundary">
                  <InfoCircleOutlined />
                  <span>
                    单张图片不能确认药材身份。需要鉴定时，应由具备资质的机构或专业人员，
                    按现行标准和规范完成检查。
                  </span>
                </div>
              </div>
            ) : selectedHerb ? (
              <div className="formula-herb-profile">
                <div className="classification-main">
                  <div>
                    <span>中药图鉴样片</span>
                    <h2>{selectedHerb.name}</h2>
                    <p>{selectedHerb.description}</p>
                  </div>
                </div>
                <div className="formula-knowledge-facts">
                  <div><span>性味</span><strong>{selectedHerb.property}</strong></div>
                  <div><span>归经</span><strong>{selectedHerb.meridian}</strong></div>
                  <div className="is-wide"><span>功能</span><strong>{selectedHerb.functions}</strong></div>
                  <div className="is-wide"><span>传统主治</span><strong>{selectedHerb.indications}</strong></div>
                  <div className="is-wide"><span>资料参考用量</span><strong>{selectedHerb.dosage}</strong></div>
                  <div className="is-wide"><span>使用注意</span><strong>{selectedHerb.precautions}</strong></div>
                </div>
                <div className="formula-herb-prescriptions">
                  <div className="knowledge-section-label">
                    <BookOutlined />
                    常见关联方
                  </div>
                  <div className="related-knowledge-grid">
                    {relatedPrescriptions.map((prescription) => (
                      <button
                        type="button"
                        key={prescription.id}
                        onClick={() =>
                          navigate(
                            `/efficacy?prescription=${encodeURIComponent(prescription.name)}`,
                          )
                        }
                      >
                        <span>{prescription.category}</span>
                        <strong>{prescription.name}</strong>
                        <small>《{prescription.source}》</small>
                      </button>
                    ))}
                  </div>
                </div>
                <div className="recognition-boundary">
                  <InfoCircleOutlined />
                  <span>
                    参考用量、炮制和禁忌不能直接转为个人用药方案。涉及妊娠、儿童、慢病、
                    毒性药或正在服药时，应由中医师或药师判断。
                  </span>
                </div>
              </div>
            ) : null}
          </Card>

          <Card
            title={
              <span className="card-title-with-icon">
                <HistoryOutlined /> 最近查看样片
              </span>
            }
            extra={<span className="section-caption">最多保留 5 条</span>}
            className="result-card"
          >
            {history.length ? (
              <div className="recognition-history">
                {history.map((item) => (
                  <button
                    type="button"
                    className="history-row history-row-button"
                    key={`${item.name}-${item.id}`}
                    onClick={() => {
                      const herb = SAMPLE_HERBS.find((entry) => entry.name === item.name)
                      if (herb) selectSample(herb)
                    }}
                  >
                    <span className="history-image-mark"><PictureOutlined /></span>
                    <div>
                      <strong>{item.name}</strong>
                      <span>点击重新查看样片资料</span>
                    </div>
                    <time>{item.time}</time>
                  </button>
                ))}
              </div>
            ) : (
              <div className="recognition-history-empty">
                <HistoryOutlined />
                <span>选择一张样片后，查看记录会出现在这里</span>
              </div>
            )}
          </Card>
        </Col>
      </Row>

      <Card title="样片学习流程" className="result-card">
        <div className="recognition-flow">
          {[
            ['01', '选择样片', '先对照名称与本地图鉴图片'],
            ['02', '记录特征', '观察形态、颜色、表面与边缘'],
            ['03', '回到方剂', '查看该药参与的方剂与配伍'],
            ['04', '阅读边界', '区分学习辨识与专业鉴定'],
          ].map(([number, title, detail]) => (
            <div key={number}>
              <span>{number}</span>
              <strong>{title}</strong>
              <small>{detail}</small>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}

export default HerbRecognition
