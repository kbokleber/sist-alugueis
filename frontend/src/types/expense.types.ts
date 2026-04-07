export interface Expense {
  id: string
  user_id: string
  is_recurring: boolean
  property_id: string
  property_code?: string
  property_name?: string
  category_id: string
  category_name?: string
  year_month: string
  name: string
  amount: number
  is_reserve: boolean
  due_date: string | null
  paid_date: string | null
  status: 'PENDING' | 'PAID' | 'CANCELLED'
  notes: string | null
  created_at: string
  updated_at: string | null
}

export interface CreateExpenseRequest {
  property_id: string
  category_id: string
  year_month?: string
  name?: string
  amount: number
  is_reserve?: boolean
  due_date?: string
  paid_date?: string
  status?: 'PENDING' | 'PAID' | 'CANCELLED'
  notes?: string
  is_recurring?: boolean
  recurrence_type?: 'MONTHLY' | 'ANNUAL'
  recurrence_start_date?: string
  recurrence_end_date?: string
}

export type CategoryType = 'REVENUE' | 'EXPENSE'

export interface Category {
  id: string
  user_id: string
  name: string
  type: CategoryType
  color: string
  icon: string
  is_system: boolean
  created_at: string
}
