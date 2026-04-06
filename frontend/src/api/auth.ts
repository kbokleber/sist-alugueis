import apiClient from './client'
import type { AuthTokens, LoginRequest, RegisterRequest, User } from '@/types/auth.types'

export const authApi = {
  login: async (data: LoginRequest): Promise<AuthTokens> => {
    const response = await apiClient.post<{ data: AuthTokens }>('/auth/login', data)
    return response.data.data
  },

  register: async (data: RegisterRequest): Promise<User> => {
    const response = await apiClient.post<{ data: User }>('/auth/register', data)
    return response.data.data
  },

  me: async (): Promise<User> => {
    const response = await apiClient.get<{ data: User }>('/auth/me')
    return response.data.data
  },

  refresh: async (refreshToken: string): Promise<AuthTokens> => {
    const response = await apiClient.post<{ data: AuthTokens }>('/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data.data
  },
}
