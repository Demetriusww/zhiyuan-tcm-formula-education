import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  ApartmentOutlined,
  BarChartOutlined,
  BookOutlined,
  NodeIndexOutlined,
  PictureOutlined,
  PieChartOutlined,
  ShareAltOutlined,
} from '@ant-design/icons'
import { Button, Card, Col, Row, Select, Statistic, Tag } from 'antd'
import * as echarts from 'echarts'
import G6, {
  type EdgeConfig,
  type NodeConfig,
} from '@antv/g6'
import {
  HERBS,
  HERB_IMAGE_COUNT,
  PRESCRIPTIONS,
  PRESCRIPTION_CATEGORIES,
  getHerbsForPrescription,
  getPrescriptionByName,
  getTopicByName,
} from '../data/scienceContent'

const topicNodeId = (id: string) => `topic-${id}`
const formulaNodeId = (id: number) => `formula-${id}`
const herbNodeId = (name: string) => `herb-${name}`

const DataVisualization: React.FC = () => {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const initialTopic =
    getTopicByName(params.get('topic') || '') || PRESCRIPTION_CATEGORIES[0]
  const [focusTopic, setFocusTopic] = useState(initialTopic.name)
  const barRef = useRef<HTMLDivElement>(null)
  const pieRef = useRef<HTMLDivElement>(null)
  const graphRef = useRef<HTMLDivElement>(null)

  const categoryStats = useMemo(
    () =>
      PRESCRIPTION_CATEGORIES.map((topic) => ({
        ...topic,
        actualCount: PRESCRIPTIONS.filter((item) => item.category === topic.name).length,
      })),
    [],
  )

  const currentTopic = getTopicByName(focusTopic) || PRESCRIPTION_CATEGORIES[0]
  const currentPrescriptions = useMemo(
    () => PRESCRIPTIONS.filter((item) => item.category === currentTopic.name),
    [currentTopic.name],
  )
  const representatives = useMemo(() => {
    const examples = currentPrescriptions.filter((item) =>
      currentTopic.examples.includes(item.name),
    )
    const rest = currentPrescriptions.filter((item) => !examples.includes(item))
    return [...examples, ...rest].slice(0, 3)
  }, [currentPrescriptions, currentTopic.examples])

  useEffect(() => {
    if (!barRef.current || !pieRef.current) return
    const barChart = echarts.init(barRef.current)
    const pieChart = echarts.init(pieRef.current)

    barChart.setOption({
      color: ['#0B6E69'],
      tooltip: { trigger: 'axis' },
      grid: { left: 38, right: 16, top: 24, bottom: 58 },
      xAxis: {
        type: 'category',
        data: categoryStats.map((item) => item.name),
        axisLine: { lineStyle: { color: '#C8D6D9' } },
        axisTick: { show: false },
        axisLabel: { color: '#6B7E85', fontSize: 10, interval: 0, rotate: 28 },
      },
      yAxis: {
        type: 'value',
        minInterval: 1,
        axisLabel: { color: '#6B7E85', fontSize: 11 },
        splitLine: { lineStyle: { color: '#EEF3F4' } },
      },
      series: [
        {
          type: 'bar',
          barMaxWidth: 27,
          data: categoryStats.map((item) => ({
            value: item.actualCount,
            itemStyle: {
              color: item.accent,
              borderRadius: [4, 4, 0, 0],
            },
          })),
          label: { show: true, position: 'top', color: '#334A52', fontSize: 10 },
        },
      ],
    })

    pieChart.setOption({
      color: ['#0B6E69', '#D8E2E4'],
      tooltip: { trigger: 'item', formatter: '{b}: {c} 味（{d}%）' },
      legend: {
        bottom: 4,
        textStyle: { color: '#6B7E85', fontSize: 11 },
        itemWidth: 12,
        itemHeight: 8,
      },
      series: [
        {
          type: 'pie',
          radius: ['48%', '68%'],
          center: ['50%', '43%'],
          avoidLabelOverlap: true,
          itemStyle: { borderColor: '#FFFFFF', borderWidth: 3 },
          label: { color: '#334A52', fontSize: 11 },
          data: [
            { name: '有本地图片', value: HERB_IMAGE_COUNT },
            { name: '文字图鉴', value: HERBS.length - HERB_IMAGE_COUNT },
          ],
        },
      ],
    })

    const resize = () => {
      barChart.resize()
      pieChart.resize()
    }
    window.addEventListener('resize', resize)
    return () => {
      window.removeEventListener('resize', resize)
      barChart.dispose()
      pieChart.dispose()
    }
  }, [categoryStats])

  useEffect(() => {
    if (!graphRef.current) return
    const width = graphRef.current.clientWidth || 760
    const height = graphRef.current.clientHeight || 520
    const graph = new G6.Graph({
      container: graphRef.current,
      width,
      height,
      fitView: true,
      fitViewPadding: 38,
      modes: {
        default: ['drag-canvas', 'zoom-canvas', 'drag-node'],
      },
      defaultNode: {
        type: 'circle',
        labelCfg: {
          style: {
            fill: '#18303A',
            fontSize: 10,
          },
          position: 'bottom',
          offset: 7,
        },
      },
      defaultEdge: {
        style: {
          stroke: '#C8D6D9',
          lineWidth: 1.2,
          endArrow: false,
        },
      },
      layout: {
        type: 'force',
        preventOverlap: true,
        linkDistance: 92,
        nodeStrength: -110,
        edgeStrength: 0.55,
      },
    })

    const nodes: NodeConfig[] = PRESCRIPTION_CATEGORIES.map((topic) => ({
      id: topicNodeId(topic.id),
      label: topic.name,
      size: topic.id === currentTopic.id ? 62 : 42,
      style: {
        fill: topic.accent,
        stroke: topic.id === currentTopic.id ? '#F0B43C' : '#FFFFFF',
        lineWidth: topic.id === currentTopic.id ? 4 : 2.5,
        shadowColor: `${topic.accent}55`,
        shadowBlur: topic.id === currentTopic.id ? 18 : 10,
      },
      labelCfg: {
        style: { fill: '#FFFFFF', fontSize: topic.id === currentTopic.id ? 11 : 9, fontWeight: 600 },
        position: 'center',
      },
    }))

    const edges: EdgeConfig[] = []
    representatives.forEach((prescription) => {
      const formulaId = formulaNodeId(prescription.id)
      nodes.push({
        id: formulaId,
        label: prescription.name,
        size: 31,
        style: {
          fill: '#FFF5DA',
          stroke: currentTopic.accent,
          lineWidth: 1.5,
        },
        labelCfg: {
          style: { fill: '#334A52', fontSize: 9 },
          position: 'bottom',
          offset: 5,
        },
      })
      edges.push({
        source: topicNodeId(currentTopic.id),
        target: formulaId,
        style: { stroke: currentTopic.accent, lineWidth: 1.6 },
      })

      getHerbsForPrescription(prescription).forEach((herb) => {
        const id = herbNodeId(herb.name)
        if (!nodes.some((node) => node.id === id)) {
          nodes.push({
            id,
            label: herb.name,
            size: 20,
            style: {
              fill: '#E7F3F1',
              stroke: '#8DBEBA',
              lineWidth: 1,
            },
            labelCfg: {
              style: { fill: '#476067', fontSize: 8 },
              position: 'bottom',
              offset: 4,
            },
          })
        }
        edges.push({
          source: formulaId,
          target: id,
          style: { stroke: '#C8D6D9', lineWidth: 1 },
        })
      })
    })

    graph.data({ nodes, edges })
    graph.render()
    graph.on('node:click', (event: any) => {
      const model = event.item?.getModel()
      const id = String(model?.id || '')

      if (id.startsWith('topic-')) {
        const topic = PRESCRIPTION_CATEGORIES.find((item) => topicNodeId(item.id) === id)
        if (topic) setFocusTopic(topic.name)
        return
      }

      if (id.startsWith('formula-')) {
        const prescription = getPrescriptionByName(id.replace('formula-', ''))
        if (prescription) {
          navigate(`/efficacy?prescription=${encodeURIComponent(prescription.name)}`)
        }
        return
      }

      if (id.startsWith('herb-')) {
        navigate(`/herbs?name=${encodeURIComponent(id.replace('herb-', ''))}`)
      }
    })

    const resize = () => {
      if (!graphRef.current || graph.get('destroyed')) return
      graph.changeSize(
        graphRef.current.clientWidth || width,
        graphRef.current.clientHeight || height,
      )
    }
    window.addEventListener('resize', resize)
    return () => {
      window.removeEventListener('resize', resize)
      graph.destroy()
    }
  }, [currentTopic, navigate, representatives])

  return (
    <div className="page-shell data-visualization-page">
      <div className="page-heading page-heading-row">
        <div>
          <div className="page-eyebrow">
            <ShareAltOutlined />
            FORMULA KNOWLEDGE ATLAS
          </div>
          <h1 className="page-title">方剂知识图谱</h1>
          <p className="page-description">
            从十五类方剂进入代表方，再查看组成中药与关联图鉴。
            图谱用于通识学习和内容发现，不代表方剂之间的疗效排序或临床替代关系。
          </p>
        </div>
        <Select
          value={focusTopic}
          onChange={setFocusTopic}
          style={{ width: 190 }}
          options={PRESCRIPTION_CATEGORIES.map((topic) => ({
            value: topic.name,
            label: `${topic.name} · ${topic.count}`,
          }))}
          aria-label="选择方剂类别"
        />
      </div>

      <div className="data-viz-metrics">
        <Card>
          <Statistic
            title="方剂类别"
            value={PRESCRIPTION_CATEGORIES.length}
            suffix="类"
            prefix={<NodeIndexOutlined />}
          />
        </Card>
        <Card>
          <Statistic
            title="经典方剂"
            value={PRESCRIPTIONS.length}
            suffix="首"
            prefix={<BookOutlined />}
          />
        </Card>
        <Card>
          <Statistic
            title="中药图鉴"
            value={HERBS.length}
            suffix="味"
            prefix={<ApartmentOutlined />}
          />
        </Card>
        <Card>
          <Statistic
            title="本地中药图片"
            value={HERB_IMAGE_COUNT}
            suffix="张"
            prefix={<PictureOutlined />}
          />
        </Card>
      </div>

      <Row gutter={[18, 18]}>
        <Col xs={24} xl={15}>
          <Card
            title={
              <span className="card-title-with-icon">
                <ShareAltOutlined /> 类别 · 代表方 · 组成中药
              </span>
            }
            extra={<Tag color="cyan">可缩放 · 可拖动</Tag>}
          >
            <div ref={graphRef} className="knowledge-graph-canvas" />
            <p className="chart-footnote">
              点击类别切换当前学习范围；点击代表方进入方剂拆解，点击中药进入图鉴。拖动节点或画布可调整视角。
            </p>
          </Card>
        </Col>
        <Col xs={24} xl={9}>
          <Card
            title={
              <span className="card-title-with-icon">
                <BarChartOutlined /> 十五类方剂数量
              </span>
            }
          >
            <div ref={barRef} className="viz-chart-small" />
          </Card>
          <Card
            title={
              <span className="card-title-with-icon">
                <PieChartOutlined /> 中药图片覆盖
              </span>
            }
            className="result-card"
          >
            <div ref={pieRef} className="viz-chart-small" />
          </Card>
        </Col>
      </Row>

      <Card
        className="topic-focus-card"
        title={
          <span className="card-title-with-icon">
            <NodeIndexOutlined /> {currentTopic.name} · 学习入口
          </span>
        }
        extra={
          <Button
            type="link"
            onClick={() =>
              navigate(`/similarity?topic=${encodeURIComponent(currentTopic.name)}`)
            }
          >
            查看类别关联
          </Button>
        }
      >
        <div className="topic-focus-layout">
          <div className="topic-focus-intro">
            <span style={{ background: currentTopic.accent }} />
            <p>{currentTopic.description}</p>
            <div>
              <Tag>{currentTopic.category}</Tag>
              <Tag>{currentPrescriptions.length} 首方剂</Tag>
              <Tag>{currentTopic.examples[0]}</Tag>
            </div>
          </div>
          <div className="topic-focus-articles">
            {representatives.map((prescription) => (
              <button
                type="button"
                key={prescription.id}
                onClick={() =>
                  navigate(`/efficacy?prescription=${encodeURIComponent(prescription.name)}`)
                }
              >
                <span>{prescription.category} · 《{prescription.source}》</span>
                <strong>{prescription.name}</strong>
                <small>{prescription.herb_names.length} 味药 · 查看组成与配伍</small>
              </button>
            ))}
          </div>
        </div>
      </Card>
    </div>
  )
}

export default DataVisualization
