export interface Revenue {
  id: string
  user_id: string
  property_id: string
  property_name?: string
  year_month: string
  date: string
  checkin_date: string | null
  checkout_date: string | null
  guest_name: string
  listing_name: string | null
  listing_source: string | null
  nights: number
  gross_amount: number
  cleaning_fee: number
  platform_fee: number
  net_amount: number
  external_id: string | null
  notes: string | null
  created_at: string
  updated_at: string | null
}

export interface CreateRevenueRequest {
  property_id: string
  year_month: string
  date: string
  checkin_date?: string
  checkout_date?: string
  guest_name: string
  listing_name?: string
  listing_source?: string
  nights: number
  gross_amount: number
  cleaning_fee?: number
  platform_fee?: number
  net_amount: number
  external_id?: string
  notes?: string
}
