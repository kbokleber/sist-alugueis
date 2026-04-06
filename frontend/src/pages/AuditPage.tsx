import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { auditApi, type AuditLog } from '@/api/audit'
import { usersApi } from '@/api/users'
import PageContainer from '@/components/layout/PageContainer'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { toast } from '@/stores/toastStore'
import { Loader2, ChevronLeft, ChevronRight, Filter, History, User, Calendar } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { User as UserType } from '@/types/auth.types'

const ACTION_COLORS: Record<string, string> = {
  CREATE: 'bg-green-100 text-green-700 border-green-200',
  UPDATE: 'bg-blue-100 text-blue-700 border-blue-200',
  DELETE: 'bg-red-100 text-red-700 border-red-200',
}

const ENTITY_TYPES = [
  { value: '', label: 'Todos' },
  { value: 'property', label: 'Imóvel' },
  { value: 'revenue', label: 'Receita' },
  { value: 'expense', label: 'Despesa' },
  { value: 'category', label: 'Categoria' },
  { value: 'user', label: 'Usuário' },
  { value: 'closing', label: 'Fechamento' },
]

const ACTIONS = ['CREATE', 'UPDATE', 'DELETE']

export default function AuditPage() {
  const [entityType, setEntityType] = useState('')
  const [page, setPage] = useState(1)
  const [expandedLog, setExpandedLog] = useState<string | null>(null)
  const perPage = 20

  const { data: users = [] } = useQuery({
    queryKey: ['users'],
    queryFn: usersApi.list,
  })

  const { data, isLoading, isError } = useQuery({
    queryKey: ['audit-logs', entityType, page],
    queryFn: () => auditApi.list({ entity_type: entityType || undefined, page, per_page: perPage }),
  })

  const logs = data?.data || []
  const meta = data?.meta || { total: 0, page: 1, per_page: perPage, total_pages: 1 }

  const getUserName = (userId: string | null): string => {
    if (!userId) return 'Sistema'
    const user = users.find((u: UserType) => u.id === userId)
    return user?.full_name || user?.email || userId
  }

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr)
    return date.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const formatValue = (key: string, value: unknown): string => {
    if (value === null || value === undefined) return 'N/A'
    if (typeof value === 'object') return JSON.stringify(value)
    if (key.includes('date') || key.includes('_at')) {
      try {
        return formatDate(String(value))
      } catch {
        return String(value)
      }
    }
    if (key.includes('amount') || key.includes('value') || key.includes('total')) {
      return Number(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
    }
    return String(value)
  }

  const renderDiff = (oldValues: Record<string, unknown> | null, newValues: Record<string, unknown> | null) => {
    if (!oldValues && !newValues) return null

    const allKeys = new Set([
      ...Object.keys(oldValues || {}),
      ...Object.keys(newValues || {}),
    ])

    const changes: Array<{ key: string; oldVal: unknown; newVal: unknown }> = []

    allKeys.forEach(key => {
      const oldVal = oldValues?.[key]
      const newVal = newValues?.[key]
      if (JSON.stringify(oldVal) !== JSON.stringify(newVal)) {
        changes.push({ key, oldVal, newVal })
      }
    })

    if (changes.length === 0) return null

    return (
      <div className="space-y-2">
        {changes.map(({ key, oldVal, newVal }) => (
          <div key={key} className="grid grid-cols-3 gap-2 text-sm">
            <span className="font-medium text-slate-500 capitalize">
              {key.replace(/_/g, ' ')}:
            </span>
            <span className="text-red-600 col-span-1">
              {formatValue(key, oldVal)}
            </span>
            <span className="text-green-600 col-span-1">
              {formatValue(key, newVal)}
            </span>
          </div>
        ))}
      </div>
    )
  }

  if (isError) {
    toast.error('Erro ao carregar logs de auditoria.')
  }

  return (
    <PageContainer
      title="Log de Auditoria"
      subtitle="Histórico de alterações no sistema"
    >
      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4 items-end">
            <div className="w-48">
              <label className="block text-sm font-medium text-slate-700 mb-1">
                <Filter className="h-4 w-4 inline mr-1" />
                Tipo de Entidade
              </label>
              <select
                value={entityType}
                onChange={e => {
                  setEntityType(e.target.value)
                  setPage(1)
                }}
                className="w-full h-10 px-3 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {ENTITY_TYPES.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-12 text-slate-500">
          <Loader2 className="h-8 w-8 animate-spin mr-2" />
          Carregando...
        </div>
      )}

      {/* Empty */}
      {!isLoading && logs.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center text-slate-500">
            <History className="mx-auto h-12 w-12 text-slate-300 mb-3" />
            <p className="font-medium">Nenhum registro de auditoria encontrado</p>
          </CardContent>
        </Card>
      )}

      {/* Logs */}
      {!isLoading && logs.length > 0 && (
        <>
          <div className="space-y-3">
            {logs.map(log => (
              <Card key={log.id} className="overflow-hidden">
                <CardContent className="p-0">
                  <div
                    className="p-4 cursor-pointer hover:bg-slate-50 transition-colors"
                    onClick={() => setExpandedLog(expandedLog === log.id ? null : log.id)}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <Badge className={cn(ACTION_COLORS[log.action] || 'bg-slate-100 text-slate-700')}>
                            {log.action}
                          </Badge>
                          <Badge variant="outline">{log.entity_type}</Badge>
                          <span className="text-sm text-slate-600 truncate">
                            ID: {log.entity_id}
                          </span>
                        </div>
                        <div className="flex items-center gap-4 mt-2 text-sm text-slate-500">
                          <span className="flex items-center gap-1">
                            <User className="h-3 w-3" />
                            {getUserName(log.user_id)}
                          </span>
                          <span className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            {formatDate(log.created_at)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Expanded details */}
                  {expandedLog === log.id && (log.old_values || log.new_values) && (
                    <div className="border-t border-slate-100 bg-slate-50 p-4">
                      <h4 className="text-sm font-medium text-slate-700 mb-2">Alterações</h4>
                      {renderDiff(log.old_values, log.new_values)}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Pagination */}
          {meta.total_pages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-6">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                <ChevronLeft className="h-4 w-4" />
                Anterior
              </Button>
              <span className="text-sm text-slate-600 px-4">
                Página {page} de {meta.total_pages} ({meta.total} registros)
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(p => Math.min(meta.total_pages, p + 1))}
                disabled={page === meta.total_pages}
              >
                Próxima
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </>
      )}
    </PageContainer>
  )
}
