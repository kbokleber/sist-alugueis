import apiClient from './client'
import type { Category, CategoryType } from '@/types/expense.types'

export interface CategoryPayload {
  name: string
  type: CategoryType
  color?: string | null
  icon?: string | null
}

export const categoriesApi = {
  list: async (params?: { type?: CategoryType }): Promise<Category[]> => {
    const response = await apiClient.get<{ data: Category[] }>('/categories', { params })
    return response.data.data
  },

  create: async (data: CategoryPayload): Promise<Category> => {
    const response = await apiClient.post<{ data: Category }>('/categories', data)
    return response.data.data
  },

  update: async (id: string, data: Partial<CategoryPayload>): Promise<Category> => {
    const response = await apiClient.put<{ data: Category }>(`/categories/${id}`, data)
    return response.data.data
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/categories/${id}`)
  },
}
