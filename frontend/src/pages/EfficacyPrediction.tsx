import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  BookOutlined,
  ExperimentOutlined,
  InfoCircleOutlined,
  ReloadOutlined,
  SafetyCertificateOutlined,
  ShareAltOutlined,
} from '@ant-design/icons'
import { Button, Card, Col, Row, Select, Tag } from 'antd'
import {
  EDUCATION_NOTICE,
  PRESCRIPTIONS,
  PRESCRIPTION_CATEGORIES,
  getHerbsForPrescription,
  getPrescriptionByName,
  getPrescriptionsByCategory,
} from '../data/scienceContent'

const DEFAULT_PRESCRIPTION = '四君子汤'

const EfficacyPrediction: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const initialPrescription =
    getPrescriptionByName(searchParams.get('prescription') || '') ||
    getPrescriptionByName(DEFAULT_PRESCRIPTION) ||
    PRESCRIPTIONS[0]
  const [selectedName, setSelectedName] = useState(initialPrescription.name)
  const [selectedHerbName, setSelectedHerbName] = useState('')

  useEffect(() => {
    const name = searchParams.get('prescription')
    if (!name) return
    const prescription = getPrescriptionByName(name)
    if (prescription) {
      setSelectedName(prescription.name)
      setSelectedHerbName('')
    }
  }, [searchParams])

  const prescription =
    getPrescriptionByName(selectedName) || getPrescriptionByName(DEFAULT_PRESCRIPTION) || PRESCRIPTIONS[0]
  const herbs = getHerbsForPrescription(prescription)
  const selectedHerb = herbs.find((herb) => herb.name === selectedHerbName)
  const peers = useMemo(
    () =>
      getPrescriptionsByCategory(prescription.category)
        .filter((item) => item.id !== prescription.id)
        .slice(0, 4),
    [prescription],
  )

  const selectPrescription = (name: string) => {
    setSelectedName(name)
    setSelectedHerbName('')
  }

  const pickAnother = () => {
    const candidates = PRESCRIPTIONS.filter((item) => item.id !== prescription.id)
    const next = candidates[Math.floor(Math.random() * candidates.length)]
    selectPrescription(next.name)
  }

  return (
    <div className="page-shell formula-lab-page">
      <div className="page-heading page-heading-row">
        <div>
          <div className="page-eyebrow">
            <ExperimentOutlined />
            FORMULA DISSECTION
          </div>
          <h1 className="page-title">方剂拆解实验室</h1>
          <p className="page-description">
            选择一首真实方剂，沿着“出处、组成、功用主治、配伍关系、安全边界”逐层阅读。
            本页不预测药效，也不生成个体处方。
          </p>
        </div>
        <Tag color="cyan">118 首方剂可检索</Tag>
      </div>

      <Row gutter={[20, 20]}>
        <Col xs={24} xl={8}>
          <Card title="选择拆解对象" className="lab-control-card">
            <div className="field-label">方剂名称</div>
            <Select
              showSearch
              value={prescription.name}
              style={{ width: '100%' }}
              onChange={selectPrescription}
              optionFilterProp="label"
              options={PRESCRIPTION_CATEGORIES.map((item) => ({
                label: item.name,
                options: getPrescriptionsByCategory(item.name).map((formula) => ({
                  value: formula.name,
                  label: formula.name,
                })),
              }))}
            />

            <div className="lab-question">
              <span>本次阅读问题</span>
              <p>{prescription.name}由哪些药味组成，为什么归入{prescription.category}？</p>
            </div>

            <div className="formula-lab-facts">
              <div>
                <span>方剂类别</span>
                <strong>{prescription.category}</strong>
              </div>
              <div>
                <span>出处线索</span>
                <strong>《{prescription.source}》</strong>
              </div>
              <div>
                <span>组成药味</span>
                <strong>{prescription.herb_names.length} 味</strong>
              </div>
              <div>
                <span>同类条目</span>
                <strong>{getPrescriptionsByCategory(prescription.category).length} 首</strong>
              </div>
            </div>

            <div className="lab-buttons">
              <Button
                type="primary"
                icon={<ShareAltOutlined />}
                onClick={() =>
                  navigate(`/analysis?q=${encodeURIComponent(`${prescription.name}由哪些药组成？`)}`)
                }
              >
                继续追问
              </Button>
              <Button icon={<ReloadOutlined />} onClick={pickAnother}>
                换一首
              </Button>
            </div>
          </Card>

          <Card title="同类方延伸" className="result-card">
            {peers.length ? (
              <div className="formula-peer-list">
                {peers.map((peer) => (
                  <button type="button" key={peer.id} onClick={() => selectPrescription(peer.name)}>
                    <div>
                      <strong>{peer.name}</strong>
                      <span>{peer.functions}</span>
                    </div>
                    <Tag>{peer.herb_names.length} 味</Tag>
                  </button>
                ))}
              </div>
            ) : (
              <p className="formula-empty-copy">当前类别暂无其他方剂条目。</p>
            )}
          </Card>
        </Col>

        <Col xs={24} xl={16}>
          <Card
            title={
              <span className="card-title-with-icon">
                <BookOutlined /> {prescription.name} · 方剂档案
              </span>
            }
            extra={<Tag color="cyan">{prescription.category}</Tag>}
          >
            <div className="formula-profile-intro">
              <div>
                <span className="section-caption">传统功用</span>
                <strong>{prescription.functions}</strong>
              </div>
              <div>
                <span className="section-caption">传统主治表述</span>
                <strong>{prescription.indications}</strong>
              </div>
            </div>

            <div className="formula-herb-panel">
              <div className="knowledge-section-label">
                <ExperimentOutlined />
                组成药味 · 点击查看单味药资料
              </div>
              <div className="formula-herb-grid">
                {prescription.herb_names.map((herbName) => (
                  <button
                    type="button"
                    key={herbName}
                    className={selectedHerbName === herbName ? 'is-active' : ''}
                    onClick={() => setSelectedHerbName(herbName === selectedHerbName ? '' : herbName)}
                  >
                    {herbName}
                  </button>
                ))}
              </div>
            </div>

            {selectedHerb && (
              <div className="formula-herb-detail">
                <div>
                  <span className="section-caption">单味药学习卡</span>
                  <h3>{selectedHerb.name}</h3>
                  <p>{selectedHerb.property}；{selectedHerb.meridian}。</p>
                </div>
                <div>
                  <strong>功能与主治</strong>
                  <p>{selectedHerb.functions}。传统主治表述：{selectedHerb.indications}。</p>
                  <strong>使用注意</strong>
                  <p>{selectedHerb.precautions}</p>
                </div>
                <Button onClick={() => navigate(`/herbs?name=${encodeURIComponent(selectedHerb.name)}`)}>
                  查看中药图鉴
                </Button>
              </div>
            )}

            <div className="formula-reading-grid">
              <section>
                <h3>01 · 先看方源与类别</h3>
                <p>
                  本方资料标注出自《{prescription.source}》，归入{prescription.category}。
                  阅读时还应继续核对古籍版本、原文语境和后世方书之间的差异。
                </p>
              </section>
              <section>
                <h3>02 · 再拆组成与药味</h3>
                <p>
                  教材式组成记录为：{prescription.herbs_raw}。学习配伍时，不只看药味数量，
                  还要观察每味药在方中承担的主要方向、兼治作用与药性制约。
                </p>
              </section>
              <section>
                <h3>03 · 放回功用与主治</h3>
                <p>
                  传统功用与主治表述属于中医辨证语境，需要结合证候、体质、病程和兼证理解，
                  不能直接对应某一个现代疾病名称或自行用药方案。
                </p>
              </section>
              <section>
                <h3>04 · 比较同类方</h3>
                <p>
                  可与{peers.length ? peers.map((item) => item.name).join('、') : '同类别其他方剂'}
                  比较共同药味、特有药味和主治表述，理解组方侧重点为什么不同。
                </p>
              </section>
            </div>

            <div className="formula-safety-panel">
              <SafetyCertificateOutlined />
              <div>
                <strong>安全边界</strong>
                <p>{EDUCATION_NOTICE}</p>
                <p>
                  古籍剂量仅作历史资料；毒性药、炮制、妊娠禁忌、十八反十九畏及特殊人群用药，
                  必须由中医师或药师判断，请勿照方自行抓药。
                </p>
              </div>
            </div>
          </Card>

          <Card
            title={<span className="card-title-with-icon"><InfoCircleOutlined /> 拆解说明</span>}
            className="result-card"
          >
            <div className="experiment-flow">
              {[
                ['01', '核对方源', '确认方名、类别与出处线索'],
                ['02', '列出组成', '完整记录全部药味'],
                ['03', '理解语境', '对照功用、主治与传统证候'],
                ['04', '说明边界', '保留剂量、炮制与专业指导提示'],
              ].map(([number, title, detail]) => (
                <div key={number} className="flow-step is-complete">
                  <span>{number}</span>
                  <strong>{title}</strong>
                  <small>{detail}</small>
                </div>
              ))}
            </div>
            <div className="science-note">
              <InfoCircleOutlined />
              <span>
                当前页面提供的是资料化拆解，不计算疗效、不评价某一首方是否适合某个人，
                也不以任何分数替代专业辨证。
              </span>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default EfficacyPrediction
