import { X } from 'lucide-react'
import type { ReactNode } from 'react'

interface FormModalProps {
  open: boolean
  title: string
  description?: string
  children: ReactNode
  onClose: () => void
  /** fullHeight: ideal para formulários longos no celular (checklist) */
  fullHeight?: boolean
  /** Rodapé fixo com ações (ex.: salvar, excluir). */
  footer?: ReactNode
}

export function FormModal({
  open,
  title,
  description,
  children,
  onClose,
  fullHeight = false,
  footer,
}: FormModalProps) {
  if (!open) return null

  return (
    <div
      className={
        fullHeight
          ? 'fixed inset-0 z-50 flex items-stretch justify-center sm:items-center sm:p-4'
          : 'fixed inset-0 z-50 flex items-end justify-center sm:items-center sm:p-4'
      }
    >
      <div className="fixed inset-0 bg-slate-950/50 backdrop-blur-sm" onClick={onClose} />
      <div
        className={
          fullHeight
            ? 'relative z-10 flex h-[100dvh] w-full max-w-3xl flex-col overflow-hidden bg-white shadow-2xl sm:h-auto sm:max-h-[calc(100vh-2rem)] sm:rounded-2xl sm:border sm:border-slate-200'
            : 'relative z-10 flex max-h-[92dvh] w-full max-w-5xl flex-col overflow-hidden rounded-t-2xl border border-slate-200 bg-white shadow-2xl sm:max-h-[calc(100vh-2rem)] sm:rounded-2xl'
        }
      >
        <div className="flex shrink-0 items-start justify-between gap-3 border-b border-slate-200 bg-gradient-to-r from-slate-50 to-slate-100/60 px-4 py-3.5 sm:px-6 sm:py-4">
          <div className="min-w-0 pr-2">
            <h2 className="text-base font-bold tracking-tight text-slate-900 sm:text-lg">{title}</h2>
            {description ? (
              <p className="mt-0.5 text-sm leading-snug text-slate-500">{description}</p>
            ) : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="shrink-0 rounded-xl p-2.5 text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-700"
            aria-label="Fechar"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain bg-slate-100/40 px-4 py-4 sm:px-6 sm:py-5">
          {children}
        </div>
        {footer ? (
          <div className="shrink-0 border-t border-slate-200 bg-slate-50 px-4 py-3 sm:px-6">
            {footer}
          </div>
        ) : null}
      </div>
    </div>
  )
}
