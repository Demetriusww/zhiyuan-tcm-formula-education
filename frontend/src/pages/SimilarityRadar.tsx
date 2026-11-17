import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  ApartmentOutlined,
  ArrowRightOutlined,
  NodeIndexOutlined,
  RadarChartOutlined,
} from '@ant-design/icons'
import { Button, Card, Col, Progress, Row, Select, Tag } from 'antd'
import * as echarts from 'echarts'
import {
  PRESCRIPTION_CATEGORIES,
  type PrescriptionCategory,
} from '../data/scienceContent'

const DIMENSION_LABELS = {
  fundamentals: '组成关联',
  application: '出处关联',
  impact: '配伍关联',
  accessibility: '类别关联',
  practice: '公众可读性',
  frontier: '延伸学习',
}

const similarity = (base: PrescriptionCategory, compare: PrescriptionCategory) => {
  const keys = Object.keys(base.dimensions) as Array<keyof PrescriptionCategory['dimensions']>
  const distance = keys.reduce(
    (sum, key) => sum + Math.abs(base.dimensions[key] - compare.dimensions[key]) / 100,
    0,
  )
  const sharedExampleBonus =
    compare.examples.some((example) => base.examples.includes(example)) ? 6 : 0
  return Math.max(
    35,
    Math.min(96, Math.round((1 - distance / keys.length) * 100 + compare.count * 0.08 + sharedExampleBonus)),
  )
}

const SimilarityRadar: React.FC = () => {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const initialTopic =
    PRESCRIPTION_CATEGORIES.find((item) => item.name === params.get('topic')) ||
    PRESCRIPTION_CATEGORIES[0]
  const [topicName, setTopicName] = useState(initialTopic.name)
  const chartRef = useRef<HTMLDivElement>(null)

  const topic =
    PRESCRIPTION_CATEGORIES.find((item) => item.name === topicName) ||
    PRESCRIPTION_CATEGORIES[0]
  const related = useMemo(
    () =>
      PRESCRIPTION_CATEGORIES.filter((item) => item.id !== topic.id)
        .map((item) => ({ topic: item, score: similarity(topic, item) }))
        .sort((a, b) => b.score - a.score)
        .slice(0, 4),
    [topic],
  )

  useEffect(() => {
    if (!chartRef.current) return
    const chart = echarts.init(chartRef.current)
    const keys = Object.keys(topic.dimensions) as Array<keyof PrescriptionCategory['dimensions']>
    chart.setOption({
      color: ['#0B6E69', '#E96B4C', '#B48725', '#3C8A62'],
      tooltip: {},
      legend: {
        bottom: 0,
        textStyle: { color: '#6B7E85', fontSize: 11 },
        itemWidth: 14,
        itemHeight: 8,
      },
      radar: {
        center: ['50%', '44%'],
        radius: '62%',
        splitNumber: 4,
        axisName: { color: '#334A52', fontSize: 12 },
        splitLine: { lineStyle: { color: '#DDE6E8' } },
        splitArea: { areaStyle: { color: ['#FFFFFF', '#F7FAFA'] } },
        axisLine: { lineStyle: { color: '#DDE6E8' } },
        indicator: keys.map((key) => ({ name: DIMENSION_LABELS[key], max: 100 })),
      },
      series: [
        {
          type: 'radar',
          symbolSize: 5,
          data: [topic, ...related.slice(0, 3).map((item) => item.topic)].map((item) => ({
            name: item.name,
            value: keys.map((key) => item.dimensions[key]),
            areaStyle: { opacity: item.id === topic.id ? 0.18 : 0.05 },
            lineStyle: { width: item.id === topic.id ? 2.4 : 1.4 },
          })),
        },
      ],
    })
    const resize = () => chart.resize()
    window.addEventListener('resize', resize)
    return () => {
      window.removeEventListener('resize', resize)
      chart.dispose()
    }
  }, [topic, related])

  return (
    <div className="page-shell">
      <div className="page-heading page-heading-row">
        <div>
          <div className="page-eyebrow">
            <RadarChartOutlined />
            FORMULA LEARNING MAP
          </div>
          <h1 className="page-title">方剂类别学习推荐</h1>
          <p className="page-description">
            从组成、方源、配伍与类别等角度观察十五类方剂的学习关联，
            为课堂、展陈和自主阅读推荐一条循序渐进的方剂通识路径。
          </p>
        </div>
        <Select
          value={topicName}
          onChange={setTopicName}
          options={PRESCRIPTION_CATEGORIES.map((item) => ({
            value: item.name,
            label: `${item.name} · ${item.count} 方`,
          }))}
          style={{ width: 200 }}
          aria-label="选择方剂类别"
        />
      </div>

      <Row gutter={[20, 20]}>
        <Col xs={24} xl={15}>
          <Card
            title={
              <span className="card-title-with-icon">
                <RadarChartOutlined /> {topic.name} · 学习关联雷达
              </span>
            }
            extra={<Tag color="cyan">{topic.count} 首方剂</Tag>}
          >
            <div ref={chartRef} className="radar-chart" />
            <p className="chart-footnote">
              维度数值用于本地内容推荐与学习路径组织，不是方剂价值、临床疗效或研究质量的排名。
            </p>
          </Card>
        </Col>

        <Col xs={24} xl={9}>
          <Card title="类别概览">
            <div className="topic-overview">
              <span className="topic-overview-mark" style={{ background: topic.accent }}>
                <NodeIndexOutlined />
              </span>
              <h2>{topic.name}</h2>
              <p>{topic.description}</p>
              <div className="topic-overview-tags">
                <Tag>{topic.category}</Tag>
                <Tag>方剂通识</Tag>
                <Tag>{topic.count} 首</Tag>
              </div>
              <div className="topic-overview-tags">
                {topic.examples.map((name) => (
                  <Tag key={name} color="cyan">{name}</Tag>
                ))}
              </div>
            </div>
          </Card>

          <Card title="适合接着学习的类别" className="result-card">
            <div className="related-topic-list">
              {related.map((item) => (
                <div className="related-topic" key={item.topic.id}>
                  <span className="related-topic-dot" style={{ background: item.topic.accent }} />
                  <div className="related-topic-main">
                    <strong>{item.topic.name}</strong>
                    <span>{item.topic.summary}</span>
                    <Progress
                      percent={item.score}
                      size="small"
                      showInfo={false}
                      strokeColor={item.topic.accent}
                    />
                  </div>
                  <div className="related-topic-score">{item.score}%</div>
                </div>
              ))}
            </div>
            <Button
              block
              icon={<ApartmentOutlined />}
              onClick={() => navigate(`/visualization?topic=${encodeURIComponent(topic.name)}`)}
            >
              在方剂知识图谱中查看
            </Button>
          </Card>
        </Col>
      </Row>

      <div className="recommendation-strip">
        <div>
          <span>推荐学习路径</span>
          <strong>
            {topic.name} → {topic.examples[0]} → {related[0]?.topic.examples[0]}
          </strong>
        </div>
        <Button
          type="primary"
          onClick={() => navigate(`/smart?topic=${encodeURIComponent(topic.name)}`)}
        >
          生成方剂学习任务 <ArrowRightOutlined />
        </Button>
      </div>
    </div>
  )
}

export default SimilarityRadar
