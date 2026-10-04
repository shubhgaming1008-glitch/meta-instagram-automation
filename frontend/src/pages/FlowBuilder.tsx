import { useEffect, useState, useCallback, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import ReactFlow, {
  ReactFlowProvider,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  BackgroundVariant,
  MiniMap,
  Panel,
  Connection,
  Edge,
  Node,
  NodeTypes,
  Handle,
  Position,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { automationsApi } from '@/api/client'
import { useToastStore } from '@/store'
import {
  Save, Play, Pause, ArrowLeft, Zap, MessageCircle,
  GitBranch, Clock, Link2, Tag, UserCheck, StopCircle,
  MessageSquare, Shuffle, Mail, Settings, ChevronRight, X, Trash2
} from 'lucide-react'

// ── Custom node renderers ─────────────────────────────────────────
function FlowNode({ data, selected }: { data: any; selected: boolean }) {
  const typeConfig: Record<string, { color: string; icon: string; className: string }> = {
    trigger:        { color: '#c44df3', icon: '⚡', className: 'node-trigger' },
    message:        { color: '#3b82f6', icon: '💬', className: 'node-message' },
    comment_reply:  { color: '#06b6d4', icon: '↩️', className: 'node-message' },
    condition:      { color: '#f59e0b', icon: '🔀', className: 'node-condition' },
    follow_check:   { color: '#8b5cf6', icon: '👥', className: 'node-follow' },
    link:           { color: '#22c55e', icon: '🔗', className: 'node-link' },
    delay:          { color: '#94a3b8', icon: '⏱️', className: 'node-delay' },
    randomizer:     { color: '#ec4899', icon: '🎲', className: 'node-randomizer' },
    tag:            { color: '#f43f5e', icon: '🏷️', className: 'node-tag' },
    remove_tag:     { color: '#f43f5e', icon: '🗑️', className: 'node-tag' },
    collect_email:  { color: '#14b8a6', icon: '📧', className: 'node-message' },
    collect_text:   { color: '#0ea5e9', icon: '📝', className: 'node-message' },
    start_automation:{ color: '#c44df3', icon: '▶️', className: 'node-trigger' },
    end:            { color: '#ef4444', icon: '⏹️', className: 'node-end' },
    button:         { color: '#6366f1', icon: '🔘', className: 'node-message' },
    quick_reply:    { color: '#8b5cf6', icon: '💭', className: 'node-message' },
  }

  const cfg = typeConfig[data.nodeType] || typeConfig.message
  const nodeTypeLabel = data.nodeType?.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())

  return (
    <div className={`flow-node ${cfg.className}${selected ? ' selected' : ''}`}>
      {data.nodeType !== 'trigger' && data.nodeType !== 'start_automation' && (
        <Handle type="target" position={Position.Top} style={{ background: '#555' }} />
      )}
      <div className="flow-node-header">
        <span>{cfg.icon}</span>
        <span>{nodeTypeLabel}</span>
      </div>
      <div className="flow-node-body">
        {data.label && <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>{data.label}</div>}
        {data.text && <div style={{ fontSize: 11, color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 190 }}>"{data.text}"</div>}
        {data.delay_value && <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>⏱ {data.delay_value} {data.delay_unit}</div>}
        {data.tag_name && <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>🏷 {data.tag_name}</div>}
        {data.url && <div style={{ fontSize: 11, color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 190 }}>{data.url}</div>}
      </div>
      {data.nodeType !== 'end' && (
        <Handle type="source" position={Position.Bottom} style={{ background: '#555' }} />
      )}
    </div>
  )
}

const NODE_TYPES: NodeTypes = {
  custom: FlowNode,
}

// ── Node Palette ──────────────────────────────────────────────────
const PALETTE_NODES = [
  { type: 'trigger',        label: 'Trigger',      icon: '⚡' },
  { type: 'message',        label: 'Send DM',      icon: '💬' },
  { type: 'comment_reply',  label: 'Comment Reply',icon: '↩️' },
  { type: 'button',         label: 'Buttons',      icon: '🔘' },
  { type: 'quick_reply',    label: 'Quick Reply',  icon: '💭' },
  { type: 'condition',      label: 'Condition',    icon: '🔀' },
  { type: 'follow_check',   label: 'Follow Gate',  icon: '👥' },
  { type: 'link',           label: 'Send Link',    icon: '🔗' },
  { type: 'delay',          label: 'Delay',        icon: '⏱️' },
  { type: 'randomizer',     label: 'Randomizer',   icon: '🎲' },
  { type: 'tag',            label: 'Add Tag',      icon: '🏷️' },
  { type: 'remove_tag',     label: 'Remove Tag',   icon: '🗑️' },
  { type: 'collect_email',  label: 'Collect Email',icon: '📧' },
  { type: 'collect_text',   label: 'Collect Text', icon: '📝' },
  { type: 'start_automation','label': 'Start Flow', icon: '▶️' },
  { type: 'end',            label: 'End Flow',     icon: '⏹️' },
]

// ── Config Panel ──────────────────────────────────────────────────
function NodeConfigPanel({ node, onChange, onClose, onDelete }: { node: Node | null; onChange: (data: any) => void; onClose: () => void; onDelete: () => void }) {
  if (!node) return null
  const data = node.data || {}
  const type = data.nodeType || 'message'

  return (
    <div className="flow-panel">
      <div className="flow-panel-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span>Configure Node</span>
        <button className="btn btn-ghost btn-icon" onClick={onClose}><X size={14} /></button>
      </div>
      <div className="flow-panel-body" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, flex: 1, overflowY: 'auto' }}>
          <div className="form-group">
            <label className="form-label">Label (optional)</label>
            <input className="form-input" value={data.label || ''} onChange={(e) => onChange({ ...data, label: e.target.value })} placeholder="Node label" />
          </div>

          {/* Message / Button / Comment Reply */}
          {['message', 'comment_reply', 'button', 'quick_reply', 'collect_email', 'collect_text'].includes(type) && (
            <div className="form-group">
              <label className="form-label">Message text</label>
              <textarea className="form-textarea" value={data.text || ''} onChange={(e) => onChange({ ...data, text: e.target.value })} placeholder="Type your message... Use {{username}} for personalization" />
            </div>
          )}

          {/* Button options */}
          {type === 'button' && (
            <div className="form-group">
              <label className="form-label">Buttons (one per line: Title|PAYLOAD)</label>
              <textarea className="form-textarea" value={(data.buttons || []).map((b: any) => `${b.title}|${b.payload}`).join('\n')} onChange={(e) => {
                const buttons = e.target.value.split('\n').filter(Boolean).map((line: string) => {
                  const [title, payload] = line.split('|')
                  return { title: title?.trim(), payload: payload?.trim() || title?.trim()?.toUpperCase(), type: 'postback' }
                })
                onChange({ ...data, buttons })
              }} placeholder="GET LINK|GET_LINK&#10;I've Followed|FOLLOW_CONFIRMED" />
            </div>
          )}

          {/* Trigger config */}
          {type === 'trigger' && (
            <>
              <div className="form-group">
                <label className="form-label">Match mode</label>
                <select className="form-select" value={data.match_mode || 'any'} onChange={(e) => onChange({ ...data, match_mode: e.target.value })}>
                  <option value="any">Any comment (all comments trigger)</option>
                  <option value="exact">Exact keyword match</option>
                  <option value="contains">Contains keyword</option>
                  <option value="starts_with">Starts with keyword</option>
                </select>
              </div>
              {data.match_mode !== 'any' && (
                <div className="form-group">
                  <label className="form-label">Keywords (comma-separated)</label>
                  <input className="form-input" value={(data.keywords || []).join(', ')} onChange={(e) => onChange({ ...data, keywords: e.target.value.split(',').map((k: string) => k.trim()).filter(Boolean) })} placeholder="LINK, PDF, FREE" />
                </div>
              )}
              <div className="form-group">
                <label className="form-label">Excluded keywords (comma-separated)</label>
                <input className="form-input" value={(data.excluded_keywords || []).join(', ')} onChange={(e) => onChange({ ...data, excluded_keywords: e.target.value.split(',').map((k: string) => k.trim()).filter(Boolean) })} placeholder="spam, bot" />
              </div>
            </>
          )}

          {/* Delay config */}
          {type === 'delay' && (
            <div style={{ display: 'flex', gap: 8 }}>
              <div className="form-group" style={{ flex: 2 }}>
                <label className="form-label">Duration</label>
                <input type="number" className="form-input" value={data.delay_value || 5} min={1} onChange={(e) => onChange({ ...data, delay_value: parseInt(e.target.value) })} />
              </div>
              <div className="form-group" style={{ flex: 3 }}>
                <label className="form-label">Unit</label>
                <select className="form-select" value={data.delay_unit || 'minutes'} onChange={(e) => onChange({ ...data, delay_unit: e.target.value })}>
                  <option value="seconds">Seconds</option>
                  <option value="minutes">Minutes</option>
                  <option value="hours">Hours</option>
                  <option value="days">Days</option>
                </select>
              </div>
            </div>
          )}

          {/* Tag config */}
          {['tag', 'remove_tag'].includes(type) && (
            <div className="form-group">
              <label className="form-label">Tag name</label>
              <input className="form-input" value={data.tag_name || ''} onChange={(e) => onChange({ ...data, tag_name: e.target.value })} placeholder="e.g. LEAD, DOWNLOADED, JEE" />
            </div>
          )}

          {/* Condition config */}
          {type === 'condition' && (
            <>
              <div className="form-group">
                <label className="form-label">Logic</label>
                <select className="form-select" value={data.condition?.logic || 'AND'} onChange={(e) => onChange({ ...data, condition: { ...(data.condition || {}), logic: e.target.value } })}>
                  <option value="AND">ALL conditions must match (AND)</option>
                  <option value="OR">ANY condition must match (OR)</option>
                </select>
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', background: 'var(--bg-hover)', borderRadius: 8, padding: '10px 12px' }}>
                💡 Full condition editor available in the next phase. Currently supports basic branching.
              </div>
            </>
          )}

          {/* Follow check */}
          {type === 'follow_check' && (
            <div style={{ background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: 10, padding: '12px 14px', fontSize: 12, color: 'var(--status-warning)' }}>
              ⚠️ <strong>Important:</strong> Instagram API does not provide real-time follow verification for standard accounts. This node uses a self-reported confirmation button ("I've Followed"). The follow gate will show users a follow prompt and proceed when they confirm.
            </div>
          )}

          {/* Link config */}
          {type === 'link' && (
            <div className="form-group">
              <label className="form-label">Link ID (from Link Manager)</label>
              <input className="form-input" value={data.link_id || ''} onChange={(e) => onChange({ ...data, link_id: e.target.value })} placeholder="Link ID from /links page" />
            </div>
          )}
        </div>
        
        <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--bg-border)' }}>
          <button className="btn btn-danger btn-sm" style={{ width: '100%', display: 'flex', justifyContent: 'center' }} onClick={onDelete}>
            <Trash2 size={14} /> Delete Node
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Main Flow Builder ─────────────────────────────────────────────
let nodeId = 100

