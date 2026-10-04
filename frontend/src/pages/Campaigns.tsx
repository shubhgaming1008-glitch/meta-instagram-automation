import { useEffect, useState } from 'react'
import { campaignsApi } from '@/api/client'
import { useToastStore } from '@/store'
import { Plus, Megaphone, Trash2 } from 'lucide-react'

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', description: '', ig_account_id: '' })
  const [accounts, setAccounts] = useState<any[]>([])
  const { addToast } = useToastStore()

  useEffect(() => {
    load()
    import('@/api/client').then(({ instagramApi }) => {
      instagramApi.getAccounts().then((r) => {
        setAccounts(r.data)
        if (r.data.length > 0) setForm((f) => ({ ...f, ig_account_id: r.data[0].id }))
      })
    })
  }, [])

  const load = async () => {
    try {
      const res = await campaignsApi.list()
      setCampaigns(res.data)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!form.name) return
    try {
      await campaignsApi.create(form)
      addToast('success', 'Campaign created!')
      setShowCreate(false)
      load()
    } catch {
      addToast('error', 'Failed to create campaign')
    }
  }

  return (
    <div>
      {showCreate && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="card fade-in" style={{ width: 400, padding: 28 }}>
            <h2 style={{ fontWeight: 800, fontSize: 18, marginBottom: 20 }}>New Campaign</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div className="form-group">
                <label className="form-label">Campaign name</label>
                <input className="form-input" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} placeholder='e.g. "FREE JEE NOTES"' />
              </div>
              <div className="form-group">
                <label className="form-label">Description</label>
                <textarea className="form-textarea" value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} placeholder="Optional description" />
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                <button className="btn btn-secondary" onClick={() => setShowCreate(false)} style={{ flex: 1 }}>Cancel</button>
                <button className="btn btn-primary" onClick={handleCreate} style={{ flex: 2 }}>Create</button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="page-header">
        <div className="page-header-left">
          <h1>Campaigns</h1>
          <p>Group automations under campaigns for unified tracking</p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}><Plus size={15} /> New Campaign</button>
        </div>
      </div>

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}><div className="spinner" /></div>
      ) : campaigns.length === 0 ? (
        <div className="empty-state" style={{ minHeight: 360 }}>
          <div className="empty-state-icon"><Megaphone size={22} /></div>
          <h3>No campaigns yet</h3>
          <p>Group your automations into campaigns to track performance across multiple reels and posts.</p>
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}><Plus size={15} /> Create Campaign</button>
        </div>
      ) : (
        <div className="cards-grid">
          {campaigns.map((c) => (
            <div key={c.id} className="card">
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 4 }}>{c.name}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{c.description || 'No description'}</div>
                </div>
                <button className="btn btn-danger btn-sm btn-icon" onClick={async () => { await campaignsApi.delete(c.id); load() }}><Trash2 size={12} /></button>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--bg-border)' }}>
                {[
                  { label: 'Triggers', value: c.total_triggers },
                  { label: 'DMs', value: c.total_dms_sent },
                  { label: 'Clicks', value: c.total_link_clicks },
                ].map((m) => (
                  <div key={m.label} className="metric-item">
                    <div className="metric-value">{m.value}</div>
                    <div className="metric-label">{m.label}</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
