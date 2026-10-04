import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'

interface Post {
  id: string
  caption?: string
  media_type: 'IMAGE' | 'VIDEO' | 'CAROUSEL_ALBUM'
  media_url?: string
  thumbnail_url?: string
  permalink: string
  like_count: number
  comments_count: number
  timestamp: string
}

interface IGAccount {
  id: string
  ig_username: string | null
  ig_name: string | null
  page_name: string | null
  is_active: boolean
}

const PRESETS = [
  {
    id: 'link_in_bio',
    emoji: '🔗',
    title: 'Link in Bio',
    desc: 'Jab koi "link" comment kare, seedha DM mein link bhejo',
    keyword: 'link',
    dm: 'Yahan hai tumhara link 👇\n[LINK]',
    commentReply: 'DM check karo! 📩',
  },
  {
    id: 'price_inquiry',
    emoji: '💰',
    title: 'Price/Rate Inquiry',
    desc: 'Jab koi "price" ya "rate" puche, details DM karo',
    keyword: 'price,rate,cost,kitna',
    dm: 'Hmare rates ke baare mein jaanne ke liye DM check karo! 💬',
    commentReply: 'DM kiya hai tumhe! Check karo 📩',
  },
  {
    id: 'giveaway',
    emoji: '🎁',
    title: 'Giveaway Entry',
    desc: 'Giveaway mein "join" likhne walo ko confirm karo',
    keyword: 'join,enter,participate',
    dm: '🎉 Tumhara giveaway entry confirm ho gaya! Winner announce hoga soon.',
    commentReply: 'Entry ho gayi! ✅ DM check karo.',
  },
  {
    id: 'free_resource',
    emoji: '📚',
    title: 'Free Resource / PDF',
    desc: 'Jab koi "free" ya "send" kare, resource DM karo',
    keyword: 'free,send,chahiye,bhejo',
    dm: 'Yahan hai tumhara free resource 🎯\n[LINK]',
    commentReply: 'DM kar diya! Check karo 📩',
  },
  {
    id: 'collab',
    emoji: '🤝',
    title: 'Collaboration Request',
    desc: 'Jab koi "collab" likhhe, contact info DM karo',
    keyword: 'collab,collaboration,partner',
    dm: 'Collab ke liye interested ho? Yahan detail bhejo:\n[EMAIL/FORM LINK]',
    commentReply: 'DM kar diya! Baat karte hai 🙌',
  },
  {
    id: 'custom',
    emoji: '✏️',
    title: 'Custom Automation',
    desc: 'Apni marzi se trigger aur reply set karo',
    keyword: '',
    dm: '',
    commentReply: '',
  },
]