function getNewNodeId() {
  return `node-${++nodeId}`
}

const DEFAULT_NODES: Node[] = [
  {
    id: 'trigger-1',
    type: 'custom',
    position: { x: 300, y: 80 },
    data: { nodeType: 'trigger', label: 'Comment Trigger', match_mode: 'any', keywords: [] },
  },
]

function FlowBuilderInner() {
  const { id: automationId } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { addToast } = useToastStore()
  const reactFlowWrapper = useRef<HTMLDivElement>(null)

  const [nodes, setNodes, onNodesChange] = useNodesState(DEFAULT_NODES)
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [automation, setAutomation] = useState<any>(null)
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [saving, setSaving] = useState(false)
  const [showPalette, setShowPalette] = useState(true)

  // Load automation and flow
  useEffect(() => {
    if (!automationId) return
    Promise.all([
      automationsApi.get(automationId),
      automationsApi.getFlow(automationId),
    ]).then(([autoRes, flowRes]) => {
      setAutomation(autoRes.data)
      if (flowRes.data.nodes?.length > 0) {
        setNodes(flowRes.data.nodes)
        setEdges(flowRes.data.edges || [])
      }
    }).catch(() => {
      addToast('error', 'Failed to load automation')
    })
  }, [automationId])

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge({ ...params, animated: true, style: { stroke: 'var(--accent-primary)', strokeWidth: 2 } }, eds)),
    [setEdges]
  )

  const onNodeClick = useCallback((_: any, node: Node) => {
    setSelectedNode(node)
  }, [])

  const onNodeDataChange = useCallback((nodeId: string, newData: any) => {
    setNodes((nds) =>
      nds.map((n) => (n.id === nodeId ? { ...n, data: newData } : n))
    )
    setSelectedNode((prev) => prev?.id === nodeId ? { ...prev, data: newData } : prev)
  }, [setNodes])

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault()
      const type = event.dataTransfer.getData('application/reactflow')
      if (!type) return
      const bounds = reactFlowWrapper.current?.getBoundingClientRect()
      if (!bounds) return
      const position = {
        x: event.clientX - bounds.left - 90,
        y: event.clientY - bounds.top - 30,
      }
      const newNode: Node = {
        id: getNewNodeId(),
        type: 'custom',
        position,
        data: { nodeType: type, label: PALETTE_NODES.find((p) => p.type === type)?.label || type },
      }
      setNodes((nds) => [...nds, newNode])
    },
    [setNodes]
  )

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }, [])

  const handleSave = async () => {
    if (!automationId) return
    setSaving(true)
    try {
      await automationsApi.saveFlow(automationId, {
        nodes: nodes.map((n) => ({
          id: n.id,
          type: n.data.nodeType,
          position: n.position,
          data: n.data,
        })),
        edges: edges.map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          sourceHandle: e.sourceHandle,
          label: e.label,
        })),
      })
      addToast('success', 'Flow saved!')
    } catch {
      addToast('error', 'Failed to save flow')
    } finally {
      setSaving(false)
    }
  }

  const handlePublish = async () => {
    await handleSave()
    try {
      await automationsApi.publish(automationId!)
      addToast('success', 'Automation is now active!')
      setAutomation((a: any) => ({ ...a, status: 'active' }))
    } catch {
      addToast('error', 'Failed to publish')
    }
  }

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-base)' }}>
      {/* ── Top toolbar ── */}
      <div style={{
        height: 56,
        background: 'var(--bg-surface)',
        borderBottom: '1px solid var(--bg-border)',
        display: 'flex',
        alignItems: 'center',
        padding: '0 16px',
        gap: 12,
        zIndex: 10,
      }}>
        <button className="btn btn-ghost btn-icon" onClick={() => navigate('/automations')}>
          <ArrowLeft size={16} />
        </button>
        <div style={{ width: 1, height: 24, background: 'var(--bg-border)' }} />
        <div>
          <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-primary)' }}>
            {automation?.name || 'Loading...'}
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Visual Flow Builder</div>
        </div>

        {automation && (
          <span className={`badge badge-${automation.status}`} style={{ marginLeft: 4 }}>
            {automation.status}
          </span>
        )}

        <div style={{ flex: 1 }} />

        {/* Actions */}
        <button className="btn btn-secondary btn-sm" onClick={() => setShowPalette(!showPalette)}>
          <Settings size={13} /> Nodes
        </button>
        <button className="btn btn-secondary btn-sm" onClick={handleSave} disabled={saving}>
          <Save size={13} /> {saving ? 'Saving...' : 'Save'}
        </button>
        {automation?.status !== 'active' ? (
          <button className="btn btn-primary btn-sm" onClick={handlePublish}>
            <Play size={13} /> Publish
          </button>
        ) : (
          <button className="btn btn-secondary btn-sm" onClick={async () => {
            await automationsApi.pause(automationId!)
            setAutomation((a: any) => ({ ...a, status: 'paused' }))
            addToast('info', 'Automation paused')
          }}>
            <Pause size={13} /> Pause
          </button>
        )}
      </div>

      {/* ── Canvas area ── */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Node Palette */}
        {showPalette && (
          <div style={{
            width: 220,
            background: 'var(--bg-surface)',
            borderRight: '1px solid var(--bg-border)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}>
            <div className="flow-panel-header">Add Nodes</div>
            <div style={{ overflowY: 'auto', padding: 10 }}>
              <div className="node-palette">
                {PALETTE_NODES.map((p) => (
                  <div
                    key={p.type}
                    className="palette-item"
                    draggable
                    onDragStart={(e) => {
                      e.dataTransfer.setData('application/reactflow', p.type)
                      e.dataTransfer.effectAllowed = 'move'
                    }}
                  >
                    <div className="palette-item-icon"><span style={{ fontSize: 16 }}>{p.icon}</span></div>
                    {p.label}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* React Flow canvas */}
        <div ref={reactFlowWrapper} style={{ flex: 1 }} onDrop={onDrop} onDragOver={onDragOver}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onPaneClick={() => setSelectedNode(null)}
            nodeTypes={NODE_TYPES}
            fitView
            defaultEdgeOptions={{
              animated: true,
              style: { stroke: 'var(--accent-primary)', strokeWidth: 2 },
            }}
          >
            <Background variant={BackgroundVariant.Dots} color="var(--bg-border)" gap={20} />
            <Controls style={{ background: 'var(--bg-card)', border: '1px solid var(--bg-border)', borderRadius: 8 }} />
            <MiniMap
              style={{ background: 'var(--bg-card)', border: '1px solid var(--bg-border)' }}
              nodeColor={() => 'var(--accent-primary)'}
            />
            <Panel position="bottom-center">
              <div style={{ background: 'var(--bg-card)', border: '1px solid var(--bg-border)', borderRadius: 20, padding: '6px 16px', fontSize: 11, color: 'var(--text-muted)' }}>
                Drag nodes from the palette • Connect handles to build the flow • Click a node to configure it
              </div>
            </Panel>
          </ReactFlow>
        </div>

        {/* Node config panel */}
        {selectedNode && (
          <NodeConfigPanel
            node={selectedNode}
            onChange={(newData) => onNodeDataChange(selectedNode.id, newData)}
            onClose={() => setSelectedNode(null)}
            onDelete={() => {
              setNodes((nds) => nds.filter((n) => n.id !== selectedNode.id))
              setEdges((eds) => eds.filter((e) => e.source !== selectedNode.id && e.target !== selectedNode.id))
              setSelectedNode(null)
            }}
          />
        )}
      </div>
    </div>
  )
}

export default function FlowBuilderPage() {
  return (
    <ReactFlowProvider>
      <FlowBuilderInner />
    </ReactFlowProvider>
  )
}
