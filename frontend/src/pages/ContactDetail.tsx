import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { contactsApi } from '@/api/client'
import { ArrowLeft, Clock } from 'lucide-react'

const LEVEL_COLORS: Record<string, string> = {
  info: '#3b82f6', warning: '#f59e0b', error: '#ef4444', failed: '#ef4444', retrying: '#f59e0b',
}

export default function ContactDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [contact, setContact] = useState<any>(null)
  const [timeline, setTimeline] = useState<any[]>([])

  useEffect(() => {
    if (!id) return
    Promise.all([contactsApi.get(id), contactsApi.timeline(id)]).then(([c, t]) => {
      setContact(c.data)
      setTimeline(t.data)
    })
  }, [id])

  if (!contact) return <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}><div className="spinner" /></div>

  return (
    <div>
      <button className="btn btn-ghost" onClick={() => navigate('/contacts')} style={{ marginBottom: 16 }}>
        <ArrowLeft size={14} /> Back to Contacts
      </button>

      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 20 }}>
        {/* Contact card */}
        <div className="card" style={{ height: 'fit-content' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: 12, marginBottom: 20 }}>
            <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'linear-gradient(135deg, var(--ig-purple), var(--ig-pink))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24, fontWeight: 800, color: 'white' }}>
              {(contact.username || contact.ig_user_id)?.[0]?.toUpperCase()}
            </div>
            <div>
              <div style={{ fontWeight: 800, fontSize: 16 }}>@{contact.username || contact.ig_user_id}</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{contact.ig_user_id}</div>
            </div>
            <span className={`badge badge-${contact.opted_out ? 'archived' : 'active'}`}>
              {contact.opted_out ? 'Opted Out' : 'Active'}
            </span>
          </div>

          {[
            { label: 'Email', value: contact.email || 'Not collected' },
            { label: 'First seen', value: contact.first_interaction_at ? new Date(contact.first_interaction_at).toLocaleDateString() : '-' },
            { label: 'Last active', value: contact.last_interaction_at ? new Date(contact.last_interaction_at).toLocaleDateString() : '-' },
          ].map((row) => (
            <div key={row.label} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--bg-border)', fontSize: 13 }}>
              <span style={{ color: 'var(--text-muted)' }}>{row.label}</span>
              <span style={{ fontWeight: 600 }}>{row.value}</span>
            </div>
          ))}
        </div>

        {/* Timeline */}
        <div className="card">
          <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 20 }}>Interaction Timeline</div>
          {timeline.length === 0 ? (
            <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 40 }}>No timeline events yet.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
              {timeline.map((event, i) => (
                <div key={event.id} style={{ display: 'flex', gap: 16, paddingBottom: 20, position: 'relative' }}>
                  {i < timeline.length - 1 && (
                    <div style={{ position: 'absolute', left: 11, top: 24, bottom: 0, width: 2, background: 'var(--bg-border)' }} />
                  )}
                  <div style={{ width: 24, height: 24, borderRadius: '50%', background: LEVEL_COLORS[event.level] || 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, flexShrink: 0 }}>
                    ✓
                  </div>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{event.message}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                      {event.category} • {new Date(event.created_at).toLocaleString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
