import { useCallback, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  AlertTriangle,
  CheckCircle2,
  ClipboardCheck,
  Loader2,
  LogIn,
  LogOut,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
} from 'lucide-react'
import { checklistsApi } from '@/api/inventory'
import { propertiesApi } from '@/api/properties'
import { revenuesApi } from '@/api/revenues'
import ChecklistFormModal from '@/components/checklist/ChecklistFormModal'
import PageContainer from '@/components/layout/PageContainer'
import { Button } from '@/components/ui/Button'
import { Card, CardContent } from '@/components/ui/Card'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { Input } from '@/components/ui/Input'
import { isChecklistProfile } from '@/lib/appProfile'
import {
  checklistActionButtonClass,
  checklistActionLabel,
  isChecklistCompleted,
} from '@/lib/checklistUi'
import { currentYearMonth, formatDate } from '@/lib/utils'
import { useAuthStore } from '@/stores/authStore'
import { toast } from '@/stores/toastStore'
import type { ChecklistType } from '@/types/inventory.types'
import type { Revenue } from '@/types/revenue.types'

const selectClassName =
  'w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500'

export default function ConferencesPage() {
  const queryClient = useQueryClient()
  const user = useAuthStore((state) => state.user)
  const canReopen = !isChecklistProfile(user)

  const currentMonth = currentYearMonth()
  const [filterStartMonth, setFilterStartMonth] = useState(currentMonth)
  const [filterEndMonth, setFilterEndMonth] = useState(currentMonth)
  const [filterPropertyId, setFilterPropertyId] = useState('all')
  const [onlyPending, setOnlyPending] = useState(true)
  const [page, setPage] = useState(1)
  const [checklistTarget, setChecklistTarget] = useState<{
    revenueId: string
    type: ChecklistType
  } | null>(null)
  const [reopenTarget, setReopenTarget] = useState<{
    id: string
    label: string
  } | null>(null)
  const perPage = 20

  const hasInvalidRange =
    Boolean(filterStartMonth) && Boolean(filterEndMonth) && filterStartMonth > filterEndMonth

  const { data: properties = [] } = useQuery({
    queryKey: ['properties'],
    queryFn: () => propertiesApi.list(),
  })

  const { data, isLoading } = useQuery({
    queryKey: ['conferences', filterPropertyId, filterStartMonth, filterEndMonth, page],
    queryFn: () =>
      revenuesApi.list({
        property_id: filterPropertyId !== 'all' ? filterPropertyId : undefined,
        start_month: filterStartMonth || undefined,
        end_month: filterEndMonth || undefined,
        page,
        per_page: perPage,
      }),
    enabled: !hasInvalidRange,
    refetchOnMount: 'always',
  })

  const revenues = data?.data ?? []
  const meta = data?.meta ?? { page: 1, per_page: perPage, total: 0, total_pages: 1 }

  const visible = useMemo(() => {
    return [...revenues]
      .sort((a, b) => {
        const aDate = a.checkin_date || a.date || ''
        const bDate = b.checkin_date || b.date || ''
        return bDate.localeCompare(aDate)
      })
      .filter((rev) => {
        if (!onlyPending) return true
        const checkinDone = isChecklistCompleted(rev.checkin_checklist_status)
        const checkoutDone = isChecklistCompleted(rev.checkout_checklist_status)
        // Mantém na lista as já feitas com intercorrência (botão vermelho)
        if (rev.checkin_has_incidents || rev.checkout_has_incidents) return true
        return !(checkinDone && checkoutDone)
      })
  }, [revenues, onlyPending])

  const reopenMutation = useMutation({
    mutationFn: (id: string) => checklistsApi.reopen(id),
    onSuccess: async () => {
      toast.success('Checklist marcado como não feito. Pode ser refeito.')
      setReopenTarget(null)
      await queryClient.invalidateQueries({ queryKey: ['conferences'] })
      await queryClient.invalidateQueries({ queryKey: ['revenues'] })
    },
    onError: () => toast.error('Não foi possível reabrir o checklist.'),
  })

  const closeChecklist = useCallback(() => setChecklistTarget(null), [])

  const renderAction = (
    rev: Revenue,
    type: ChecklistType,
    done: boolean,
    hasIncidents: boolean,
    checklistId?: string | null,
    performedByName?: string | null
  ) => {
    const label = type === 'checkin' ? 'Entrada' : 'Saída'
    const Icon = type === 'checkin' ? LogIn : LogOut
    const byLabel =
      done && performedByName?.trim() ? `Por ${performedByName.trim()}` : null
    return (
      <div key={type} className="space-y-1.5">
        <Button
          variant="ghost"
          className={checklistActionButtonClass(done, hasIncidents)}
          onClick={() => setChecklistTarget({ revenueId: rev.id, type })}
        >
          {hasIncidents ? (
            <AlertTriangle className="mr-1 h-4 w-4" />
          ) : done ? (
            <CheckCircle2 className="mr-1 h-4 w-4" />
          ) : (
            <Icon className="mr-1 h-4 w-4" />
          )}
          <span className="min-w-0 flex-1 text-left">
            <span className="block leading-tight">
              {checklistActionLabel(label, done, hasIncidents)}
            </span>
            {byLabel ? (
              <span className="block truncate text-xs font-normal opacity-90">{byLabel}</span>
            ) : null}
          </span>
        </Button>
        {canReopen && done && checklistId ? (
          <button
            type="button"
            className="flex w-full items-center justify-center gap-1 text-xs font-medium text-slate-500 hover:text-amber-700"
            onClick={() => setReopenTarget({ id: checklistId, label })}
          >
            <RotateCcw className="h-3 w-3" />
            Marcar como não feito
          </button>
        ) : null}
      </div>
    )
  }

  return (
    <PageContainer
      title="Conferências"
      subtitle="Amarelo = pendente · Verde = ok · Vermelho = intercorrência."
    >
      <div className="mb-4 grid gap-3 sm:grid-cols-3">
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-slate-700">Imóvel</label>
          <select
            className={selectClassName}
            value={filterPropertyId}
            onChange={(e) => {
              setFilterPropertyId(e.target.value)
              setPage(1)
            }}
          >
            <option value="all">Todos os imóveis</option>
            {properties.map((property) => (
              <option key={property.id} value={property.id}>
                {property.name}
              </option>
            ))}
          </select>
        </div>
        <Input
          label="De (competência)"
          type="month"
          value={filterStartMonth}
          onChange={(e) => {
            setFilterStartMonth(e.target.value)
            setPage(1)
          }}
        />
        <Input
          label="Até (competência)"
          type="month"
          value={filterEndMonth}
          onChange={(e) => {
            setFilterEndMonth(e.target.value)
            setPage(1)
          }}
        />
      </div>

      <label className="mb-4 flex cursor-pointer items-center gap-2 text-sm text-slate-700">
        <input
          type="checkbox"
          className="h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
          checked={onlyPending}
          onChange={(e) => setOnlyPending(e.target.checked)}
        />
        Somente checklists não concluídos
      </label>

      {hasInvalidRange && (
        <Card className="mb-4 border-amber-200 bg-amber-50">
          <CardContent className="p-4 text-sm text-amber-900">
            O mês inicial não pode ser maior que o mês final.
          </CardContent>
        </Card>
      )}

      {isLoading && (
        <div className="flex items-center justify-center py-12 text-slate-500">
          <Loader2 className="mr-2 h-8 w-8 animate-spin" />
          Carregando estadias...
        </div>
      )}

      {!isLoading && visible.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center text-slate-500">
            <ClipboardCheck className="mx-auto mb-3 h-12 w-12 text-slate-300" />
            <p className="font-medium">
              {onlyPending ? 'Nenhuma conferência pendente' : 'Nenhuma estadia neste período'}
            </p>
            <p className="mt-1 text-sm">
              {onlyPending
                ? 'Desmarque o filtro para ver também as já concluídas.'
                : 'Ajuste o filtro de competência ou imóvel.'}
            </p>
          </CardContent>
        </Card>
      )}

      {!isLoading && visible.length > 0 && (
        <div className="space-y-3">
          {visible.map((rev) => {
            const checkinDone = isChecklistCompleted(rev.checkin_checklist_status)
            const checkoutDone = isChecklistCompleted(rev.checkout_checklist_status)
            return (
              <Card key={rev.id}>
                <CardContent className="space-y-3 p-4">
                  <div>
                    <p className="text-base font-semibold text-slate-900">
                      {rev.property_name || 'Imóvel'}
                    </p>
                    <p className="text-sm text-slate-500">
                      {rev.guest_name || '—'}
                      {rev.external_id ? ` · ${rev.external_id}` : ''}
                    </p>
                    <p className="mt-1 text-sm text-slate-600">
                      {rev.checkin_date ? formatDate(rev.checkin_date) : '—'} →{' '}
                      {rev.checkout_date ? formatDate(rev.checkout_date) : '—'}
                      {rev.nights ? ` · ${rev.nights} noites` : ''}
                    </p>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    {renderAction(
                      rev,
                      'checkin',
                      checkinDone,
                      Boolean(rev.checkin_has_incidents),
                      rev.checkin_checklist_id,
                      rev.checkin_performed_by_name
                    )}
                    {renderAction(
                      rev,
                      'checkout',
                      checkoutDone,
                      Boolean(rev.checkout_has_incidents),
                      rev.checkout_checklist_id,
                      rev.checkout_performed_by_name
                    )}
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {(meta.total_pages || 1) > 1 && (
        <div className="mt-6 flex items-center justify-center gap-2">
          <Button
            variant="outline"
            className="h-11"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            <ChevronLeft className="h-4 w-4" />
            Anterior
          </Button>
          <span className="px-2 text-sm text-slate-600">
            {page}/{meta.total_pages}
          </span>
          <Button
            variant="outline"
            className="h-11"
            onClick={() => setPage((p) => Math.min(meta.total_pages || 1, p + 1))}
            disabled={page === meta.total_pages}
          >
            Próxima
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}

      <ChecklistFormModal
        open={!!checklistTarget}
        revenueId={checklistTarget?.revenueId ?? null}
        checklistType={checklistTarget?.type ?? null}
        onClose={closeChecklist}
      />

      <ConfirmDialog
        open={!!reopenTarget}
        title="Marcar como não feito?"
        message={`A ${reopenTarget?.label?.toLowerCase() ?? 'conferência'} voltará para pendente e precisará ser refeita.`}
        confirmLabel="Marcar como não feito"
        variant="danger"
        isLoading={reopenMutation.isPending}
        onConfirm={() => reopenTarget && reopenMutation.mutate(reopenTarget.id)}
        onCancel={() => setReopenTarget(null)}
      />
    </PageContainer>
  )
}
