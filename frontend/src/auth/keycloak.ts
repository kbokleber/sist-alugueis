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
/** Flag durante o fluxo de Sair — Login não deve chamar login() automático. */
export const KC_LOGGING_OUT_FLAG = 'kc-logging-out'
const ID_TOKEN_STORAGE_KEY = 'kc-id-token'

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

export function markLoggingOut() {
  sessionStorage.setItem(KC_LOGGING_OUT_FLAG, '1')
}

export function isLoggingOut(): boolean {
  return sessionStorage.getItem(KC_LOGGING_OUT_FLAG) === '1'
}

export function consumeLoggingOutFlag(): boolean {
  if (!isLoggingOut()) return false
  sessionStorage.removeItem(KC_LOGGING_OUT_FLAG)
  return true
}

function persistIdToken() {
  if (keycloak?.idToken) {
    sessionStorage.setItem(ID_TOKEN_STORAGE_KEY, keycloak.idToken)
  }
}

function readPersistedIdToken(): string | undefined {
  return keycloak?.idToken || sessionStorage.getItem(ID_TOKEN_STORAGE_KEY) || undefined
}

function clearPersistedIdToken() {
  sessionStorage.removeItem(ID_TOKEN_STORAGE_KEY)
}

/** True quando a URL ainda carrega o callback OIDC (code/state) — não disparar login de novo. */
export function isOidcCallback(): boolean {
  const search = new URLSearchParams(window.location.search)
  const hash = new URLSearchParams(window.location.hash.replace(/^#/, ''))
  return (
    search.has('code') ||
    search.has('state') ||
    search.has('error') ||
    hash.has('code') ||
    hash.has('state') ||
    hash.has('error')
  )
}

export function initKeycloak(): Promise<boolean> {
  if (!keycloak) {
    return Promise.resolve(false)
  }
  // Uma única troca de code — evita invalid_code com StrictMode / effects duplicados.
  if (initPromise) {
    return initPromise
  }

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
      if (authenticated) {
        persistIdToken()
      }
      keycloak!.onTokenExpired = () => {
        void keycloak!.updateToken(30).catch(() => {
          logoutKeycloak()
        })
      }
      keycloak!.onAuthSuccess = () => {
        persistIdToken()
      }
      keycloak!.onAuthRefreshSuccess = () => {
        persistIdToken()
      }
      return authenticated
    })
    .catch((err) => {
      console.warn('[keycloak] init falhou ou expirou; seguindo sem SSO silencioso', err)
      // Não zera initPromise se a URL ainda tem code (evita 2ª troca).
      if (!isOidcCallback()) {
        initPromise = null
      }
      return false
    })

  return initPromise
}

export async function getAccessToken(): Promise<string | null> {
  if (!keycloak?.authenticated) {
    return null
  }
  try {
    await keycloak.updateToken(30)
    persistIdToken()
  } catch {
    return null
  }
  return keycloak.token ?? null
}

/** Abre a tela de login do próprio Keycloak (Google / usuário do realm). */
export function loginWithKeycloak(options?: { idpHint?: string }) {
  if (!keycloak) return
  if (isLoggingOut()) return
  if (isOidcCallback()) return
  sessionStorage.removeItem(KC_LOGGING_OUT_FLAG)
  void keycloak.login({
    ...(options?.idpHint ? { idpHint: options.idpHint } : {}),
    redirectUri: `${window.location.origin}/`,
  })
}

export function loginWithGoogle() {
  loginWithKeycloak({ idpHint: 'google' })
}

/**
 * Logout OIDC direto (sem re-init).
 * Limpa estado local só via beforeRedirect, imediatamente antes do replace.
 */
export function logoutKeycloak(beforeRedirect?: () => void): void {
  if (!keycloakEnabled || !url || !realm || !clientId) {
    beforeRedirect?.()
    return
  }

  const idToken = readPersistedIdToken()
  const postLogoutRedirect = `${window.location.origin}/login`
  const params = new URLSearchParams({
    client_id: clientId,
    post_logout_redirect_uri: postLogoutRedirect,
  })
  if (idToken) {
    params.set('id_token_hint', idToken)
  }

  const logoutUrl =
    `${url.replace(/\/$/, '')}/realms/${encodeURIComponent(realm)}` +
    `/protocol/openid-connect/logout?${params.toString()}`

  beforeRedirect?.()
  clearPersistedIdToken()
  window.location.replace(logoutUrl)
}
