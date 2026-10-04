import { useEffect, useState } from 'react'
import { linksApi } from '@/api/client'
import { useToastStore } from '@/store'
import { Plus, Link2, Copy, Trash2, Shield, Globe } from 'lucide-react'

interface LinkItem {
  id: string
  name: string
  destination_url: string
  token: string
  is_protected: boolean
  status: string
  total_clicks: number
  unique_clicks: number
  expires_at: string | null
  created_at: string
}

export default function LinksPage() {
  const [links, setLinks] = useState<LinkItem[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', destination_url: '', is_protected: false, ig_account_id: '' })
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
      const res = await linksApi.list()
      setLinks(res.data)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!form.name || !form.destination_url) return
    try {
      await linksApi.create(form)
      addToast('success', 'Link created!')
      setShowCreate(false)
      load()
    } catch (e: any) {
      addToast('error', e?.response?.data?.detail || 'Failed to create link')
    }
  }

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete "${name}"?`)) return
    await linksApi.delete(id)
    addToast('success', 'Link deleted')
    load()
  }

  const copyUnlockUrl = (token: string) => {
    navigator.clipboard.writeText(`${window.location.origin}/unlock/${token}`)
    addToast('success', 'Link copied to clipboard!')
  }

  return (
    <div>
      {showCreate && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="card fade-in" style={{ width: 440, padding: 28 }}>
            <h2 style={{ fontWeight: 800, fontSize: 18, marginBottom: 20 }}>Create Link</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div className="form-group">
                <label className="form-label">Link name</label>
                <input className="form-input" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} placeholder='e.g. "JEE Notes PDF"' />
              </div>
              <div className="form-group">
                <label className="form-label">Destination URL</label>
                <input className="form-input" value={form.destination_url} onChange={(e) => setForm((f) => ({ ...f, destination_url: e.target.value }))} placeholder="https://example.com/file.pdf" />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <input type="checkbox" id="is-protected" checked={form.is_protected} onChange={(e) => setForm((f) => ({ ...f, is_protected: e.target.checked }))} />
                <label htmlFor="is-protected" style={{ fontSize: 13, color: 'var(--text-secondary)', cursor: 'pointer' }}>
                  🔒 Protected link (show unlock page instead of direct URL)
                </label>
              </div>
              {accounts.length > 0 && (
                <div className="form-group">
                  <label className="form-label">Instagram Account</label>
                  <select className="form-select" value={form.ig_account_id} onChange={(e) => setForm((f) => ({ ...f, ig_account_id: e.target.value }))}>
                    {accounts.map((a) => <option key={a.id} value={a.id}>@{a.ig_username || a.ig_user_id}</option>)}
                  </select>
                </div>
              )}
              <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
                <button className="btn btn-secondary" onClick={() => setShowCreate(false)} style={{ flex: 1 }}>Cancel</button>
                <button className="btn btn-primary" onClick={handleCreate} style={{ flex: 2 }}>Create Link</button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="page-header">
        <div className="page-header-left">
          <h1>Link Manager</h1>
          <p>Create tracked and protected links for your automations</p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
            <Plus size={15} /> Create Link
          </button>
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Token URL</th>
              <th>Clicks</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} style={{ textAlign: 'center', padding: 40 }}><div className="spinner" style={{ margin: 'auto' }} /></td></tr>
            ) : links.length === 0 ? (
              <tr><td colSpan={6} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>No links yet. Create your first link.</td></tr>
            ) : (
              links.map((link) => (
                <tr key={link.id}>
                  <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{link.name}</td>
                  <td>
                    {link.is_protected
                      ? <span className="badge badge-info"><Shield size={10} /> Protected</span>
                      : <span className="badge badge-draft"><Globe size={10} /> Direct</span>}
                  </td>
                  <td>
                    <code style={{ fontSize: 11, color: 'var(--accent-primary)', background: 'var(--accent-glow)', padding: '2px 8px', borderRadius: 4 }}>
                      /unlock/{link.token.slice(0, 12)}...
                    </code>
                  </td>
                  <td>
                    <span style={{ fontWeight: 600 }}>{link.total_clicks}</span>
                    <span style={{ color: 'var(--text-muted)', fontSize: 11 }}> ({link.unique_clicks} unique)</span>
                  </td>
                  <td><span className={`badge badge-${link.status === 'active' ? 'active' : 'archived'}`}>{link.status}</span></td>
                  <td>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <button className="btn btn-secondary btn-sm btn-icon" onClick={() => copyUnlockUrl(link.token)} title="Copy unlock URL">
                        <Copy size={12} />
                      </button>
                      <button className="btn btn-danger btn-sm btn-icon" onClick={() => handleDelete(link.id, link.name)}>
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
