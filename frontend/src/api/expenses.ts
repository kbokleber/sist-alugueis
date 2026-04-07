import apiClient from './client'
import type { Expense, CreateExpenseRequest } from '@/types/expense.types'
import type { ApiResponse } from '@/types/api.types'

export const expensesApi = {
  list: async (params?: {
    property_id?: string
    category_id?: string
    year_month?: string
    start_month?: string
    end_month?: string
    status?: string
    page?: number
    per_page?: number
  }): Promise<{ data: Expense[]; meta?: ApiResponse<Expense[]>['meta'] }> => {
    const response = await apiClient.get<ApiResponse<Expense[]>>('/expenses', { params })
    return { data: response.data.data, meta: response.data.meta }
  },

  get: async (id: string): Promise<Expense> => {
    const response = await apiClient.get<{ data: Expense }>(`/expenses/${id}`)
    return response.data.data
  },

  create: async (data: CreateExpenseRequest): Promise<Expense> => {
    const response = await apiClient.post<{ data: Expense }>('/expenses', data)
    return response.data.data
  },

  update: async (id: string, data: Partial<CreateExpenseRequest>): Promise<Expense> => {
    const response = await apiClient.put<{ data: Expense }>(`/expenses/${id}`, data)
    return response.data.data
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/expenses/${id}`)
  },

  markPaid: async (id: string): Promise<Expense> => {
    const response = await apiClient.patch<{ data: Expense }>(`/expenses/${id}/pay`, {})
    return response.data.data
  },
}
