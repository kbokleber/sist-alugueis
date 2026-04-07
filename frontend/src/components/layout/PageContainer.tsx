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
        <div className="flex items-start justify-between gap-4">
          <div>
            {title && <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>}
            {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  )
}
