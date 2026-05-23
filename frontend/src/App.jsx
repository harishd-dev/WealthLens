/**
 * App.jsx — root component with routing and auth guard.
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useAuth }   from '@/hooks/useAuth'

import Layout        from '@/components/shared/Layout'
import LoginPage     from '@/pages/LoginPage'
import SignupPage    from '@/pages/SignupPage'
import ForgotPage    from '@/pages/ForgotPage'
import DashboardPage from '@/pages/DashboardPage'
import TransactionsPage from '@/pages/TransactionsPage'
import UploadPage    from '@/pages/UploadPage'
import AnalyticsPage from '@/pages/AnalyticsPage'
import InsightsPage  from '@/pages/InsightsPage'

/** Redirect unauthenticated users to /login */
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <FullPageSpinner />
  if (!user)   return <Navigate to="/login" replace />
  return children
}

function FullPageSpinner() {
  return (
    <div className="min-h-screen bg-surface-900 flex items-center justify-center">
      <div className="w-10 h-10 border-2 border-brand-green border-t-transparent rounded-full animate-spin" />
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#111827',
            color: '#E8EDF5',
            border: '1px solid #1E2D45',
            fontFamily: "'DM Sans', sans-serif",
          },
          success: { iconTheme: { primary: '#10B981', secondary: '#111827' } },
          error:   { iconTheme: { primary: '#EF4444', secondary: '#111827' } },
        }}
      />
      <Routes>
        {/* Public */}
        <Route path="/login"   element={<LoginPage />}  />
        <Route path="/signup"  element={<SignupPage />} />
        <Route path="/forgot"  element={<ForgotPage />} />

        {/* Protected — wrapped in Layout (sidebar + topbar) */}
        <Route path="/" element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }>
          <Route index            element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard"    element={<DashboardPage />}    />
          <Route path="transactions" element={<TransactionsPage />} />
          <Route path="upload"       element={<UploadPage />}       />
          <Route path="analytics"    element={<AnalyticsPage />}    />
          <Route path="insights"     element={<InsightsPage />}     />
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
