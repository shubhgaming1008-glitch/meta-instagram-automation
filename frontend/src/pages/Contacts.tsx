import { useEffect, useState } from 'react'
import { contactsApi } from '@/api/client'
import { useNavigate } from 'react-router-dom'
import { Users, Search } from 'lucide-react'

export default function ContactsPage() {
  const [contacts, setContacts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    const t = setTimeout(() => {
      contactsApi.list({ search: search || undefined, limit: 100 }).then((r) => setContacts(r.data)).finally(() => setLoading(false))
    }, 300)
    return () => clearTimeout(t)
  }, [search])

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h1>Contacts</h1>
          <p>Instagram users who have interacted with your automations</p>
        </div>
      </div>

      <div style={{ position: 'relative', maxWidth: 320, marginBottom: 20 }}>
        <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
        <input className="form-input" placeholder="Search by username or email..." value={search} onChange={(e) => setSearch(e.target.value)} style={{ paddingLeft: 32 }} />
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>User</th>
              <th>First Seen</th>
              <th>Last Active</th>
              <th>Email</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} style={{ textAlign: 'center', padding: 40 }}><div className="spinner" style={{ margin: 'auto' }} /></td></tr>
            ) : contacts.length === 0 ? (
              <tr><td colSpan={5}>
                <div className="empty-state" style={{ padding: '40px 0' }}>
                  <div className="empty-state-icon"><Users size={22} /></div>
                  <h3>No contacts yet</h3>
                  <p>Contacts are automatically created when users interact with your automations.</p>
                </div>
              </td></tr>
            ) : contacts.map((c) => (
              <tr key={c.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/contacts/${c.id}`)}>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'linear-gradient(135deg, var(--ig-purple), var(--ig-pink))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700, color: 'white', flexShrink: 0 }}>
                      {(c.username || c.ig_user_id)?.[0]?.toUpperCase()}
                    </div>
                    <div>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: 13 }}>@{c.username || c.ig_user_id}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{c.ig_user_id}</div>
                    </div>
                  </div>
                </td>
                <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>{c.first_interaction_at ? new Date(c.first_interaction_at).toLocaleDateString() : '-'}</td>
                <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>{c.last_interaction_at ? new Date(c.last_interaction_at).toLocaleDateString() : '-'}</td>
                <td style={{ fontSize: 12 }}>{c.email || <span style={{ color: 'var(--text-muted)' }}>-</span>}</td>
                <td><span className={`badge badge-${c.opted_out ? 'archived' : 'active'}`}>{c.opted_out ? 'Opted Out' : 'Active'}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
