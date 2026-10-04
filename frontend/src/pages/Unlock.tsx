import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Instagram, Lock, ExternalLink, CheckCircle } from 'lucide-react'

export default function UnlockPage() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()
  const [state, setState] = useState<'loading' | 'ready' | 'unlocking' | 'unlocked' | 'error'>('loading')
  const [destination, setDestination] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (!token) return
    fetch(`/api/links/unlock/${token}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.error) {
          setError(data.error)
          setState('error')
        } else {
          setDestination(data.destination_url)
          setState('ready')
        }
      })
      .catch(() => {
        setError('Failed to load link')
        setState('error')
      })
  }, [token])

  const handleUnlock = () => {
    setState('unlocked')
    setTimeout(() => {
      window.location.href = destination
    }, 1500)
  }

  return (
    <div className="auth-page">
      <div className="auth-bg-glow" />
      <div className="auth-card fade-in" style={{ maxWidth: 400, textAlign: 'center' }}>
        {state === 'loading' && (
          <>
            <div className="spinner" style={{ margin: '0 auto 20px', width: 32, height: 32, borderWidth: 3 }} />
            <div style={{ color: 'var(--text-muted)' }}>Loading link...</div>
          </>
        )}

        {state === 'ready' && (
          <>
            <div style={{ width: 64, height: 64, borderRadius: 20, background: 'linear-gradient(135deg, var(--ig-purple), var(--ig-pink))', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px' }}>
              <Lock size={28} color="white" />
            </div>
            <h1 style={{ fontSize: 22, fontWeight: 800, marginBottom: 8 }}>Protected Link</h1>
            <p style={{ color: 'var(--text-muted)', fontSize: 14, marginBottom: 28, lineHeight: 1.6 }}>
              You're about to access a protected link. Click the button below to proceed.
            </p>
            <button className="btn btn-primary btn-lg" onClick={handleUnlock} style={{ width: '100%' }}>
              <ExternalLink size={16} /> Open Link
            </button>
          </>
        )}

        {state === 'unlocked' && (
          <>
            <div style={{ width: 64, height: 64, borderRadius: 20, background: 'rgba(34,197,94,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px' }}>
              <CheckCircle size={28} color="var(--status-success)" />
            </div>
            <h1 style={{ fontSize: 22, fontWeight: 800, marginBottom: 8 }}>Unlocked! ✨</h1>
            <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>Redirecting you now...</p>
          </>
        )}

        {state === 'error' && (
          <>
            <div style={{ width: 64, height: 64, borderRadius: 20, background: 'rgba(239,68,68,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px' }}>
              <Lock size={28} color="var(--status-error)" />
            </div>
            <h1 style={{ fontSize: 22, fontWeight: 800, marginBottom: 8 }}>Link Unavailable</h1>
            <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>{error || 'This link has expired or is no longer available.'}</p>
          </>
        )}
      </div>
    </div>
  )
}
