import { cn } from '@/lib/utils'

export function isChecklistCompleted(status?: string | null): boolean {
  return status === 'completed'
}

/** Amarelo = pendente · Verde = ok · Vermelho = intercorrência */
export function checklistActionButtonClass(
  done: boolean,
  hasIncidents: boolean,
  size: 'md' | 'sm' = 'md'
) {
  return cn(
    'border-transparent shadow-sm text-white',
    size === 'md' ? 'h-12 w-full text-base' : 'h-8',
    hasIncidents
      ? '!bg-red-600 hover:!bg-red-700 focus:!ring-red-500'
      : done
        ? '!bg-emerald-600 hover:!bg-emerald-700 focus:!ring-emerald-500'
        : '!bg-amber-500 hover:!bg-amber-600 focus:!ring-amber-500'
  )
}

export function checklistActionLabel(
  label: string,
  done: boolean,
  hasIncidents: boolean
): string {
  if (hasIncidents) return `${label} · intercorrência`
  if (done) return `${label} ok`
  return label
}

export function checklistPerformedByLabel(name?: string | null): string | null {
  const trimmed = name?.trim()
  return trimmed ? `Por ${trimmed}` : null
}
