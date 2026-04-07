import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/authStore'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardContent } from '@/components/ui/Card'
import { Building, Eye, EyeOff } from 'lucide-react'

const LAST_LOGIN_STORAGE_KEY = 'last-login-credentials'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login, setUser } = useAuthStore()
  const navigate = useNavigate()

  useEffect(() => {
    const savedCredentials = localStorage.getItem(LAST_LOGIN_STORAGE_KEY)

    if (!savedCredentials) {
      return
    }

    try {
      const parsedCredentials = JSON.parse(savedCredentials) as {
        email?: string
        password?: string
      }

      setEmail(parsedCredentials.email ?? '')
      setPassword(parsedCredentials.password ?? '')
    } catch {
      localStorage.removeItem(LAST_LOGIN_STORAGE_KEY)
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const tokens = await authApi.login({ email, password })
      localStorage.setItem(
        LAST_LOGIN_STORAGE_KEY,
        JSON.stringify({ email, password }),
      )
      login({ id: '', email, full_name: '', is_active: true, is_superuser: false, created_at: '', updated_at: null }, tokens.access_token)
      const currentUser = await authApi.me()
      setUser(currentUser)
      navigate('/dashboard')
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      setError(error.response?.data?.detail || 'Login falhou. Verifique suas credenciais.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 flex flex-col items-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-primary-600 text-white mb-4">
            <Building className="h-7 w-7" />
          </div>
          <h1 className="text-2xl font-semibold text-slate-900">Controle de Aluguéis</h1>
          <p className="mt-1 text-sm text-slate-500">Faça login para continuar</p>
        </div>

        <Card>
          <CardContent className="p-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
                  {error}
                </div>
              )}

              <Input
                id="email"
                type="email"
                label="Email"
                placeholder="seu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />

              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  label="Senha"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-8 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>

              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Entrando...' : 'Entrar'}
              </Button>
            </form>
          </CardContent>
        </Card>

      </div>
    </div>
  )
}
