import apiClient from './client'
import type { Property, CreatePropertyRequest } from '@/types/property.types'

export const propertiesApi = {
  list: async (): Promise<Property[]> => {
    const response = await apiClient.get<{ data: Property[] }>('/properties')
    return response.data.data
  },

  get: async (id: string): Promise<Property> => {
    const response = await apiClient.get<{ data: Property }>(`/properties/${id}`)
    return response.data.data
  },

  create: async (data: CreatePropertyRequest): Promise<Property> => {
    const response = await apiClient.post<{ data: Property }>('/properties', data)
    return response.data.data
  },

  update: async (id: string, data: Partial<CreatePropertyRequest>): Promise<Property> => {
    const response = await apiClient.put<{ data: Property }>(`/properties/${id}`, data)
    return response.data.data
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/properties/${id}`)
  },
}
