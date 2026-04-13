export interface ApiResponse<T> {
  data: T
  message?: string
  meta?: {
    page: number
    per_page: number
    total: number
    total_pages?: number
    totals?: {
      total_gross: number
      total_net: number
      total_pending: number
      total_net_after_pending: number
    }
  }
}

export interface PaginatedRequest {
  page?: number
  per_page?: number
  sort?: string
}
