import apiClient from './client'
import type { User } from '@/types/auth.types'

export interface CreateUserRequest {
  email: string
  password: string
  full_name: string
  is_superuser?: boolean
}

export interface UpdateUserRequest {
  full_name?: string
  is_active?: boolean
  is_superuser?: boolean
}

export interface ChangePasswordRequest {
  current_password?: string
  new_password: string
}

export const usersApi = {
  list: async (): Promise<User[]> => {
    const response = await apiClient.get<{ data: User[] }>('/users')
    return response.data.data
  },

  get: async (id: string): Promise<User> => {
    const response = await apiClient.get<{ data: User }>(`/users/${id}`)
    return response.data.data
  },

  create: async (data: CreateUserRequest): Promise<User> => {
    const response = await apiClient.post<{ data: User }>('/users', data)
    return response.data.data
  },

  update: async (id: string, data: UpdateUserRequest): Promise<User> => {
    const response = await apiClient.put<{ data: User }>(`/users/${id}`, data)
    return response.data.data
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/users/${id}`)
  },

  changePassword: async (id: string, data: ChangePasswordRequest): Promise<void> => {
    await apiClient.patch(`/users/${id}/password`, data)
  },

  toggleActive: async (id: string, is_active: boolean): Promise<User> => {
    const response = await apiClient.put<{ data: User }>(`/users/${id}`, { is_active })
    return response.data.data
  },
}