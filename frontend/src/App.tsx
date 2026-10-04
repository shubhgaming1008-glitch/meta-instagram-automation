import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store'

// Layout
import Layout from '@/components/Layout'

// Pages
import LoginPage from '@/pages/auth/LoginPage'
import RegisterPage from '@/pages/auth/RegisterPage'
import DashboardPage from '@/pages/Dashboard'
import AutomationsPage from '@/pages/Automations'
import FlowBuilderPage from '@/pages/FlowBuilder'
import ContactsPage from '@/pages/Contacts'
import ContactDetailPage from '@/pages/ContactDetail'
import InboxPage from '@/pages/Inbox'
import LinksPage from '@/pages/Links'
import CampaignsPage from '@/pages/Campaigns'
import AnalyticsPage from '@/pages/Analytics'
import LogsPage from '@/pages/Logs'
import SettingsPage from '@/pages/Settings'
import UnlockPage from '@/pages/Unlock'
import PostsPage from '@/pages/Posts'
import ToastContainer from '@/components/ToastContainer'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { user, initialized } = useAuthStore()
  if (!initialized) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
        <div className="spinner" />
      </div>
    )
  }
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  const fetchMe = useAuthStore((s) => s.fetchMe)

  useEffect(() => {
    fetchMe()
  }, [fetchMe])

  return (
    <BrowserRouter>
      <ToastContainer />
      <Routes>
        {/* Public */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/unlock/:token" element={<UnlockPage />} />

        {/* Protected */}
        <Route
          path="/"
          element={
            <PrivateRoute>
              <Layout />
            </PrivateRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="automations" element={<AutomationsPage />} />
          <Route path="automations/:id/builder" element={<FlowBuilderPage />} />
          <Route path="contacts" element={<ContactsPage />} />
          <Route path="contacts/:id" element={<ContactDetailPage />} />
          <Route path="inbox" element={<InboxPage />} />
          <Route path="links" element={<LinksPage />} />
          <Route path="campaigns" element={<CampaignsPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="logs" element={<LogsPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="settings/instagram" element={<SettingsPage tab="instagram" />} />
          <Route path="posts" element={<PostsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
