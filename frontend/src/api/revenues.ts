import apiClient from './client'
import type { Revenue, CreateRevenueRequest } from '@/types/revenue.types'

export const revenuesApi = {
  list: async (params?: { property_id?: string; year_month?: string }): Promise<Revenue[]> => {
    const response = await apiClient.get<{ data: Revenue[] }>('/revenues', { params })
    return response.data.data
  },

  get: async (id: string): Promise<Revenue> => {
    const response = await apiClient.get<{ data: Revenue }>(`/revenues/${id}`)
    return response.data.data
  },

  create: async (data: CreateRevenueRequest): Promise<Revenue> => {
    const response = await apiClient.post<{ data: Revenue }>('/revenues', data)
    return response.data.data
  },

  update: async (id: string, data: Partial<CreateRevenueRequest>): Promise<Revenue> => {
    const response = await apiClient.put<{ data: Revenue }>(`/revenues/${id}`, data)
    return response.data.data
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/revenues/${id}`)
  },
}
