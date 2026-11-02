import { cn } from '@/lib/utils'
import type { ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'

interface DetailSheetProps {
  children: ReactNode
  className?: string
}

/** Wrapper de "ficha": blocos de cadastro empilhados com respiro entre eles. */
export function DetailSheet({ children, className }: DetailSheetProps) {
  return <div className={cn('space-y-4', className)}>{children}</div>
}

interface DetailRowProps {
  label: string
  value: ReactNode
  /** Destaca o valor (ex.: valor líquido em destaque). */
  emphasis?: boolean
  valueClassName?: string
  /** Realça a linha com fundo tintado e borda própria. */
  highlight?: boolean
  /** Ocupa as duas colunas da grade (ex.: observações). */
  fullWidth?: boolean
  className?: string
}

/** Campo de cadastro: rótulo acima, valor abaixo. */
export function DetailRow({
  label,
  value,
  emphasis = false,
  valueClassName,
  highlight = false,
  fullWidth = false,
  className,
}: DetailRowProps) {
  return (
    <div
      className={cn(
        'min-w-0',
        fullWidth && 'sm:col-span-2',
        highlight && '-mx-3 rounded-lg bg-primary-50/70 px-3 py-2 ring-1 ring-inset ring-primary-100',
        className
      )}
    >
      <dt className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
        {label}
      </dt>
      <dd
        className={cn(
          'mt-1 break-words leading-snug text-slate-900',
          emphasis ? 'text-base font-bold text-slate-950' : 'text-sm',
          valueClassName
        )}
      >
        {value}
      </dd>
    </div>
  )
}

interface DetailSectionProps {
  title: string
  children: ReactNode
  /** Ícone do cabeçalho da seção. */
  icon?: LucideIcon
  className?: string
}

/** Painel de cadastro: cabeçalho destacado + grade de campos em duas colunas. */
export function DetailSection({ title, children, icon: Icon, className }: DetailSectionProps) {
  return (
    <section
      className={cn(
        'overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm',
        className
      )}
    >
      <header className="flex items-center gap-2.5 border-b border-slate-200 bg-slate-50/80 px-4 py-2.5">
        <span aria-hidden className="h-4 w-[3px] shrink-0 rounded-full bg-primary-600" />
        {Icon ? <Icon className="h-4 w-4 shrink-0 text-primary-600" /> : null}
        <h3 className="text-[11px] font-bold uppercase tracking-[0.14em] text-slate-600">
          {title}
        </h3>
      </header>
      <dl className="grid grid-cols-1 gap-x-8 gap-y-4 px-4 py-4 sm:grid-cols-2">{children}</dl>
    </section>
  )
}
