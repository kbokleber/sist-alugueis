import apiClient from './client'
import type { Revenue, CreateRevenueRequest } from '@/types/revenue.types'
import type { ApiResponse } from '@/types/api.types'

export const revenuesApi = {
  list: async (params?: {
    property_id?: string
    year_month?: string
    start_month?: string
    end_month?: string
    external_id?: string
    page?: number
    per_page?: number
  }): Promise<{ data: Revenue[]; meta?: ApiResponse<Revenue[]>['meta'] }> => {
    const response = await apiClient.get<ApiResponse<Revenue[]>>('/revenues', { params })
    return { data: response.data.data, meta: response.data.meta }
  },

  calendar: async (params: {
    property_id: string
    start_date: string
    end_date: string
  }): Promise<Revenue[]> => {
    const response = await apiClient.get<ApiResponse<Revenue[]>>('/revenues/calendar', { params })
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
