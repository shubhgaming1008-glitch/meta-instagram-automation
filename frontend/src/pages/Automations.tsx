import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { automationsApi } from '@/api/client'
import { Plus, Zap, Play, Pause, Trash2, ExternalLink, Search } from 'lucide-react'
import { useToastStore } from '@/store'

interface Automation {
  id: string
  name: string
  trigger_type: string
  status: string
  total_runs: number
  total_dms_sent: number
  total_link_clicks: number
  updated_at: string
}

const TRIGGER_LABELS: Record<string, { label: string; emoji: string }> = {
  comment:       { label: 'Comment', emoji: '💬' },
  dm_keyword:    { label: 'DM Keyword', emoji: '📩' },
  story_reply:   { label: 'Story Reply', emoji: '📖' },
  story_mention: { label: 'Story Mention', emoji: '@' },
  live_comment:  { label: 'Live Comment', emoji: '🔴' },
  manual:        { label: 'Manual', emoji: '⚡' },
  api:           { label: 'API Trigger', emoji: '🔌' },
}

const TRIGGER_OPTIONS = [
  { value: 'comment', label: '💬 Instagram Comment' },
  { value: 'dm_keyword', label: '📩 DM Keyword' },
  { value: 'story_reply', label: '📖 Story Reply' },
  { value: 'story_mention', label: '@ Story Mention' },
  { value: 'live_comment', label: '🔴 Live Comment' },
  { value: 'manual', label: '⚡ Manual Trigger' },
]

interface CreateModalProps {
  onClose: () => void
  onCreated: (auto: Automation) => void
}

