/**
 * Layout — persistent sidebar + topbar wrapper.
 * <Outlet /> renders the current page content.
 */
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { useAuth }  from '@/hooks/useAuth'

const NAV = [
  { to: '/dashboard',    label: 'Dashboard',       icon: '🏠' },
  { to: '/transactions', label: 'Transactions',     icon: '💳' },
  { to: '/upload',       label: 'Upload Statement', icon: '📤' },
  { to: '/analytics',    label: 'Analytics',        icon: '📊' },
  { to: '/insights',     label: 'AI Insights',      icon: '✨', badge: 'AI' },
]

function SidebarContent({ onClose, user, logout }) {
  const navigate = useNavigate()
  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="flex flex-col h-full bg-surface-800 border-r border-surface-600">
      {/* Logo */}
      <div className="flex items-center justify-between px-5 py-[22px]">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-[10px] bg-brand-gradient flex items-center justify-center text-lg">💰</div>
          <span className="font-display font-bold text-[17px] text-text-primary tracking-tight">WealthLens</span>
        </div>
        {onClose && (
          <button onClick={onClose} className="text-text-secondary text-xl md:hidden">✕</button>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2.5 pt-2 space-y-0.5">
        {NAV.map(({ to, label, icon, badge }) => (
          <NavLink key={to} to={to} onClick={onClose}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3.5 py-2.5 rounded-[10px] text-sm font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-brand-green/10 text-brand-green font-semibold'
                  : 'text-text-secondary hover:bg-surface-700 hover:text-text-primary'
              }`
            }
          >
            <span className="text-base">{icon}</span>
            <span>{label}</span>
            {badge && (
              <span className="ml-auto text-[10px] bg-brand-green/20 text-brand-green px-2 py-0.5 rounded-full font-bold">
                {badge}
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      {/* User */}
      <div className="p-2.5 pb-5 border-t border-surface-600">
        <div className="bg-surface-700 rounded-[10px] px-3.5 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-brand-gradient flex items-center justify-center text-xs font-bold text-white">
              {(user?.user_metadata?.name || user?.email || 'U').charAt(0).toUpperCase()}
            </div>
            <div>
              <div className="text-text-primary text-[13px] font-medium truncate max-w-[110px]">
                {user?.user_metadata?.name || user?.email?.split('@')[0]}
              </div>
              <div className="text-text-secondary text-[10px] truncate max-w-[110px]">{user?.email}</div>
            </div>
          </div>
          <button onClick={handleLogout} title="Sign out"
            className="text-text-secondary hover:text-text-primary text-sm px-1 transition-colors">
            ⇥
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Layout() {
  const { user, logout } = useAuth()
  const [mobileOpen, setMobileOpen] = useState(false)
  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'

  return (
    <div className="min-h-screen bg-surface-900 flex">
      {/* Desktop sidebar */}
      <div className="hidden md:flex w-60 shrink-0 h-screen sticky top-0 z-30">
        <div className="w-full"><SidebarContent user={user} logout={logout} /></div>
      </div>

      {/* Mobile sidebar overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-black/70" onClick={() => setMobileOpen(false)} />
          <div className="absolute left-0 top-0 w-72 h-full">
            <SidebarContent onClose={() => setMobileOpen(false)} user={user} logout={logout} />
          </div>
        </div>
      )}

      {/* Main */}
      <div className="flex-1 min-w-0 flex flex-col">
        {/* Topbar */}
        <header className="sticky top-0 z-20 bg-surface-900 border-b border-surface-600 px-6 md:px-8 py-[18px] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => setMobileOpen(true)}
              className="md:hidden text-text-secondary text-2xl mr-1">☰</button>
            <span className="text-text-secondary text-sm">
              {greeting},{' '}
              <span className="text-text-primary font-medium">
                {user?.user_metadata?.name || user?.email?.split('@')[0]} 👋
              </span>
            </span>
          </div>
          <div className="flex items-center gap-3">
            <div className="bg-brand-green/10 border border-brand-green/20 rounded-lg px-3 py-1">
              <span className="text-brand-green text-xs font-medium">● Live</span>
            </div>
            <div className="w-8 h-8 rounded-lg bg-brand-gradient flex items-center justify-center text-xs font-bold text-white">
              {(user?.user_metadata?.name || user?.email || 'U').charAt(0).toUpperCase()}
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-6 md:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
