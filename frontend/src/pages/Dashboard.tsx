import { useEffect, useState } from 'react'
import { analyticsApi, automationsApi, instagramApi } from '@/api/client'
import {
  Zap, MessageCircle, Link2, Users, TrendingUp,
  AlertCircle, Play, Plus, ChevronRight, Instagram
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'

interface Stats {
  total_automations: number
  active_automations: number
  total_runs: number
  dms_sent: number
  link_clicks: number
  total_contacts: number
  failed_jobs: number
  error_rate: number
}

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

const TRIGGER_LABELS: Record<string, string> = {
  comment:      '💬 Comment',
  dm_keyword:   '📩 DM Keyword',
  story_reply:  '📖 Story Reply',
  live_comment: '🔴 Live Comment',
  manual:       '⚡ Manual',
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [automations, setAutomations] = useState<Automation[]>([])
  const [loading, setLoading] = useState(true)
  const [hasAccount, setHasAccount] = useState<boolean | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    const load = async () => {
      try {
        const [statsRes, autoRes, accRes] = await Promise.allSettled([
          analyticsApi.overview({ days: 30 }),
          automationsApi.list(),
          instagramApi.getAccounts(),
        ])
        if (statsRes.status === 'fulfilled') setStats(statsRes.value.data)
        if (autoRes.status === 'fulfilled') setAutomations(autoRes.value.data.slice(0, 5))
        if (accRes.status === 'fulfilled') setHasAccount(accRes.value.data.length > 0)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const STAT_CARDS = [
    { label: 'Automations', value: stats?.total_automations ?? '-', icon: Zap, color: '#c44df3', sub: `${stats?.active_automations ?? 0} active` },
    { label: 'DMs Sent', value: stats?.dms_sent ?? '-', icon: MessageCircle, color: '#3b82f6', sub: 'Last 30 days' },
    { label: 'Link Clicks', value: stats?.link_clicks ?? '-', icon: Link2, color: '#22c55e', sub: 'Last 30 days' },
    { label: 'Contacts', value: stats?.total_contacts ?? '-', icon: Users, color: '#f59e0b', sub: 'Total' },
    { label: 'Runs', value: stats?.total_runs ?? '-', icon: TrendingUp, color: '#8b5cf6', sub: 'Last 30 days' },
    { label: 'Error Rate', value: stats ? `${stats.error_rate}%` : '-', icon: AlertCircle, color: '#ef4444', sub: 'Last 30 days' },
  ]

  return (
    <div>
      {/* Header */}
      <div className="page-header">
        <div className="page-header-left">
          <h1>Dashboard <span className="gradient-text">Overview</span></h1>
          <p>Last 30 days performance across all automations</p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-primary" onClick={() => navigate('/automations')}>
            <Plus size={15} /> New Automation
          </button>
        </div>
      </div>

      {/* No Instagram account banner */}
      {hasAccount === false && (
        <div
          className="card"
          style={{
            background: 'linear-gradient(135deg, rgba(131,58,180,0.15), rgba(253,29,29,0.08))',
            border: '1px solid rgba(196,77,243,0.3)',
            display: 'flex',
            alignItems: 'center',
            gap: 16,
            marginBottom: 24,
          }}
        >
          <div style={{ width: 44, height: 44, borderRadius: 12, background: 'linear-gradient(135deg, #833ab4, #fd1d1d)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <Instagram size={22} color="white" />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: 14 }}>Connect your Instagram account</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
              Connect a Business or Creator account to start automating comments and DMs.
            </div>
          </div>
          <button className="btn btn-primary" onClick={() => navigate('/settings')}>
            Connect Instagram <ChevronRight size={14} />
          </button>
        </div>
      )}

      {/* Stats Grid */}
      <div className="stats-grid" style={{ marginBottom: 28 }}>
        {STAT_CARDS.map((card) => (
          <div key={card.label} className="stat-card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <span className="stat-label">{card.label}</span>
              <div style={{ width: 32, height: 32, borderRadius: 8, background: `${card.color}20`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <card.icon size={15} color={card.color} />
              </div>
            </div>
            {loading ? (
              <div style={{ height: 32, background: 'var(--bg-hover)', borderRadius: 6, animation: 'pulse 1.5s ease infinite' }} />
            ) : (
              <div className="stat-value">{card.value?.toLocaleString()}</div>
            )}
            <div className="stat-label" style={{ marginTop: 6 }}>{card.sub}</div>
          </div>
        ))}
      </div>

      {/* Recent Automations */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 20 }}>
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <div style={{ fontWeight: 700, fontSize: 15, color: 'var(--text-primary)' }}>Recent Automations</div>
            <button className="btn btn-ghost btn-sm" onClick={() => navigate('/automations')}>
              View all <ChevronRight size={13} />
            </button>
          </div>

          {automations.length === 0 && !loading ? (
            <div className="empty-state" style={{ padding: '32px 0' }}>
              <div className="empty-state-icon"><Zap size={22} /></div>
              <h3>No automations yet</h3>
              <p>Create your first automation to start engaging your Instagram audience automatically.</p>
              <button className="btn btn-primary" onClick={() => navigate('/automations')}>
                <Plus size={15} /> Create Automation
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {automations.map((auto) => (
                <div
                  key={auto.id}
                  style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 12px', borderRadius: 10, background: 'var(--bg-base)', cursor: 'pointer', transition: 'background 150ms' }}
                  onClick={() => navigate(`/automations/${auto.id}/builder`)}
                  onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-hover)')}
                  onMouseLeave={(e) => (e.currentTarget.style.background = 'var(--bg-base)')}
                >
                  <div className={`status-dot ${auto.status}`} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-primary)' }}>{auto.name}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 1 }}>
                      {TRIGGER_LABELS[auto.trigger_type] || auto.trigger_type}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 16, fontSize: 12, color: 'var(--text-muted)' }}>
                    <span title="Runs">⚡ {auto.total_runs}</span>
                    <span title="DMs">💬 {auto.total_dms_sent}</span>
                    <span title="Clicks">🔗 {auto.total_link_clicks}</span>
                  </div>
                  <span className={`badge badge-${auto.status}`}>{auto.status}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="card" style={{ height: 'fit-content' }}>
          <div style={{ fontWeight: 700, fontSize: 15, color: 'var(--text-primary)', marginBottom: 16 }}>Quick Actions</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {[
              { label: 'New Comment Automation', icon: '💬', path: '/automations', trigger: 'comment' },
              { label: 'New DM Keyword Bot',     icon: '📩', path: '/automations', trigger: 'dm_keyword' },
              { label: 'Create Protected Link',   icon: '🔒', path: '/links' },
              { label: 'View Analytics',          icon: '📊', path: '/analytics' },
              { label: 'Instagram Settings',      icon: '⚙️', path: '/settings' },
            ].map((action) => (
              <button
                key={action.label}
                className="btn btn-secondary"
                onClick={() => navigate(action.path)}
                style={{ justifyContent: 'flex-start', gap: 10 }}
              >
                <span>{action.icon}</span>
                <span>{action.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
