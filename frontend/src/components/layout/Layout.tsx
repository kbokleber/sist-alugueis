import { Outlet, useNavigate, useLocation, Link } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { useUIStore } from '@/stores/uiStore'
import { Menu, X, Home, Building, TrendingUp, TrendingDown, PieChart, Users, Settings, LogOut, History } from 'lucide-react'
import { cn } from '@/lib/utils'

const navItems = [
  { label: 'Dashboard', path: '/dashboard', icon: Home },
  { label: 'Imóveis', path: '/properties', icon: Building },
  { label: 'Receitas', path: '/revenues', icon: TrendingUp },
  { label: 'Despesas', path: '/expenses', icon: TrendingDown },
  { label: 'Fechamento', path: '/closing', icon: PieChart },
  { label: 'Usuários', path: '/users', icon: Users },
  { label: 'Auditoria', path: '/audit', icon: History },
]

export default function Layout() {
  const { user, logout } = useAuthStore()
  const { sidebarOpen, toggleSidebar } = useUIStore()
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-slate-50">
      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-30 flex w-64 flex-col bg-slate-900 text-white transition-transform duration-300 lg:static lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Logo */}
        <div className="flex h-16 items-center justify-between px-4 border-b border-slate-700">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600">
              <Building className="h-4 w-4" />
            </div>
            <span className="font-semibold">Aluguéis</span>
          </div>
          <button onClick={toggleSidebar} className="lg:hidden">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 space-y-1 px-3 py-4">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                location.pathname.startsWith(item.path)
                  ? 'bg-primary-600 text-white'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          ))}
        </nav>

        {/* Footer */}
        <div className="border-t border-slate-700 p-4">
          <div className="mb-2 text-xs text-slate-400">{user?.email}</div>
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-300 hover:bg-slate-800 hover:text-white"
          >
            <LogOut className="h-4 w-4" />
            Sair
          </button>
        </div>
      </aside>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/50 lg:hidden"
          onClick={toggleSidebar}
        />
      )}

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex h-16 items-center gap-4 border-b border-slate-200 bg-white px-4 lg:px-6">
          <button onClick={toggleSidebar} className="lg:hidden">
            <Menu className="h-5 w-5 text-slate-600" />
          </button>
          <div className="ml-auto flex items-center gap-3">
            <span className="text-sm text-slate-600">{user?.full_name}</span>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
