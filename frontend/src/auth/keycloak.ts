import Keycloak from 'keycloak-js'

const url = import.meta.env.VITE_KEYCLOAK_URL?.trim()
const realm = import.meta.env.VITE_KEYCLOAK_REALM?.trim()
const clientId = import.meta.env.VITE_KEYCLOAK_CLIENT_ID?.trim()

export const keycloakEnabled = Boolean(url && realm && clientId)

export const keycloak: Keycloak | null = keycloakEnabled
  ? new Keycloak({ url: url!, realm: realm!, clientId: clientId! })
  : null

let initPromise: Promise<boolean> | null = null

const INIT_TIMEOUT_MS = 5000

function withTimeout<T>(promise: Promise<T>, ms: number, label: string): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const timer = window.setTimeout(() => {
      reject(new Error(`${label} timed out after ${ms}ms`))
    }, ms)
    promise
      .then((value) => {
        window.clearTimeout(timer)
        resolve(value)
      })
      .catch((err) => {
        window.clearTimeout(timer)
        reject(err)
      })
  })
}

export function initKeycloak(): Promise<boolean> {
  if (!keycloak) {
    return Promise.resolve(false)
  }
  if (!initPromise) {
    initPromise = withTimeout(
      keycloak.init({
        onLoad: 'check-sso',
        pkceMethod: 'S256',
        checkLoginIframe: false,
        silentCheckSsoRedirectUri: `${window.location.origin}/silent-check-sso.html`,
        // Evita ficar preso se o iframe silencioso for bloqueado (3rd-party cookies / redirect URI).
        enableLogging: import.meta.env.DEV,
      }),
      INIT_TIMEOUT_MS,
      'Keycloak init',
    )
      .then((authenticated) => {
        keycloak!.onTokenExpired = () => {
          void keycloak!.updateToken(30).catch(() => {
            void keycloak!.logout({ redirectUri: `${window.location.origin}/login` })
          })
        }
        return authenticated
      })
      .catch((err) => {
        // Permite retry em hot-reload; não deixa a UI branca.
        console.warn('[keycloak] init falhou ou expirou; seguindo sem SSO silencioso', err)
        initPromise = null
        return false
      })
  }
  return initPromise
}

export async function getAccessToken(): Promise<string | null> {
  if (!keycloak?.authenticated) {
    return null
  }
  try {
    await keycloak.updateToken(30)
  } catch {
    return null
  }
  return keycloak.token ?? null
}

/** Abre a tela de login do próprio Keycloak (Google / usuário do realm). */
export function loginWithKeycloak(options?: { idpHint?: string }) {
  if (!keycloak) return
  void keycloak.login({
    ...(options?.idpHint ? { idpHint: options.idpHint } : {}),
    redirectUri: `${window.location.origin}/`,
  })
}

export function loginWithGoogle() {
  loginWithKeycloak({ idpHint: 'google' })
}

export function logoutKeycloak() {
  if (!keycloak) return
  void keycloak.logout({ redirectUri: `${window.location.origin}/` })
}
