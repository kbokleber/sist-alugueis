import { X } from 'lucide-react'
import type { ReactNode } from 'react'

interface FormModalProps {
  open: boolean
  title: string
  description?: string
  children: ReactNode
  onClose: () => void
}

export function FormModal({ open, title, description, children, onClose }: FormModalProps) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-slate-950/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative z-10 w-full max-w-5xl overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl">
        <div className="flex items-start justify-between border-b border-slate-200 bg-slate-50 px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
            {description ? <p className="mt-1 text-sm text-slate-500">{description}</p> : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-200 hover:text-slate-700"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="max-h-[calc(100vh-8rem)] overflow-y-auto px-6 py-5">{children}</div>
      </div>
    </div>
  )
}