function CreateModal({ onClose, onCreated }: CreateModalProps) {
  const [name, setName] = useState('')
  const [triggerType, setTriggerType] = useState('comment')
  const [igAccountId, setIgAccountId] = useState('')
  const [accounts, setAccounts] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const { addToast } = useToastStore()
  const navigate = useNavigate()

  useEffect(() => {
    import('@/api/client').then(({ instagramApi }) => {
      instagramApi.getAccounts().then((r) => {
        setAccounts(r.data)
        if (r.data.length > 0) setIgAccountId(r.data[0].id)
      }).catch(() => {})
    })
  }, [])

  const handleCreate = async () => {
    if (!name.trim()) return
    if (!igAccountId) {
      addToast('error', 'Please connect an Instagram account first')
      return
    }
    setLoading(true)
    try {
      const res = await automationsApi.create({
        name,
        trigger_type: triggerType,
        ig_account_id: igAccountId,
        trigger_config: { match_mode: 'any', keywords: [] },
      })
      addToast('success', 'Automation created!')
      onCreated(res.data)
      navigate(`/automations/${res.data.id}/builder`)
    } catch {
      addToast('error', 'Failed to create automation')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
      <div className="card fade-in" style={{ width: 440, padding: 28 }}>
        <h2 style={{ fontSize: 18, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 6 }}>New Automation</h2>
        <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 24 }}>Choose a trigger type and name your automation</p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="form-group">
            <label className="form-label">Automation name</label>
            <input className="form-input" value={name} onChange={(e) => setName(e.target.value)} placeholder='e.g. "FREE PDF REEL"' autoFocus />
          </div>

          <div className="form-group">
            <label className="form-label">Trigger type</label>
            <select className="form-select" value={triggerType} onChange={(e) => setTriggerType(e.target.value)}>
              {TRIGGER_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          {accounts.length === 0 ? (
            <div style={{ background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: 10, padding: '12px 16px', fontSize: 12, color: 'var(--status-warning)' }}>
              ⚠️ No Instagram account connected. Go to Settings → Instagram to connect one.
            </div>
          ) : (
            <div className="form-group">
              <label className="form-label">Instagram Account</label>
              <select className="form-select" value={igAccountId} onChange={(e) => setIgAccountId(e.target.value)}>
                {accounts.map((a) => (
                  <option key={a.id} value={a.id}>@{a.ig_username || a.ig_user_id}</option>
                ))}
              </select>
            </div>
          )}

          <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
            <button className="btn btn-secondary" onClick={onClose} style={{ flex: 1 }}>Cancel</button>
            <button className="btn btn-primary" onClick={handleCreate} disabled={loading || !name.trim()} style={{ flex: 2 }}>
              {loading ? <span className="spinner" style={{ width: 14, height: 14 }} /> : '→ Create & Open Builder'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function AutomationsPage() {
  const [automations, setAutomations] = useState<Automation[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')
  const [showCreate, setShowCreate] = useState(false)
  const { addToast } = useToastStore()
  const navigate = useNavigate()

  const loadAutomations = async () => {
    try {
      const res = await automationsApi.list()
      setAutomations(res.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadAutomations() }, [])

  const handleToggle = async (auto: Automation) => {
    try {
      if (auto.status === 'active') {
        await automationsApi.pause(auto.id)
        addToast('info', `"${auto.name}" paused`)
      } else {
        await automationsApi.publish(auto.id)
        addToast('success', `"${auto.name}" is now active`)
      }
      loadAutomations()
    } catch {
      addToast('error', 'Failed to update automation status')
    }
  }

  const handleDelete = async (auto: Automation) => {
    if (!confirm(`Delete "${auto.name}"? This cannot be undone.`)) return
    try {
      await automationsApi.delete(auto.id)
      addToast('success', 'Automation deleted')
      loadAutomations()
    } catch {
      addToast('error', 'Failed to delete automation')
    }
  }

  const filtered = automations.filter((a) => {
    const matchSearch = a.name.toLowerCase().includes(search.toLowerCase())
    const matchFilter = filter === 'all' || a.status === filter
    return matchSearch && matchFilter
  })

  return (
    <div>
      {showCreate && (
        <CreateModal onClose={() => setShowCreate(false)} onCreated={() => loadAutomations()} />
      )}

      <div className="page-header">
        <div className="page-header-left">
          <h1>Automations</h1>
          <p>Build and manage your Instagram automation workflows</p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
            <Plus size={15} /> New Automation
          </button>
        </div>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
        <div style={{ position: 'relative', flex: 1, maxWidth: 320 }}>
          <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            className="form-input"
            placeholder="Search automations..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ paddingLeft: 32 }}
          />
        </div>
        <div className="tabs">
          {['all', 'active', 'draft', 'paused'].map((s) => (
            <button key={s} className={`tab-item${filter === s ? ' active' : ''}`} onClick={() => setFilter(s)}>
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Automation cards */}
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}><div className="spinner" /></div>
      ) : filtered.length === 0 ? (
        <div className="empty-state" style={{ minHeight: 400 }}>
          <div className="empty-state-icon"><Zap size={24} /></div>
          <h3>{search ? 'No results found' : 'No automations yet'}</h3>
          <p>
            {search ? 'Try a different search term.' : 'Create your first automation to start automatically responding to comments and DMs.'}
          </p>
          {!search && (
            <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
              <Plus size={15} /> Create Automation
            </button>
          )}
        </div>
      ) : (
        <div className="cards-grid">
          {filtered.map((auto) => {
            const trigger = TRIGGER_LABELS[auto.trigger_type] || { label: auto.trigger_type, emoji: '⚡' }
            return (
              <div key={auto.id} className="automation-card">
                <div className="automation-card-header">
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <div className={`status-dot ${auto.status}`} />
                      <span className="automation-card-name">{auto.name}</span>
                    </div>
                    <div className="automation-card-trigger">
                      {trigger.emoji} {trigger.label}
                    </div>
                  </div>
                  <span className={`badge badge-${auto.status}`}>{auto.status}</span>
                </div>

                <div className="automation-card-metrics">
                  <div className="metric-item">
                    <div className="metric-value">{auto.total_runs.toLocaleString()}</div>
                    <div className="metric-label">Runs</div>
                  </div>
                  <div className="metric-item">
                    <div className="metric-value">{auto.total_dms_sent.toLocaleString()}</div>
                    <div className="metric-label">DMs</div>
                  </div>
                  <div className="metric-item">
                    <div className="metric-value">{auto.total_link_clicks.toLocaleString()}</div>
                    <div className="metric-label">Clicks</div>
                  </div>
                  <div className="metric-item">
                    <div className="metric-value">
                      {auto.total_runs > 0
                        ? `${Math.round((auto.total_link_clicks / auto.total_runs) * 100)}%`
                        : '-'}
                    </div>
                    <div className="metric-label">Conv.</div>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: 6, marginTop: 14 }}>
                  <button
                    className="btn btn-secondary btn-sm"
                    style={{ flex: 1 }}
                    onClick={() => navigate(`/automations/${auto.id}/builder`)}
                  >
                    <ExternalLink size={12} /> Open Builder
                  </button>
                  <button
                    className={`btn btn-sm ${auto.status === 'active' ? 'btn-secondary' : 'btn-primary'}`}
                    onClick={() => handleToggle(auto)}
                  >
                    {auto.status === 'active' ? <Pause size={12} /> : <Play size={12} />}
                    {auto.status === 'active' ? 'Pause' : 'Activate'}
                  </button>
                  <button className="btn btn-danger btn-sm btn-icon" onClick={() => handleDelete(auto)}>
                    <Trash2 size={12} />
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
