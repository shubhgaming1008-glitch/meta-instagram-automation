import { useEffect, useState } from 'react'
import { instagramApi } from '@/api/client'
import { useToastStore } from '@/store'
import { useAuthStore } from '@/store'
import { Instagram, CheckCircle, XCircle, AlertCircle, ExternalLink, Key } from 'lucide-react'

interface SettingsPageProps {
  tab?: string
}

export default function SettingsPage({ tab }: SettingsPageProps) {
  const [activeTab, setActiveTab] = useState(tab || 'instagram')
  const [accounts, setAccounts] = useState<any[]>([])
  const [capabilities, setCapabilities] = useState<Record<string, any>>({})
  const [loading, setLoading] = useState(true)
  const { user } = useAuthStore()
  const { addToast } = useToastStore()

  useEffect(() => {
    instagramApi.getAccounts()
      .then((r) => {
        setAccounts(r.data)
        if (r.data.length > 0) {
          instagramApi.getCapabilities(r.data[0].id).then((cap) => setCapabilities(cap.data.capabilities || {}))
        }
      })
      .finally(() => setLoading(false))
  }, [])

  const handleConnect = async () => {
    try {
      const res = await instagramApi.startOAuth()
      window.location.href = res.data.oauth_url
    } catch (e: any) {
      addToast('error', e?.response?.data?.detail || 'Meta App ID not configured. Add META_APP_ID to .env')
    }
  }

  const handleDisconnect = async (id: string) => {
    if (!confirm('Disconnect this Instagram account?')) return
    await instagramApi.disconnect(id)
    addToast('success', 'Account disconnected')
    setAccounts((a) => a.filter((acc) => acc.id !== id))
  }

  const CAP_LABELS: Record<string, string> = {
    COMMENT_TRIGGER: 'Comment Triggers',
    DM_SEND: 'Send DMs',
    STORY_REPLY_TRIGGER: 'Story Reply Trigger',
    STORY_MENTION_TRIGGER: 'Story Mention Trigger',
    LIVE_COMMENTS: 'Live Comment Triggers',
    FOLLOW_VERIFICATION: 'Follow Verification',
    FOLLOW_TO_DM: 'Follow-to-DM Trigger',
    WEBHOOK: 'Webhook Verified',
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h1>Settings</h1>
          <p>Configure your platform, Instagram connection, and API settings</p>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 20 }}>
        {/* Sidebar tabs */}
        <div style={{ width: 200, flexShrink: 0 }}>
          <div className="card" style={{ padding: 8 }}>
            {[
              { id: 'instagram', label: '📸 Instagram', icon: Instagram },
              { id: 'account', label: '👤 My Account' },
              { id: 'api', label: '🔌 API Config' },
            ].map((t) => (
              <button
                key={t.id}
                className={`nav-item${activeTab === t.id ? ' active' : ''}`}
                onClick={() => setActiveTab(t.id)}
                style={{ width: '100%', textAlign: 'left' }}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tab content */}
        <div style={{ flex: 1 }}>
          {/* ── Instagram Tab ── */}
          {activeTab === 'instagram' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div className="card">
                <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 4 }}>Instagram Connection</div>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 20 }}>
                  Connect a Business or Creator Instagram account via Meta OAuth to enable automations.
                </p>

                {accounts.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '24px 0' }}>
                    <div style={{ width: 56, height: 56, borderRadius: 16, background: 'linear-gradient(135deg, #833ab4, #fd1d1d)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
                      <Instagram size={24} color="white" />
                    </div>
                    <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 6 }}>No account connected</div>
                    <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 20, maxWidth: 360, margin: '0 auto 20px' }}>
                      You'll need a Business or Creator account and a Meta Developer App to connect.
                    </p>
                    <button className="btn btn-primary" onClick={handleConnect}>
                      <Instagram size={15} /> Connect Instagram via Meta OAuth
                    </button>
                  </div>
                ) : (
                  accounts.map((acc) => (
                    <div key={acc.id} style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '14px 16px', background: 'var(--bg-base)', borderRadius: 12 }}>
                      <div style={{ width: 44, height: 44, borderRadius: '50%', background: 'linear-gradient(135deg, #833ab4, #fd1d1d)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, color: 'white', fontWeight: 800 }}>
                        {acc.ig_username?.[0]?.toUpperCase()}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 700 }}>@{acc.ig_username || acc.ig_user_id}</div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{acc.ig_account_type || 'Unknown type'}</div>
                      </div>
                      <span className={`badge badge-${acc.is_active ? 'active' : 'archived'}`}>{acc.is_active ? 'Connected' : 'Disconnected'}</span>
                      <button className="btn btn-danger btn-sm" onClick={() => handleDisconnect(acc.id)}>Disconnect</button>
                    </div>
                  ))
                )}
              </div>

              {/* Capability Matrix */}
              {Object.keys(capabilities).length > 0 && (
                <div className="card">
                  <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 4 }}>API Capability Matrix</div>
                  <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 20 }}>
                    Features available based on your Meta permissions and account type.
                  </p>
                  {Object.entries(capabilities).map(([key, cap]: [string, any]) => (
                    <div key={key} className="capability-row">
                      <div>
                        <div className="capability-name">{CAP_LABELS[key] || key}</div>
                        <div className="capability-reason">{cap.reason}</div>
                      </div>
                      <div className={`capability-status ${cap.enabled ? 'available' : 'unavailable'}`}>
                        {cap.enabled ? <CheckCircle size={14} /> : <XCircle size={14} />}
                        {cap.enabled ? 'Available' : 'Unavailable'}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Setup instructions */}
              <div className="card" style={{ background: 'rgba(59,130,246,0.05)', border: '1px solid rgba(59,130,246,0.2)' }}>
                <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12, color: 'var(--status-info)' }}>📋 Setup Requirements</div>
                <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                  <ol style={{ paddingLeft: 16, display: 'flex', flexDirection: 'column', gap: 6 }}>
                    <li>Create a <strong>Meta Developer App</strong> at <a href="https://developers.facebook.com" target="_blank" rel="noopener" style={{ color: 'var(--accent-primary)' }}>developers.facebook.com</a></li>
                    <li>Add <strong>META_APP_ID</strong> and <strong>META_APP_SECRET</strong> to your <code>.env</code> file</li>
                    <li>Set <strong>META_WEBHOOK_VERIFY_TOKEN</strong> in <code>.env</code></li>
                    <li>Use <strong>ngrok</strong> in development to expose your webhook URL</li>
                    <li>Set callback URL to <code>{window.location.origin}/api/webhooks/meta</code></li>
                    <li>Subscribe to: <code>messages</code>, <code>messaging_postbacks</code>, <code>comments</code></li>
                    <li>Connect a <strong>Business or Creator</strong> Instagram account (not Personal)</li>
                  </ol>
                </div>
              </div>
            </div>
          )}

          {/* ── Account Tab ── */}
          {activeTab === 'account' && (
            <div className="card">
              <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 20 }}>My Account</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14, maxWidth: 400 }}>
                <div className="form-group">
                  <label className="form-label">Name</label>
                  <input className="form-input" value={user?.name || ''} readOnly />
                </div>
                <div className="form-group">
                  <label className="form-label">Email</label>
                  <input className="form-input" value={user?.email || ''} readOnly />
                </div>
                <div className="form-group">
                  <label className="form-label">Role</label>
                  <input className="form-input" value={user?.role || ''} readOnly />
                </div>
              </div>
            </div>
          )}

          {/* ── API Tab ── */}
          {activeTab === 'api' && (
            <div className="card">
              <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 4 }}>API Configuration</div>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 20 }}>
                All sensitive configuration is managed via environment variables. Never edit secrets from the UI.
              </p>
              <div style={{ background: 'var(--bg-hover)', borderRadius: 10, padding: '14px 16px', fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', lineHeight: 2 }}>
                <div>META_APP_ID = {(import.meta as any).env.VITE_META_APP_ID ? '✅ Set' : '❌ Not set'}</div>
                <div>BASE_URL = {window.location.origin}</div>
                <div>WEBHOOK_URL = {window.location.origin}/api/webhooks/meta</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
