import { memo, useCallback, useState } from 'react'
import {
  CaretRightOutlined,
  FileTextOutlined,
  FolderOpenOutlined,
  FolderOutlined,
  NodeIndexOutlined,
} from '@ant-design/icons'

export interface KnowledgeTreeNode {
  id: string
  name: string
  description?: string
  meta?: string
  children?: KnowledgeTreeNode[]
}

interface KnowledgeCategoryTreeProps {
  data: KnowledgeTreeNode[]
  selectedKey?: string
  onSelect?: (key: string, item: KnowledgeTreeNode) => void
  defaultExpandedKeys?: string[]
}

interface TreeNodeProps {
  item: KnowledgeTreeNode
  level: number
  expandedKeys: Record<string, boolean>
  selectedKey?: string
  onToggle: (key: string) => void
  onSelect: (key: string, item: KnowledgeTreeNode) => void
}

const LEVEL_ACCENTS = ['#0B6E69', '#3C8A62', '#B48725']

const TreeNode = memo<TreeNodeProps>(
  ({ item, level, expandedKeys, selectedKey, onToggle, onSelect }) => {
    const hasChildren = Boolean(item.children?.length)
    const isExpanded = Boolean(expandedKeys[item.id])
    const isSelected = selectedKey === item.id
    const accent = LEVEL_ACCENTS[Math.min(level, LEVEL_ACCENTS.length - 1)]

    const handleClick = () => {
      if (hasChildren) onToggle(item.id)
      onSelect(item.id, item)
    }

    return (
      <div className="knowledge-tree-node">
        <button
          type="button"
          className={`knowledge-tree-row level-${level}${isSelected ? ' is-selected' : ''}`}
          style={{ paddingLeft: 12 + level * 18 }}
          onClick={handleClick}
          aria-expanded={hasChildren ? isExpanded : undefined}
        >
          <span
            className={`knowledge-tree-caret${hasChildren ? '' : ' is-hidden'}`}
            onClick={(event) => {
              event.stopPropagation()
              if (hasChildren) onToggle(item.id)
            }}
          >
            <CaretRightOutlined rotate={isExpanded ? 90 : 0} />
          </span>
          <span className="knowledge-tree-icon" style={{ color: accent }}>
            {level === 0 ? (
              isExpanded ? <FolderOpenOutlined /> : <FolderOutlined />
            ) : level === 1 ? (
              <NodeIndexOutlined />
            ) : (
              <FileTextOutlined />
            )}
          </span>
          <span className="knowledge-tree-label">
            <strong>{item.name}</strong>
            {level < 2 && item.description && <small>{item.description}</small>}
          </span>
          {item.meta && <span className="knowledge-tree-meta">{item.meta}</span>}
        </button>

        {hasChildren && isExpanded && (
          <div className="knowledge-tree-children">
            {item.children?.map((child) => (
              <TreeNode
                key={child.id}
                item={child}
                level={level + 1}
                expandedKeys={expandedKeys}
                selectedKey={selectedKey}
                onToggle={onToggle}
                onSelect={onSelect}
              />
            ))}
          </div>
        )}
      </div>
    )
  },
)

TreeNode.displayName = 'KnowledgeTreeNode'

const HerbCategoryTree: React.FC<KnowledgeCategoryTreeProps> = ({
  data,
  selectedKey,
  onSelect,
  defaultExpandedKeys = [],
}) => {
  const [expandedKeys, setExpandedKeys] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(defaultExpandedKeys.map((key) => [key, true])),
  )

  const handleToggle = useCallback((key: string) => {
    setExpandedKeys((current) => ({ ...current, [key]: !current[key] }))
  }, [])

  const handleSelect = useCallback(
    (key: string, item: KnowledgeTreeNode) => {
      onSelect?.(key, item)
    },
    [onSelect],
  )

  const setAll = (expanded: boolean) => {
    if (!expanded) {
      setExpandedKeys({})
      return
    }
    const next: Record<string, boolean> = {}
    const visit = (nodes: KnowledgeTreeNode[]) => {
      nodes.forEach((node) => {
        if (node.children?.length) {
          next[node.id] = true
          visit(node.children)
        }
      })
    }
    visit(data)
    setExpandedKeys(next)
  }

  return (
    <div className="knowledge-category-tree">
      <div className="knowledge-tree-toolbar">
        <div>
          <strong>方剂与中药分类</strong>
          <span>{data.length} 个知识入口</span>
        </div>
        <div>
          <button type="button" onClick={() => setAll(true)}>展开</button>
          <button type="button" onClick={() => setAll(false)}>收起</button>
        </div>
      </div>

      <div className="knowledge-tree-scroll">
        {data.map((item) => (
          <TreeNode
            key={item.id}
            item={item}
            level={0}
            expandedKeys={expandedKeys}
            selectedKey={selectedKey}
            onToggle={handleToggle}
            onSelect={handleSelect}
          />
        ))}
      </div>

      <div className="knowledge-tree-footer">
        <span>按方剂类别、方源与中药功能组织</span>
        <span>{Object.values(expandedKeys).filter(Boolean).length} 项已展开</span>
      </div>
    </div>
  )
}

export default HerbCategoryTree
