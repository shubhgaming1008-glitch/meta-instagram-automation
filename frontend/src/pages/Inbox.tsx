import { useEffect, useState } from 'react'
import { inboxApi } from '@/api/client'
import { Inbox, MessageCircle } from 'lucide-react'

export default function InboxPage() {
  const [conversations, setConversations] = useState<any[]>([])
  const [selected, setSelected] = useState<any>(null)
  const [messages, setMessages] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    inboxApi.conversations({ limit: 50 }).then((r) => setConversations(r.data)).finally(() => setLoading(false))
  }, [])

  const loadMessages = async (conv: any) => {
    setSelected(conv)
    const res = await inboxApi.messages(conv.id)
    setMessages(res.data)
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h1>Inbox</h1>
          <p>Unified view of all DM conversations</p>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 0, background: 'var(--bg-card)', border: '1px solid var(--bg-border)', borderRadius: 14, overflow: 'hidden', height: 600 }}>
        {/* Conversation list */}
        <div style={{ width: 280, borderRight: '1px solid var(--bg-border)', overflow: 'auto' }}>
          <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--bg-border)', fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
            Conversations
          </div>
          {loading ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: 30 }}><div className="spinner" /></div>
          ) : conversations.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)', fontSize: 13 }}>
              No conversations yet
            </div>
          ) : (
            conversations.map((c) => (
              <div
                key={c.id}
                onClick={() => loadMessages(c)}
                style={{
                  padding: '12px 16px',
                  borderBottom: '1px solid var(--bg-border)',
                  cursor: 'pointer',
                  background: selected?.id === c.id ? 'var(--accent-glow)' : 'transparent',
                  transition: 'background 150ms',
                }}
                onMouseEnter={(e) => { if (selected?.id !== c.id) e.currentTarget.style.background = 'var(--bg-hover)' }}
                onMouseLeave={(e) => { if (selected?.id !== c.id) e.currentTarget.style.background = 'transparent' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'linear-gradient(135deg, var(--ig-purple), var(--ig-pink))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700, color: 'white', flexShrink: 0 }}>?</div>
                  <div style={{ flex: 1, overflow: 'hidden' }}>
                    <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-primary)' }}>Contact</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {c.last_message_preview || 'No messages'}
                    </div>
                  </div>
                  {c.unread_count > 0 && <span className="nav-badge">{c.unread_count}</span>}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Message area */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {!selected ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)' }}>
              <Inbox size={40} style={{ marginBottom: 12, opacity: 0.4 }} />
              <div style={{ fontSize: 14, fontWeight: 600 }}>Select a conversation</div>
              <div style={{ fontSize: 12 }}>Click a conversation to view messages</div>
            </div>
          ) : (
            <>
              <div style={{ padding: '12px 20px', borderBottom: '1px solid var(--bg-border)', fontWeight: 700, fontSize: 14 }}>
                Conversation
                {selected.is_automated && <span className="badge badge-info" style={{ marginLeft: 8 }}>Automated</span>}
              </div>
              <div style={{ flex: 1, overflow: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
                {messages.map((msg) => (
                  <div key={msg.id} style={{ display: 'flex', justifyContent: msg.direction === 'out' ? 'flex-end' : 'flex-start' }}>
                    <div style={{
                      maxWidth: '70%',
                      padding: '8px 14px',
                      borderRadius: msg.direction === 'out' ? '14px 14px 4px 14px' : '14px 14px 14px 4px',
                      background: msg.direction === 'out' ? 'var(--accent-primary)' : 'var(--bg-hover)',
                      color: msg.direction === 'out' ? 'white' : 'var(--text-primary)',
                      fontSize: 13,
                    }}>
                      <div>{typeof msg.content === 'object' ? msg.content.text || JSON.stringify(msg.content) : msg.content}</div>
                      <div style={{ fontSize: 10, opacity: 0.7, marginTop: 4 }}>
                        {msg.is_automated && '🤖 '}
                        {msg.sent_at ? new Date(msg.sent_at).toLocaleTimeString() : msg.status}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
