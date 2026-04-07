export interface Property {
  id: string
  user_id: string
  code: string | null
  name: string
  address: string | null
  property_value: number
  monthly_depreciation_percent: number
  is_active: boolean
  created_at: string
  updated_at: string | null
}

export interface CreatePropertyRequest {
  code?: string
  name: string
  address?: string
  property_value: number
  monthly_depreciation_percent?: number
}
