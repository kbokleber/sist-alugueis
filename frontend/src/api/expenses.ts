import apiClient from './client'
import type { Expense, CreateExpenseRequest, Category } from '@/types/expense.types'

export const expensesApi = {
  list: async (params?: {
    property_id?: string
    category_id?: string
    year_month?: string
    status?: string
  }): Promise<Expense[]> => {
    const response = await apiClient.get<{ data: Expense[] }>('/expenses', { params })
    return response.data.data
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

export const categoriesApi = {
  list: async (): Promise<Category[]> => {
    const response = await apiClient.get<{ data: Category[] }>('/categories')
    return response.data.data
  },

  create: async (data: Partial<Category>): Promise<Category> => {
    const response = await apiClient.post<{ data: Category }>('/categories', data)
    return response.data.data
  },

  update: async (id: string, data: Partial<Category>): Promise<Category> => {
    const response = await apiClient.put<{ data: Category }>(`/categories/${id}`, data)
    return response.data.data
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/categories/${id}`)
  },
}
