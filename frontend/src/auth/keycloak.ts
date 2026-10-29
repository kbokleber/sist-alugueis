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
const LOGGED_OUT_FLAG = 'kc-logged-out'

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

export function markLoggedOut() {
  sessionStorage.setItem(LOGGED_OUT_FLAG, '1')
}

export function consumeLoggedOutFlag(): boolean {
  const value = sessionStorage.getItem(LOGGED_OUT_FLAG)
  if (value) {
    sessionStorage.removeItem(LOGGED_OUT_FLAG)
    return true
  }
  return false
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
        enableLogging: import.meta.env.DEV,
      }),
      INIT_TIMEOUT_MS,
      'Keycloak init',
    )
      .then((authenticated) => {
        keycloak!.onTokenExpired = () => {
          void keycloak!.updateToken(30).catch(() => {
            markLoggedOut()
            void logoutKeycloak()
          })
        }
        return authenticated
      })
      .catch((err) => {
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
  sessionStorage.removeItem(LOGGED_OUT_FLAG)
  void keycloak.login({
    ...(options?.idpHint ? { idpHint: options.idpHint } : {}),
    redirectUri: `${window.location.origin}/`,
  })
}

export function loginWithGoogle() {
  loginWithKeycloak({ idpHint: 'google' })
}

function buildLogoutUrl(redirectUri: string): string {
  const params = new URLSearchParams({
    client_id: clientId!,
    post_logout_redirect_uri: redirectUri,
  })
  if (keycloak?.idToken) {
    params.set('id_token_hint', keycloak.idToken)
  }
  return `${url!.replace(/\/$/, '')}/realms/${encodeURIComponent(realm!)}/protocol/openid-connect/logout?${params.toString()}`
}

/**
 * Encerra a sessão no Keycloak e redireciona de volta ao app.
 * Usa fallback por URL se keycloak.logout() falhar (comum quando o adapter
 * ainda não tem idToken / post_logout_redirect_uri).
 */
export async function logoutKeycloak(): Promise<void> {
  if (!keycloak || !url || !realm || !clientId) return

  markLoggedOut()
  const redirectUri = `${window.location.origin}/`

  try {
    await initKeycloak()
  } catch {
    // segue com fallback
  }

  try {
    if (keycloak.authenticated || keycloak.idToken) {
      await keycloak.logout({ redirectUri })
      return
    }
  } catch (err) {
    console.warn('[keycloak] logout() falhou, usando URL de logout', err)
  }

  window.location.assign(buildLogoutUrl(redirectUri))
}
