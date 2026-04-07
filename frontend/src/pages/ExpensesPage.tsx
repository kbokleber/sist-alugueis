import { useEffect, useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { expensesApi } from '@/api/expenses'
import { categoriesApi } from '@/api/categories'
import { propertiesApi } from '@/api/properties'
import PageContainer from '@/components/layout/PageContainer'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { FormModal } from '@/components/ui/FormModal'
import { toast } from '@/stores/toastStore'
import { useAuthStore } from '@/stores/authStore'
import { currentYearMonth, formatMoney } from '@/lib/utils'
import { Plus, Pencil, Trash2, TrendingDown, Loader2, ChevronLeft, ChevronRight } from 'lucide-react'
import type { Expense } from '@/types/expense.types'

export default function ExpensesPage() {
  const currentMonth = currentYearMonth()
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<Expense | null>(null)
  const [selectedExpenseIds, setSelectedExpenseIds] = useState<string[]>([])
  const [deleteConfirm, setDeleteConfirm] = useState<{ ids: string[]; mode: 'single' | 'bulk' } | null>(null)

  const [propertyId, setPropertyId] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [name, setName] = useState('')
  const [amount, setAmount] = useState('')
  const [yearMonth, setYearMonth] = useState('')
  const [dueDate, setDueDate] = useState('')
  const [isRecurring, setIsRecurring] = useState(false)
  const [recurrenceType, setRecurrenceType] = useState<'MONTHLY' | 'ANNUAL'>('MONTHLY')
  const [recurrenceStartDate, setRecurrenceStartDate] = useState('')
  const [recurrenceEndDate, setRecurrenceEndDate] = useState('')
  const [filterPropertyId, setFilterPropertyId] = useState('all')
  const [filterStartMonth, setFilterStartMonth] = useState(currentMonth)
  const [filterEndMonth, setFilterEndMonth] = useState(currentMonth)
  const [page, setPage] = useState(1)
  const perPage = 20

  const queryClient = useQueryClient()
  const userId = useAuthStore((state) => state.user?.id)
  const hasInvalidRange =
    Boolean(filterStartMonth) && Boolean(filterEndMonth) && filterStartMonth > filterEndMonth

  const { data, isLoading: isExpensesLoading } = useQuery({
    queryKey: ['expenses', userId, filterPropertyId, filterStartMonth, filterEndMonth, page],
    queryFn: () =>
      expensesApi.list({
        property_id: filterPropertyId !== 'all' ? filterPropertyId : undefined,
        start_month: filterStartMonth || undefined,
        end_month: filterEndMonth || undefined,
        page,
        per_page: perPage,
      }),
    enabled: !hasInvalidRange,
    refetchOnMount: 'always',
  })

  const expenses = data?.data || []
  const meta = data?.meta || { total: 0, page: 1, per_page: perPage, total_pages: 1 }

  const { data: properties = [], isLoading: isPropertiesLoading } = useQuery({
    queryKey: ['properties', userId],
    queryFn: propertiesApi.list,
    refetchOnMount: 'always',
  })

  const { data: categories = [], isLoading: isCategoriesLoading } = useQuery({
    queryKey: ['categories', userId],
    queryFn: categoriesApi.list,
    refetchOnMount: 'always',
  })
  const isLoading = isExpensesLoading || isPropertiesLoading || isCategoriesLoading

  const createMutation = useMutation({
    mutationFn: expensesApi.create,
    onSuccess: (createdExpenses) => {
      const createdCount = createdExpenses.length
      toast.success(createdCount > 1 ? `${createdCount} despesas criadas com sucesso!` : 'Despesa criada com sucesso!')
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      resetForm()
    },
    onError: () => {
      toast.error('Erro ao criar despesa. Verifique os dados.')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof expensesApi.update>[1] }) =>
      expensesApi.update(id, data),
    onSuccess: () => {
      toast.success('Despesa atualizada com sucesso!')
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      resetForm()
    },
    onError: () => {
      toast.error('Erro ao atualizar despesa.')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (ids: string[]) => {
      for (const id of ids) {
        await expensesApi.delete(id)
      }
    },
    onSuccess: (_, ids) => {
      toast.success(ids.length > 1 ? 'Despesas excluídas com sucesso!' : 'Despesa excluída com sucesso!')
      setDeleteConfirm(null)
      setSelectedExpenseIds((current) => current.filter((id) => !ids.includes(id)))
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
    onError: () => {
      toast.error('Erro ao excluir despesa(s).')
      setDeleteConfirm(null)
    },
  })

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: 'PENDING' | 'PAID' }) =>
      expensesApi.setStatus(id, { status }),
    onSuccess: (_expense, variables) => {
      toast.success(variables.status === 'PAID' ? 'Despesa marcada como paga!' : 'Despesa voltou para pendente!')
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
    onError: () => {
      toast.error('Erro ao atualizar o status da despesa.')
    },
  })

  const resetForm = () => {
    setPropertyId('')
    setCategoryId('')
    setName('')
    setAmount('')
    setYearMonth('')
    setDueDate('')
    setIsRecurring(false)
    setRecurrenceType('MONTHLY')
    setRecurrenceStartDate('')
    setRecurrenceEndDate('')
    setShowForm(false)
    setEditing(null)
  }

  const handleEdit = (exp: Expense) => {
    setEditing(exp)
    setPropertyId(exp.property_id)
    setCategoryId(exp.category_id)
    setName(exp.name)
    setAmount(String(exp.amount))
    setYearMonth(exp.year_month)
    setDueDate(exp.due_date || '')
    setIsRecurring(false)
    setRecurrenceType('MONTHLY')
    setRecurrenceStartDate('')
    setRecurrenceEndDate('')
    setShowForm(true)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const baseData = {
      property_id: propertyId,
      category_id: categoryId,
      name,
      amount: Number(amount),
    }

    if (editing) {
      updateMutation.mutate({
        id: editing.id,
        data: {
          ...baseData,
          year_month: yearMonth,
          due_date: dueDate || undefined,
        },
      })
    } else {
      createMutation.mutate(
        isRecurring
          ? {
              ...baseData,
              is_recurring: true,
              recurrence_type: recurrenceType,
              recurrence_start_date: recurrenceStartDate,
              recurrence_end_date: recurrenceEndDate,
              year_month: recurrenceStartDate ? recurrenceStartDate.slice(0, 7) : undefined,
            }
          : {
              ...baseData,
              year_month: yearMonth,
              due_date: dueDate || undefined,
            }
      )
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending
  const totalPending = expenses.filter((e) => e.status === 'PENDING').reduce((s, e) => s + e.amount, 0)
  const totalPaid = expenses.filter((e) => e.status === 'PAID').reduce((s, e) => s + e.amount, 0)
  const allCurrentPageSelected = expenses.length > 0 && expenses.every((expense) => selectedExpenseIds.includes(expense.id))
  const selectedCount = selectedExpenseIds.length
  const deleteDialogTitle = deleteConfirm?.mode === 'bulk' ? 'Excluir despesas selecionadas' : 'Excluir despesa'
  const deleteDialogMessage =
    deleteConfirm?.mode === 'bulk'
      ? `Tem certeza que deseja excluir ${deleteConfirm.ids.length} despesas selecionadas? Esta ação não pode ser desfeita.`
      : 'Tem certeza que deseja excluir esta despesa? Esta ação não pode ser desfeita.'

  useEffect(() => {
    setSelectedExpenseIds([])
  }, [filterPropertyId, filterStartMonth, filterEndMonth, page])

  useEffect(() => {
    setSelectedExpenseIds((current) => current.filter((id) => expenses.some((expense) => expense.id === id)))
  }, [expenses])

  const statusBadge = (s: string) => {
    if (s === 'PAID') return <Badge variant="success">Pago</Badge>
    if (s === 'CANCELLED') return <Badge variant="danger">Cancelado</Badge>
    return <Badge variant="warning">Pendente</Badge>
  }

  const recurringBadge = (isRecurring: boolean) =>
    isRecurring ? <Badge variant="info">Recorrente</Badge> : <Badge variant="default">Avulsa</Badge>

  const selectedRecurringSummary = useMemo(
    () => expenses.filter((expense) => selectedExpenseIds.includes(expense.id)),
    [expenses, selectedExpenseIds]
  )

  return (
    <PageContainer
      title="Despesas"
      action={
        <Button
          onClick={() => {
            if (showForm) {
              resetForm()
              return
            }
            setEditing(null)
            setShowForm(true)
          }}
        >
          <Plus className="h-4 w-4 mr-1" /> Nova Despesa
        </Button>
      }
    >
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="grid gap-3 md:grid-cols-4">
            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-600">Competência inicial</label>
              <Input
                type="month"
                value={filterStartMonth}
                onChange={(e) => {
                  setFilterStartMonth(e.target.value)
                  setPage(1)
                }}
              />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-600">Competência final</label>
              <Input
                type="month"
                value={filterEndMonth}
                onChange={(e) => {
                  setFilterEndMonth(e.target.value)
                  setPage(1)
                }}
              />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-600">Imóvel</label>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
                value={filterPropertyId}
                onChange={(e) => {
                  setFilterPropertyId(e.target.value)
                  setPage(1)
                }}
              >
                <option value="all">Todos os imóveis</option>
                {properties.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
            <div className="flex items-end">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setFilterPropertyId('all')
                  setFilterStartMonth(currentYearMonth())
                  setFilterEndMonth(currentYearMonth())
                  setPage(1)
                }}
              >
                Limpar filtros
              </Button>
            </div>
          </div>
          {hasInvalidRange && (
            <p className="mt-3 text-sm text-red-600">A competência inicial deve ser menor ou igual a final.</p>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 sm:grid-cols-3 mb-6">
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-slate-500">Pendente</p>
            <p className="text-xl font-semibold text-yellow-600">{formatMoney(totalPending)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-slate-500">Pago</p>
            <p className="text-xl font-semibold text-green-600">{formatMoney(totalPaid)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-slate-500">Registros</p>
            <p className="text-xl font-semibold text-slate-900">{meta.total}</p>
          </CardContent>
        </Card>
      </div>

      {!isLoading && selectedCount > 0 && (
        <Card className="mb-4">
          <CardContent className="flex flex-wrap items-center justify-between gap-3 p-4">
            <p className="text-sm text-slate-700">
              {selectedCount} despesa(s) selecionada(s)
            </p>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">
                {selectedRecurringSummary.filter((expense) => expense.is_recurring).length} recorrente(s)
              </span>
              <Button
                type="button"
                variant="danger"
                size="sm"
                onClick={() => setDeleteConfirm({ ids: selectedExpenseIds, mode: 'bulk' })}
              >
                Excluir selecionadas
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <FormModal
        open={showForm}
        title={editing ? 'Editar despesa' : 'Nova despesa'}
        description="Atualize os campos da despesa antes de salvar."
        onClose={resetForm}
      >
        <form onSubmit={handleSubmit} className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <label className="flex flex-col gap-1">
            <span className="text-sm font-medium text-slate-700">Imóvel</span>
            <select
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              value={propertyId}
              onChange={(e) => setPropertyId(e.target.value)}
              required
            >
              <option value="">Selecione o imóvel</option>
              {properties.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-sm font-medium text-slate-700">Categoria</span>
            <select
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              required
            >
              <option value="">Selecione a categoria</option>
              {categories.filter((c) => c.type === 'EXPENSE').map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </label>
          {!editing && (
            <div className="flex items-center gap-2 pt-7">
              <input
                type="checkbox"
                id="isRecurring"
                checked={isRecurring}
                onChange={(e) => setIsRecurring(e.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-primary-600"
              />
              <label htmlFor="isRecurring" className="text-sm text-slate-700">
                Despesa recorrente
              </label>
            </div>
          )}
          <Input label="Descrição" placeholder="Descrição da despesa" value={name} onChange={(e) => setName(e.target.value)} />
          <Input label="Valor (R$)" placeholder="0,00" type="number" value={amount} onChange={(e) => setAmount(e.target.value)} required />
          {editing || !isRecurring ? (
            <>
              <Input
                label="Competência"
                type="month"
                value={yearMonth}
                onChange={(e) => setYearMonth(e.target.value)}
                required
              />
              <Input label="Data de vencimento" type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
            </>
          ) : (
            <>
              <label className="flex flex-col gap-1">
                <span className="text-sm font-medium text-slate-700">Tipo de recorrência</span>
                <select
                  className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                  value={recurrenceType}
                  onChange={(e) => setRecurrenceType(e.target.value as 'MONTHLY' | 'ANNUAL')}
                >
                  <option value="MONTHLY">Mensal</option>
                  <option value="ANNUAL">Anual</option>
                </select>
              </label>
              <Input
                label="Data inicial da recorrência"
                type="date"
                value={recurrenceStartDate}
                onChange={(e) => setRecurrenceStartDate(e.target.value)}
                required
              />
              <Input
                label="Data final da recorrência"
                type="date"
                value={recurrenceEndDate}
                onChange={(e) => setRecurrenceEndDate(e.target.value)}
                required
              />
            </>
          )}
          <div className="md:col-span-2 xl:col-span-3 flex justify-end gap-2 border-t border-slate-200 pt-4">
            <Button type="button" variant="outline" onClick={resetForm}>Cancelar</Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : null}
              {isPending ? 'Salvando...' : editing ? 'Salvar alterações' : 'Criar despesa'}
            </Button>
          </div>
        </form>
      </FormModal>

      {isLoading && (
        <div className="flex items-center justify-center py-12 text-slate-500">
          <Loader2 className="h-8 w-8 animate-spin mr-2" />
          Carregando...
        </div>
      )}

      {!isLoading && expenses.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center text-slate-500">
            <TrendingDown className="mx-auto h-12 w-12 text-slate-300 mb-3" />
            <p className="font-medium">Nenhuma despesa cadastrada</p>
            <p className="text-sm mt-1">Clique em "Nova Despesa" para começar</p>
          </CardContent>
        </Card>
      )}

      {!isLoading && expenses.length > 0 && (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-left text-slate-500">
                    <th className="px-4 py-3 font-medium">
                      <input
                        type="checkbox"
                        checked={allCurrentPageSelected}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedExpenseIds(expenses.map((expense) => expense.id))
                            return
                          }
                          setSelectedExpenseIds([])
                        }}
                        aria-label="Selecionar despesas da página"
                        className="h-4 w-4 rounded border-slate-300 text-primary-600"
                      />
                    </th>
                    <th className="px-4 py-3 font-medium">Código do imóvel</th>
                    <th className="px-4 py-3 font-medium">Imóvel</th>
                    <th className="px-4 py-3 font-medium">Categoria</th>
                    <th className="px-4 py-3 font-medium">Recorrência</th>
                    <th className="px-4 py-3 font-medium">Vencimento</th>
                    <th className="px-4 py-3 font-medium text-right">Valor</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                    <th className="px-4 py-3"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {expenses.map((exp) => (
                    <tr key={exp.id} className="hover:bg-slate-50">
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={selectedExpenseIds.includes(exp.id)}
                          onChange={(e) => {
                            setSelectedExpenseIds((current) =>
                              e.target.checked ? [...current, exp.id] : current.filter((id) => id !== exp.id)
                            )
                          }}
                          aria-label={`Selecionar despesa ${exp.name}`}
                          className="h-4 w-4 rounded border-slate-300 text-primary-600"
                        />
                      </td>
                      <td className="px-4 py-3 font-medium text-slate-900">{exp.property_code || '—'}</td>
                      <td className="px-4 py-3 text-slate-600">{exp.property_name || '—'}</td>
                      <td className="px-4 py-3 text-slate-600">{exp.category_name || '—'}</td>
                      <td className="px-4 py-3">{recurringBadge(exp.is_recurring)}</td>
                      <td className="px-4 py-3 text-slate-600">{exp.due_date || '—'}</td>
                      <td className="px-4 py-3 text-right text-red-600">{formatMoney(exp.amount)}</td>
                      <td className="px-4 py-3">{statusBadge(exp.status)}</td>
                      <td className="px-4 py-3">
                        <div className="flex gap-1">
                          <Button size="sm" variant="outline" onClick={() => handleEdit(exp)}>
                            <Pencil className="h-3 w-3" />
                          </Button>
                          {exp.status === 'PENDING' && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => statusMutation.mutate({ id: exp.id, status: 'PAID' })}
                              disabled={statusMutation.isPending}
                            >
                              <span className="text-xs text-green-600">Pagar</span>
                            </Button>
                          )}
                          {exp.status === 'PAID' && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => statusMutation.mutate({ id: exp.id, status: 'PENDING' })}
                              disabled={statusMutation.isPending}
                            >
                              <span className="text-xs text-amber-600">Reabrir</span>
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => setDeleteConfirm({ ids: [exp.id], mode: 'single' })}
                          >
                            <Trash2 className="h-3 w-3 text-red-500" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {meta.total_pages > 1 && (
        <div className="mt-6 flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((currentPage) => Math.max(1, currentPage - 1))}
            disabled={page === 1}
          >
            <ChevronLeft className="h-4 w-4" />
            Anterior
          </Button>
          <span className="px-4 text-sm text-slate-600">
            Página {page} de {meta.total_pages} ({meta.total} registros)
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((currentPage) => Math.min(meta.total_pages || 1, currentPage + 1))}
            disabled={page === meta.total_pages}
          >
            Próxima
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}

      <ConfirmDialog
        open={!!deleteConfirm}
        title={deleteDialogTitle}
        message={deleteDialogMessage}
        confirmLabel="Excluir"
        variant="danger"
        isLoading={deleteMutation.isPending}
        onConfirm={() => deleteConfirm && deleteMutation.mutate(deleteConfirm.ids)}
        onCancel={() => setDeleteConfirm(null)}
      />
    </PageContainer>
  )
}
