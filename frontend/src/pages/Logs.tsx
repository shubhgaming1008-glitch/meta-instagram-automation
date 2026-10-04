import { useEffect, useState } from 'react'
import { logsApi } from '@/api/client'
import { Search, RefreshCw } from 'lucide-react'

const LEVEL_STYLES: Record<string, string> = {
  info: 'badge-info',
  warning: 'badge-paused',
  error: 'badge-failed',
  failed: 'badge-failed',
  retrying: 'badge-paused',
}

export default function LogsPage() {
  const [logs, setLogs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [level, setLevel] = useState('')
  const [category, setCategory] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const res = await logsApi.list({ level: level || undefined, category: category || undefined, limit: 100 })
      setLogs(res.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [level, category])

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h1>Execution Logs</h1>
          <p>Real-time logs for all automation runs, errors, and API calls</p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-secondary" onClick={load}><RefreshCw size={14} /> Refresh</button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
        <select className="form-select" value={level} onChange={(e) => setLevel(e.target.value)} style={{ width: 160 }}>
          <option value="">All levels</option>
          <option value="info">Info</option>
          <option value="warning">Warning</option>
          <option value="error">Error</option>
          <option value="failed">Failed</option>
          <option value="retrying">Retrying</option>
        </select>
        <select className="form-select" value={category} onChange={(e) => setCategory(e.target.value)} style={{ width: 180 }}>
          <option value="">All categories</option>
          <option value="trigger">Trigger</option>
          <option value="message">Message</option>
          <option value="condition">Condition</option>
          <option value="link">Link</option>
          <option value="follow_check">Follow Check</option>
          <option value="delay">Delay</option>
          <option value="tag">Tag</option>
          <option value="system">System</option>
        </select>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Level</th>
              <th>Category</th>
              <th>Message</th>
              <th>Node</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} style={{ textAlign: 'center', padding: 40 }}><div className="spinner" style={{ margin: 'auto' }} /></td></tr>
            ) : logs.length === 0 ? (
              <tr><td colSpan={5} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>No logs yet.</td></tr>
            ) : (
              logs.map((log) => (
                <tr key={log.id}>
                  <td style={{ fontSize: 11, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td><span className={`badge ${LEVEL_STYLES[log.level] || 'badge-draft'}`}>{log.level}</span></td>
                  <td><span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{log.category}</span></td>
                  <td style={{ fontSize: 12, color: 'var(--text-primary)', maxWidth: 400 }}>{log.message}</td>
                  <td><code style={{ fontSize: 10, color: 'var(--text-muted)' }}>{log.node_type || '-'}</code></td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
