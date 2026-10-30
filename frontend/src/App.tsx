import { BrowserRouter } from 'react-router-dom'
import { useEffect, useRef, useState } from 'react'
import AppRouter from './router/AppRouter'
import { useAuthStore } from './stores/authStore'
import ToastContainer from './components/ui/Toast'
import { authApi } from './api/auth'
import {
  consumeLoggingOutFlag,
  initKeycloak,
  isLoggingOut,
  keycloak,
  keycloakEnabled,
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

/** Garante um único bootstrap Keycloak mesmo com StrictMode (mount → unmount → mount). */
let keycloakBootstrapPromise: Promise<void> | null = null

function App() {
  const { token, user, hydrated, setUser, login, authProvider } = useAuthStore()
  const [keycloakReady, setKeycloakReady] = useState(!keycloakEnabled)
  const [bootMessage, setBootMessage] = useState('Carregando…')
  const bootStarted = useRef(false)

  useEffect(() => {
    if (!keycloakEnabled) {
      setKeycloakReady(true)
      return
    }

    // StrictMode: evita processar o callback OIDC duas vezes neste mount cycle.
    if (bootStarted.current && keycloakBootstrapPromise) {
      void keycloakBootstrapPromise.finally(() => setKeycloakReady(true))
      return
    }
    bootStarted.current = true

    setBootMessage('Validando sessão…')

    keycloakBootstrapPromise = (async () => {
      if (isLoggingOut()) {
        consumeLoggingOutFlag()
        useAuthStore.getState().clearLocalSession()
        return
      }

      const authenticated = await initKeycloak()

      if (isLoggingOut()) {
        consumeLoggingOutFlag()
        useAuthStore.getState().clearLocalSession()
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
              app_profile: 'full',
              created_at: '',
              updated_at: null,
            },
            keycloak.token,
            'keycloak',
          )
          const currentUser = await withTimeout(authApi.me(), 15000)
          setUser(currentUser)
        } catch (err: unknown) {
          const detail = (err as { response?: { data?: { detail?: string }; status?: number } })
            ?.response
          if (detail?.status === 403 && detail.data?.detail === 'Usuário não cadastrado') {
            sessionStorage.setItem('kc-not-registered', 'Usuário não cadastrado')
            useAuthStore.getState().logout()
            return
          }
          console.error('[auth] falha ao carregar /auth/me após Keycloak', err)
          useAuthStore.getState().clearLocalSession()
        }
      }
    })()
      .catch((err) => {
        console.warn('[auth] init Keycloak falhou', err)
      })
      .finally(() => {
        setKeycloakReady(true)
      })
  }, [login, setUser])

  useEffect(() => {
    if (!hydrated || !keycloakReady) return
    if (!token || user) return
    if (authProvider === 'keycloak') return
    if (isLoggingOut()) return

    authApi
      .me()
      .then((currentUser) => {
        setUser(currentUser)
      })
      .catch(() => {
        useAuthStore.getState().clearLocalSession()
      })
  }, [hydrated, keycloakReady, token, user, setUser, authProvider])

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
