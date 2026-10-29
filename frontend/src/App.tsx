import { BrowserRouter } from 'react-router-dom'
import { useEffect, useState } from 'react'
import AppRouter from './router/AppRouter'
import { useAuthStore } from './stores/authStore'
import ToastContainer from './components/ui/Toast'
import { authApi } from './api/auth'
import {
  consumeLoggedOutFlag,
  initKeycloak,
  keycloak,
  keycloakEnabled,
  logoutKeycloak,
} from './auth/keycloak'

function BootSplash({ message = 'Carregando…' }: { message?: string }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <div className="text-center text-sm text-slate-500">{message}</div>
    </div>
  )
}

async function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  let timer: number | undefined
  try {
    return await Promise.race([
      promise,
      new Promise<T>((_, reject) => {
        timer = window.setTimeout(() => reject(new Error(`timeout ${ms}ms`)), ms)
      }),
    ])
  } finally {
    if (timer !== undefined) window.clearTimeout(timer)
  }
}

function App() {
  const { token, user, hydrated, logout, setUser, login, authProvider } = useAuthStore()
  const [keycloakReady, setKeycloakReady] = useState(!keycloakEnabled)
  const [bootMessage, setBootMessage] = useState('Carregando…')

  useEffect(() => {
    if (!keycloakEnabled) {
      setKeycloakReady(true)
      return
    }

    let cancelled = false
    setBootMessage('Validando sessão…')

    initKeycloak()
      .then(async (authenticated) => {
        if (cancelled) return

        // Após "Sair", não reacertar sessão SSO residual nesta carga.
        const justLoggedOut = consumeLoggedOutFlag()
        if (justLoggedOut) {
          useAuthStore.setState({
            user: null,
            token: null,
            authProvider: null,
            isAuthenticated: false,
          })
          if (!cancelled) setKeycloakReady(true)
          return
        }

        if (authenticated && keycloak?.token) {
          setBootMessage('Carregando usuário…')
          try {
            login(
              {
                id: '',
                email: (keycloak.tokenParsed?.email as string) || '',
                full_name: (keycloak.tokenParsed?.name as string) || '',
                is_active: true,
                is_superuser: false,
                created_at: '',
                updated_at: null,
              },
              keycloak.token,
              'keycloak',
            )
            const currentUser = await withTimeout(authApi.me(), 15000)
            if (cancelled) return
            setUser(currentUser)
          } catch (err: unknown) {
            const detail = (err as { response?: { data?: { detail?: string }; status?: number } })
              ?.response
            if (detail?.status === 403 && detail.data?.detail === 'Usuário não cadastrado') {
              sessionStorage.setItem('kc-not-registered', 'Usuário não cadastrado')
              useAuthStore.setState({
                user: null,
                token: null,
                authProvider: null,
                isAuthenticated: false,
              })
              void logoutKeycloak()
              return
            }
            console.error('[auth] falha ao carregar /auth/me após Keycloak', err)
            useAuthStore.setState({
              user: null,
              token: null,
              authProvider: null,
              isAuthenticated: false,
            })
          }
        }

        if (!cancelled) setKeycloakReady(true)
      })
      .catch((err) => {
        console.warn('[auth] init Keycloak falhou', err)
        if (!cancelled) setKeycloakReady(true)
      })

    return () => {
      cancelled = true
    }
  }, [login, setUser])

  useEffect(() => {
    if (!hydrated || !keycloakReady) return
    if (!token || user) return
    if (authProvider === 'keycloak') return

    authApi
      .me()
      .then((currentUser) => {
        setUser(currentUser)
      })
      .catch(() => {
        logout()
      })
  }, [hydrated, keycloakReady, token, user, setUser, logout, authProvider])

  if (!hydrated || !keycloakReady) {
    return <BootSplash message={bootMessage} />
  }

  return (
    <>
      <BrowserRouter>
        <AppRouter />
      </BrowserRouter>
      <ToastContainer />
    </>
  )
}

export default App
