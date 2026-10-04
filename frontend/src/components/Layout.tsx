import { Outlet, NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, Zap, Users, Inbox, Link2, Megaphone,
  BarChart3, ScrollText, Settings, Instagram, LogOut,
  ChevronRight, Bot, Film
} from 'lucide-react'
import { useAuthStore } from '@/store'

const NAV_ITEMS = [
  {
    section: 'Main',
    items: [
      { to: '/dashboard',    icon: LayoutDashboard, label: 'Dashboard' },
      { to: '/automations',  icon: Zap,             label: 'Automations' },
    ],
  },
  {
    section: 'Audience',
    items: [
      { to: '/contacts',     icon: Users,    label: 'Contacts' },
      { to: '/inbox',        icon: Inbox,    label: 'Inbox' },
      { to: '/campaigns',    icon: Megaphone, label: 'Campaigns' },
    ],
  },
  {
    section: 'Content',
    items: [
      { to: '/posts',        icon: Film,     label: 'Posts & Reels' },
      { to: '/links',        icon: Link2,    label: 'Link Manager' },
    ],
  },
  {
    section: 'Insights',
    items: [
      { to: '/analytics',    icon: BarChart3,  label: 'Analytics' },
      { to: '/logs',         icon: ScrollText, label: 'Logs' },
    ],
  },
  {
    section: 'System',
    items: [
      { to: '/settings',     icon: Settings,   label: 'Settings' },
    ],
  },
]

export default function Layout() {
  const { user, logout } = useAuthStore()
  const location = useLocation()

  // Flow builder gets a bare layout (no sidebar, full screen)
  const isFullscreen = location.pathname.includes('/builder')
  if (isFullscreen) return <Outlet />

  return (
    <div className="app-shell">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        {/* Logo */}
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">
            <Instagram size={16} color="white" />
          </div>
          <div>
            <div className="sidebar-logo-text">IGAutomate</div>
            <div className="sidebar-logo-sub">Pro Platform</div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="sidebar-nav">
          {NAV_ITEMS.map((section) => (
            <div key={section.section}>
              <div className="nav-section-label">{section.section}</div>
              {section.items.map(({ to, icon: Icon, label }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
                >
                  <Icon className="nav-item-icon" size={16} />
                  {label}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div className="sidebar-footer">
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '8px 12px',
              borderRadius: 10,
              background: 'var(--bg-hover)',
              marginBottom: 8,
            }}
          >
            <div
              style={{
                width: 28,
                height: 28,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, var(--ig-purple), var(--ig-pink))',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 12,
                fontWeight: 700,
                color: 'white',
                flexShrink: 0,
              }}
            >
              {user?.name?.[0]?.toUpperCase()}
            </div>
            <div style={{ flex: 1, overflow: 'hidden' }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {user?.name}
              </div>
              <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{user?.role}</div>
            </div>
            <button className="btn-ghost btn btn-icon" onClick={logout} title="Logout">
              <LogOut size={14} />
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main content ── */}
      <div className="main-content">
        <div className="page-body fade-in">
          <Outlet />
        </div>
      </div>
    </div>
  )
}
