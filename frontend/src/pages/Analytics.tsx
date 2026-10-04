import { useEffect, useState } from 'react'
import { analyticsApi } from '@/api/client'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'

export default function AnalyticsPage() {
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(30)

  useEffect(() => {
    analyticsApi.overview({ days }).then((r) => setStats(r.data)).finally(() => setLoading(false))
  }, [days])

  const funnelData = stats ? [
    { name: 'Runs', value: stats.total_runs, fill: '#c44df3' },
    { name: 'DMs Sent', value: stats.dms_sent, fill: '#3b82f6' },
    { name: 'Link Clicks', value: stats.link_clicks, fill: '#22c55e' },
  ] : []

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h1>Analytics</h1>
          <p>Performance metrics across all automations</p>
        </div>
        <div className="page-header-actions">
          <div className="tabs">
            {[7, 30, 90].map((d) => (
              <button key={d} className={`tab-item${days === d ? ' active' : ''}`} onClick={() => setDays(d)}>
                {d}d
              </button>
            ))}
          </div>
        </div>
      </div>

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}><div className="spinner" /></div>
      ) : (
        <>
          <div className="stats-grid" style={{ marginBottom: 28 }}>
            {[
              { label: 'Total Runs', value: stats?.total_runs },
              { label: 'DMs Sent', value: stats?.dms_sent },
              { label: 'Link Clicks', value: stats?.link_clicks },
              { label: 'Contacts', value: stats?.total_contacts },
              { label: 'Failed Jobs', value: stats?.failed_jobs },
              { label: 'Error Rate', value: `${stats?.error_rate}%` },
            ].map((s) => (
              <div key={s.label} className="stat-card">
                <div className="stat-label">{s.label}</div>
                <div className="stat-value">{s.value?.toLocaleString() ?? '-'}</div>
              </div>
            ))}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            <div className="card">
              <div style={{ fontWeight: 700, marginBottom: 20, fontSize: 15 }}>Conversion Funnel</div>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={funnelData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--bg-border)" />
                  <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
                  <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
                  <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--bg-border)', borderRadius: 8 }} />
                  <Bar dataKey="value" fill="var(--accent-primary)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="card">
              <div style={{ fontWeight: 700, marginBottom: 20, fontSize: 15 }}>Performance Summary</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {[
                  { label: 'DM Delivery Rate', value: stats?.total_runs > 0 ? `${Math.round((stats?.dms_sent / stats?.total_runs) * 100)}%` : 'N/A' },
                  { label: 'Click-through Rate', value: stats?.dms_sent > 0 ? `${Math.round((stats?.link_clicks / stats?.dms_sent) * 100)}%` : 'N/A' },
                  { label: 'Total Contacts', value: stats?.total_contacts?.toLocaleString() },
                  { label: 'Error Rate', value: `${stats?.error_rate}%` },
                ].map((row) => (
                  <div key={row.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--bg-border)' }}>
                    <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{row.label}</span>
                    <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{row.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
