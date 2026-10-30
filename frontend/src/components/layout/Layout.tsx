import type { ReactNode } from 'react'
import { useMemo } from 'react'
import { Outlet, useNavigate, useLocation, Link } from 'react-router-dom'
import { keycloakEnabled } from '@/auth/keycloak'
import { useAuthStore } from '@/stores/authStore'
import { useUIStore } from '@/stores/uiStore'
import {
  Menu,
  X,
  Home,
  Building,
  TrendingUp,
  TrendingDown,
  Users,
  Tag,
  LogOut,
  History,
  ClipboardList,
  ClipboardCheck,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { isChecklistProfile } from '@/lib/appProfile'

const fullNavItems = [
  { label: 'Dashboard', path: '/dashboard', icon: Home },
  { label: 'Imóveis', path: '/properties', icon: Building },
  { label: 'Receitas', path: '/revenues', icon: TrendingUp },
  { label: 'Despesas', path: '/expenses', icon: TrendingDown },
  { label: 'Conferências', path: '/conferencias', icon: ClipboardCheck },
  { label: 'Categorias', path: '/categories', icon: Tag },
  { label: 'Cat. inventário', path: '/inventory-categories', icon: ClipboardList },
  { label: 'Usuários', path: '/users', icon: Users },
  { label: 'Auditoria', path: '/audit', icon: History },
]

const checklistNavItems = [
  { label: 'Conferências', path: '/conferencias', icon: ClipboardCheck },
]

interface LayoutProps {
  children?: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const { user, logout } = useAuthStore()
  const { sidebarOpen, toggleSidebar } = useUIStore()
  const navigate = useNavigate()
  const location = useLocation()
  const buildAt = import.meta.env.VITE_APP_BUILD_AT
  const rev = (import.meta.env.VITE_APP_VERSION || '').trim()
  const showRev = rev.length > 0 && rev !== 'dev'
  const checklistOnly = isChecklistProfile(user)

  const navItems = useMemo(
    () => (checklistOnly ? checklistNavItems : fullNavItems),
    [checklistOnly]
  )

  const handleLogout = () => {
    logout()
    if (!keycloakEnabled) {
      navigate('/login')
    }
  }

  return (
    <div className="flex h-screen bg-slate-50">
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-30 flex w-64 flex-col bg-slate-900 text-white transition-transform duration-300 lg:static lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-16 items-center justify-between px-4 border-b border-slate-700">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600">
              {checklistOnly ? (
                <ClipboardCheck className="h-4 w-4" />
              ) : (
                <Building className="h-4 w-4" />
              )}
            </div>
            <span className="font-semibold">{checklistOnly ? 'Conferências' : 'Aluguéis'}</span>
          </div>
          <button onClick={toggleSidebar} className="lg:hidden">
            <X className="h-5 w-5" />
          </button>
        </div>

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

        <div className="border-t border-slate-700 p-4">
          <div className="mb-2 text-xs text-slate-400">{user?.email}</div>
          {checklistOnly ? (
            <div className="mb-2 text-[11px] text-slate-500">Perfil: checklist</div>
          ) : null}
          <div className="mb-2 space-y-0.5 text-[11px] leading-snug text-slate-500">
            <div>Compilado em {buildAt}</div>
            {showRev && (
              <div className="font-mono text-[10px] text-slate-600">Rev. {rev}</div>
            )}
          </div>
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-300 hover:bg-slate-800 hover:text-white"
          >
            <LogOut className="h-4 w-4" />
            Sair
          </button>
        </div>
      </aside>

      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/50 lg:hidden"
          onClick={toggleSidebar}
        />
      )}

      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-16 items-center gap-4 border-b border-slate-200 bg-white px-4 lg:px-6">
          <button onClick={toggleSidebar} className="lg:hidden">
            <Menu className="h-5 w-5 text-slate-600" />
          </button>
          <div className="ml-auto flex items-center gap-3">
            <span className="text-sm text-slate-600">{user?.full_name}</span>
          </div>
        </header>

        <main className="flex-1 overflow-auto p-4 lg:p-6">
          {children ?? <Outlet />}
        </main>
      </div>
    </div>
  )
}
