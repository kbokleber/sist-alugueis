import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { getAccessToken, keycloak, keycloakEnabled } from '@/auth/keycloak'
import { useAuthStore } from '@/stores/authStore'

const resolveApiBaseUrl = (): string => {
  const configured = import.meta.env.VITE_API_BASE_URL?.trim()
  const baseUrl = configured || '/api/v1'
  return baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl
}

const BASE_URL = resolveApiBaseUrl()

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const { authProvider, token } = useAuthStore.getState()

    if (keycloakEnabled && (authProvider === 'keycloak' || keycloak?.authenticated)) {
      const kcToken = await getAccessToken()
      if (!kcToken) {
        // Sem token válido: logout completo (inclui Keycloak).
        useAuthStore.getState().logout()
        return Promise.reject(new Error('Sessão Keycloak expirada'))
      }
      if (config.headers) {
        config.headers.Authorization = `Bearer ${kcToken}`
      }
      useAuthStore.getState().setToken(kcToken)
      return config
    }

    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail

    if (status === 403 && detail === 'Usuário não cadastrado') {
      // Encerra SSO no Keycloak (não só limpa localStorage).
      useAuthStore.getState().logout()
      return Promise.reject(error)
    }

    if (status === 401) {
      if (keycloakEnabled) {
        useAuthStore.getState().logout()
      } else {
        useAuthStore.getState().clearLocalSession()
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default apiClient
