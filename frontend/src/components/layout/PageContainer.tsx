import type { ReactNode } from 'react'

interface PageContainerProps {
  children: ReactNode
  title?: string
  subtitle?: string
  action?: ReactNode
}

export default function PageContainer({ children, title, subtitle, action }: PageContainerProps) {
  return (
    <div className="space-y-6">
      {(title || action) && (
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            {title && <h1 className="text-xl font-semibold text-slate-900 sm:text-2xl">{title}</h1>}
            {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
          </div>
          {action && <div className="w-full sm:w-auto">{action}</div>}
        </div>
      )}
      {children}
    </div>
  )
}
