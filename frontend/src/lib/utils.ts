import { clsx, type ClassValue } from 'clsx'

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

export function formatMoney(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value)
}

export function formatDate(dateStr: string): string {
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
    const [year, month, day] = dateStr.split('-').map(Number)
    return new Intl.DateTimeFormat('pt-BR').format(new Date(year, month - 1, day))
  }

  return new Intl.DateTimeFormat('pt-BR').format(new Date(dateStr))
}

export function formatMonth(yearMonth: string): string {
  const [year, month] = yearMonth.split('-')
  const date = new Date(Number(year), Number(month) - 1)
  return new Intl.DateTimeFormat('pt-BR', { month: 'short', year: 'numeric' }).format(date)
}

export function currentYearMonth(): string {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}
