import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import Layout from '@/components/layout/Layout'
import LoginPage from '@/pages/LoginPage'
import DashboardPage from '@/pages/DashboardPage'
import PropertiesPage from '@/pages/PropertiesPage'
import PropertyCalendarPage from '@/pages/PropertyCalendarPage'
import PropertyInventoryPage from '@/pages/PropertyInventoryPage'
import InventoryCategoriesPage from '@/pages/InventoryCategoriesPage'
import RevenuesPage from '@/pages/RevenuesPage'
import ExpensesPage from '@/pages/ExpensesPage'
import CategoriesPage from '@/pages/CategoriesPage'
import UsersPage from '@/pages/UsersPage'
import AuditPage from '@/pages/AuditPage'
import ConferencesPage from '@/pages/ConferencesPage'
import { homePathForUser, isChecklistProfile } from '@/lib/appProfile'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <Layout>{children}</Layout>
}

/** Rotas do sistema completo — perfil checklist é redirecionado. */
function FullAccessRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (isChecklistProfile(user)) return <Navigate to="/conferencias" replace />
  return <Layout>{children}</Layout>
}

function HomeRedirect() {
  const { isAuthenticated, user } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <Navigate to={homePathForUser(user)} replace />
}

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<HomeRedirect />} />
      <Route
        path="/conferencias"
        element={
          <ProtectedRoute>
            <ConferencesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard"
        element={
          <FullAccessRoute>
            <DashboardPage />
          </FullAccessRoute>
        }
      />
      <Route
        path="/properties"
        element={
          <FullAccessRoute>
            <PropertiesPage />
          </FullAccessRoute>
        }
      />
      <Route
        path="/properties/:propertyId/calendar"
        element={
          <FullAccessRoute>
            <PropertyCalendarPage />
          </FullAccessRoute>
        }
      />
      <Route
        path="/properties/:propertyId/inventory"
        element={
          <FullAccessRoute>
            <PropertyInventoryPage />
          </FullAccessRoute>
        }
      />
      <Route
        path="/inventory-categories"
        element={
          <FullAccessRoute>
            <InventoryCategoriesPage />
          </FullAccessRoute>
        }
      />
      <Route
        path="/revenues"
        element={
          <FullAccessRoute>
            <RevenuesPage />
          </FullAccessRoute>
        }
      />
      <Route
        path="/expenses"
        element={
          <FullAccessRoute>
            <ExpensesPage />
          </FullAccessRoute>
        }
      />
      <Route
        path="/categories"
        element={
          <FullAccessRoute>
            <CategoriesPage />
          </FullAccessRoute>
        }
      />
      <Route
        path="/users"
        element={
          <FullAccessRoute>
            <UsersPage />
          </FullAccessRoute>
        }
      />
      <Route
        path="/audit"
        element={
          <FullAccessRoute>
            <AuditPage />
          </FullAccessRoute>
        }
      />
      <Route path="*" element={<HomeRedirect />} />
    </Routes>
  )
}
