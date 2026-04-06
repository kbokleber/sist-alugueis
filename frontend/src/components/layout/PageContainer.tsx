import type { ReactNode } from 'react'

interface PageContainerProps {
  children: ReactNode
  title?: string
  action?: ReactNode
}

export default function PageContainer({ children, title, action }: PageContainerProps) {
  return (
    <div className="space-y-6">
      {(title || action) && (
        <div className="flex items-center justify-between">
          {title && <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>}
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  )
}
