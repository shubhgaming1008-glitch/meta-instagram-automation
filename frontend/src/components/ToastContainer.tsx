import { useToastStore } from '@/store'
import { CheckCircle, XCircle, Info, X } from 'lucide-react'

const icons: Record<string, React.ReactNode> = {
  success: <CheckCircle size={16} color="var(--status-success)" />,
  error:   <XCircle    size={16} color="var(--status-error)" />,
  info:    <Info       size={16} color="var(--status-info)" />,
}

export default function ToastContainer() {
  const { toasts, removeToast } = useToastStore()
  if (!toasts.length) return null
  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <div key={t.id} className={`toast ${t.type}`}>
          {icons[t.type] || icons.info}
          <span style={{ flex: 1 }}>{t.message}</span>
          <button className="btn-ghost" onClick={() => removeToast(t.id)} style={{ padding: 2 }}>
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  )
}