export default function Posts() {
  const navigate = useNavigate()
  const [accounts, setAccounts] = useState<IGAccount[]>([])
  const [selectedAccount, setSelectedAccount] = useState<IGAccount | null>(null)
  const [posts, setPosts] = useState<Post[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [presetPost, setPresetPost] = useState<Post | null>(null) // For preset modal

  useEffect(() => {
    api.get('/instagram/accounts').then(res => {
      const active = res.data.filter((a: IGAccount) => a.is_active)
      setAccounts(active)
      if (active.length > 0) {
        setSelectedAccount(active[0])
      }
    }).catch(() => setError('Instagram account nahi mila. Pehle Settings mein Connect karo.'))
  }, [])

  useEffect(() => {
    if (!selectedAccount) return
    setLoading(true)
    setError(null)
    api.get(`/instagram/accounts/${selectedAccount.id}/posts`)
      .then(res => {
        setPosts(res.data.posts || [])
      })
      .catch(err => {
        const msg = err.response?.data?.detail || 'Posts load karne mein error aaya.'
        setError(msg)
      })
      .finally(() => setLoading(false))
  }, [selectedAccount])

  const handleOpenPreset = (post: Post) => {
    setPresetPost(post)
  }

  const handleSelectPreset = (preset: typeof PRESETS[0], post: Post) => {
    setPresetPost(null)
    const params = new URLSearchParams({
      trigger: 'comment',
      post_id: post.id,
      post_url: post.permalink,
      preset_id: preset.id,
      keyword: preset.keyword,
      dm: preset.dm,
      comment_reply: preset.commentReply,
    })
    navigate(`/automations/new?${params.toString()}`)
  }

  const formatCount = (n: number) => n >= 1000 ? `${(n / 1000).toFixed(1)}K` : String(n)
  const formatDate = (ts: string) => new Date(ts).toLocaleDateString('hi-IN', { day: 'numeric', month: 'short', year: 'numeric' })

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '26px', fontWeight: 700, color: '#fff', margin: 0 }}>
          📱 Posts & Reels
        </h1>
        <p style={{ color: '#aaa', marginTop: '6px', fontSize: '14px' }}>
          Apni posts dekho aur seedha wahan se automation banao
        </p>
      </div>

      {/* Account Selector */}
      {accounts.length > 0 && (
        <div style={{ display: 'flex', gap: '12px', marginBottom: '24px', flexWrap: 'wrap' }}>
          {accounts.map(acc => (
            <button
              key={acc.id}
              onClick={() => setSelectedAccount(acc)}
              style={{
                padding: '8px 18px',
                borderRadius: '20px',
                border: selectedAccount?.id === acc.id ? '2px solid #a855f7' : '2px solid #333',
                background: selectedAccount?.id === acc.id ? 'rgba(168,85,247,0.15)' : 'rgba(255,255,255,0.05)',
                color: selectedAccount?.id === acc.id ? '#a855f7' : '#aaa',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '14px',
                transition: 'all 0.2s',
              }}
            >
              @{acc.ig_username || acc.ig_name || 'Account'}
            </button>
          ))}
        </div>
      )}

      {/* Error State */}
      {error && (
        <div style={{
          background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
          borderRadius: '12px', padding: '20px', color: '#f87171', marginBottom: '24px',
          display: 'flex', alignItems: 'center', gap: '12px'
        }}>
          <span style={{ fontSize: '20px' }}>⚠️</span>
          <div>
            <div style={{ fontWeight: 600 }}>{error}</div>
            {error.includes('Connect') && (
              <button
                onClick={() => navigate('/settings')}
                style={{ marginTop: '8px', background: '#a855f7', border: 'none', borderRadius: '8px', color: '#fff', padding: '6px 14px', cursor: 'pointer', fontSize: '13px' }}
              >
                Settings mein jao →
              </button>
            )}
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} style={{ background: 'rgba(255,255,255,0.05)', borderRadius: '14px', height: '320px', animation: 'pulse 1.5s ease-in-out infinite' }} />
          ))}
        </div>
      )}

      {/* Posts Grid */}
      {!loading && posts.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
          {posts.map(post => {
            const thumb = post.thumbnail_url || post.media_url
            const isReel = post.media_type === 'VIDEO'
            return (
              <div
                key={post.id}
                style={{
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  borderRadius: '14px',
                  overflow: 'hidden',
                  transition: 'transform 0.2s, border-color 0.2s',
                  cursor: 'default',
                }}
                onMouseEnter={e => { (e.currentTarget as HTMLElement).style.transform = 'translateY(-3px)'; (e.currentTarget as HTMLElement).style.borderColor = 'rgba(168,85,247,0.4)' }}
                onMouseLeave={e => { (e.currentTarget as HTMLElement).style.transform = 'translateY(0)'; (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,255,255,0.08)' }}
              >
                {/* Thumbnail */}
                <div style={{ position: 'relative', width: '100%', paddingTop: '100%', background: '#111' }}>
                  {thumb ? (
                    <img
                      src={thumb}
                      alt={post.caption?.slice(0, 40) || 'Post'}
                      style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                  ) : (
                    <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#555', fontSize: '40px' }}>
                      {isReel ? '🎬' : '🖼️'}
                    </div>
                  )}
                  {/* Badge */}
                  <div style={{
                    position: 'absolute', top: '8px', left: '8px',
                    background: isReel ? 'rgba(168,85,247,0.85)' : 'rgba(0,0,0,0.6)',
                    color: '#fff', fontSize: '11px', fontWeight: 700,
                    padding: '3px 8px', borderRadius: '20px', backdropFilter: 'blur(4px)'
                  }}>
                    {isReel ? '🎬 Reel' : post.media_type === 'CAROUSEL_ALBUM' ? '📸 Carousel' : '🖼️ Post'}
                  </div>
                  {/* Open on Instagram */}
                  <a
                    href={post.permalink}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      position: 'absolute', top: '8px', right: '8px',
                      background: 'rgba(0,0,0,0.6)', color: '#fff',
                      borderRadius: '8px', padding: '4px 8px', fontSize: '11px',
                      textDecoration: 'none', backdropFilter: 'blur(4px)',
                      fontWeight: 600,
                    }}
                  >
                    ↗ Instagram
                  </a>
                </div>

                {/* Info */}
                <div style={{ padding: '14px' }}>
                  {/* Caption */}
                  <p style={{ color: '#ccc', fontSize: '13px', margin: '0 0 10px', lineHeight: '1.5', minHeight: '40px' }}>
                    {post.caption ? post.caption.slice(0, 80) + (post.caption.length > 80 ? '...' : '') : <span style={{ color: '#555' }}>No caption</span>}
                  </p>

                  {/* Stats */}
                  <div style={{ display: 'flex', gap: '14px', marginBottom: '14px', color: '#888', fontSize: '13px' }}>
                    <span>❤️ {formatCount(post.like_count)}</span>
                    <span>💬 {formatCount(post.comments_count)}</span>
                    <span style={{ marginLeft: 'auto', fontSize: '11px' }}>{formatDate(post.timestamp)}</span>
                  </div>

                  {/* Automation Button */}
                  <button
                    onClick={() => handleOpenPreset(post)}
                    style={{
                      width: '100%',
                      padding: '9px',
                      background: 'linear-gradient(135deg, #a855f7, #6366f1)',
                      border: 'none',
                      borderRadius: '8px',
                      color: '#fff',
                      fontWeight: 700,
                      fontSize: '13px',
                      cursor: 'pointer',
                      transition: 'opacity 0.2s',
                    }}
                    onMouseEnter={e => (e.currentTarget.style.opacity = '0.85')}
                    onMouseLeave={e => (e.currentTarget.style.opacity = '1')}
                  >
                    ⚡ Automation / Preset lagao
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && posts.length === 0 && selectedAccount && (
        <div style={{ textAlign: 'center', padding: '80px 20px', color: '#555' }}>
          <div style={{ fontSize: '60px', marginBottom: '16px' }}>📭</div>
          <div style={{ fontSize: '18px', fontWeight: 600, color: '#777' }}>Koi post nahi mila</div>
          <div style={{ fontSize: '14px', marginTop: '8px' }}>Is account par koi post nahi hai ya access nahi mila.</div>
        </div>
      )}

      {/* No account connected */}
      {!loading && !error && accounts.length === 0 && (
        <div style={{ textAlign: 'center', padding: '80px 20px' }}>
          <div style={{ fontSize: '60px', marginBottom: '16px' }}>🔗</div>
          <div style={{ fontSize: '18px', fontWeight: 600, color: '#777', marginBottom: '16px' }}>Instagram connect nahi hai</div>
          <button
            onClick={() => navigate('/settings')}
            style={{ background: 'linear-gradient(135deg, #a855f7, #6366f1)', border: 'none', borderRadius: '10px', color: '#fff', padding: '12px 28px', cursor: 'pointer', fontWeight: 700, fontSize: '15px' }}
          >
            Settings mein jaake Connect karo
          </button>
        </div>
      )}

      {/* ── Preset Modal ── */}
      {presetPost && (
        <div
          onClick={() => setPresetPost(null)}
          style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            zIndex: 9999, backdropFilter: 'blur(4px)', padding: '16px',
          }}
        >
          <div
            onClick={e => e.stopPropagation()}
            style={{
              background: '#1a1a2e', border: '1px solid rgba(168,85,247,0.3)',
              borderRadius: '18px', padding: '28px', maxWidth: '560px', width: '100%',
              maxHeight: '85vh', overflowY: 'auto',
            }}
          >
            <div style={{ marginBottom: '20px' }}>
              <h2 style={{ color: '#fff', fontSize: '20px', fontWeight: 700, margin: 0 }}>
                ⚡ Automation Preset chuno
              </h2>
              <p style={{ color: '#888', fontSize: '13px', marginTop: '6px' }}>
                Is post ke liye kaunsa automation lagana chahte ho?
              </p>
              {/* Post preview */}
              <div style={{ background: 'rgba(255,255,255,0.04)', borderRadius: '10px', padding: '10px 14px', marginTop: '12px', display: 'flex', gap: '10px', alignItems: 'center' }}>
                <span style={{ fontSize: '20px' }}>{presetPost.media_type === 'VIDEO' ? '🎬' : '🖼️'}</span>
                <span style={{ color: '#ccc', fontSize: '13px' }}>
                  {presetPost.caption?.slice(0, 60) || 'No caption'}{presetPost.caption && presetPost.caption.length > 60 ? '...' : ''}
                </span>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {PRESETS.map(preset => (
                <button
                  key={preset.id}
                  onClick={() => handleSelectPreset(preset, presetPost)}
                  style={{
                    background: 'rgba(255,255,255,0.04)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '12px', padding: '14px 16px',
                    cursor: 'pointer', textAlign: 'left',
                    transition: 'all 0.2s', color: '#fff',
                  }}
                  onMouseEnter={e => {
                    (e.currentTarget as HTMLElement).style.background = 'rgba(168,85,247,0.15)'
                    ;(e.currentTarget as HTMLElement).style.borderColor = 'rgba(168,85,247,0.5)'
                  }}
                  onMouseLeave={e => {
                    (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.04)'
                    ;(e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,255,255,0.1)'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '22px' }}>{preset.emoji}</span>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '14px' }}>{preset.title}</div>
                      <div style={{ color: '#888', fontSize: '12px', marginTop: '2px' }}>{preset.desc}</div>
                    </div>
                    <span style={{ marginLeft: 'auto', color: '#a855f7', fontSize: '18px' }}>→</span>
                  </div>
                </button>
              ))}
            </div>

            <button
              onClick={() => setPresetPost(null)}
              style={{ marginTop: '16px', width: '100%', padding: '10px', background: 'transparent', border: '1px solid #333', borderRadius: '10px', color: '#888', cursor: 'pointer', fontSize: '13px' }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
