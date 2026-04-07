import { useState } from 'react'
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
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)

  const [propertyId, setPropertyId] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [name, setName] = useState('')
  const [amount, setAmount] = useState('')
  const [yearMonth, setYearMonth] = useState('')
  const [dueDate, setDueDate] = useState('')
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
    onSuccess: () => {
      toast.success('Despesa criada com sucesso!')
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
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
      resetForm()
    },
    onError: () => {
      toast.error('Erro ao atualizar despesa.')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: expensesApi.delete,
    onSuccess: () => {
      toast.success('Despesa excluída com sucesso!')
      setDeleteConfirm(null)
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
    },
    onError: () => {
      toast.error('Erro ao excluir despesa.')
      setDeleteConfirm(null)
    },
  })

  const markPaidMutation = useMutation({
    mutationFn: expensesApi.markPaid,
    onSuccess: () => {
      toast.success('Despesa marcada como paga!')
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
    },
    onError: () => {
      toast.error('Erro ao marcar despesa como paga.')
    },
  })

  const resetForm = () => {
    setPropertyId('')
    setCategoryId('')
    setName('')
    setAmount('')
    setYearMonth('')
    setDueDate('')
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
    setShowForm(true)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const data = {
      property_id: propertyId,
      category_id: categoryId,
      name,
      amount: Number(amount),
      year_month: yearMonth,
      due_date: dueDate || undefined,
    }
    if (editing) {
      updateMutation.mutate({ id: editing.id, data })
    } else {
      createMutation.mutate(data)
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending
  const totalPending = expenses.filter((e) => e.status === 'PENDING').reduce((s, e) => s + e.amount, 0)
  const totalPaid = expenses.filter((e) => e.status === 'PAID').reduce((s, e) => s + e.amount, 0)

  const statusBadge = (s: string) => {
    if (s === 'PAID') return <Badge variant="success">Pago</Badge>
    if (s === 'CANCELLED') return <Badge variant="danger">Cancelado</Badge>
    return <Badge variant="warning">Pendente</Badge>
  }

  return (
    <PageContainer
      title="Despesas"
      action={
        <Button onClick={() => setShowForm(!showForm)}>
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
          <Input label="Descrição" placeholder="Descrição da despesa" value={name} onChange={(e) => setName(e.target.value)} required />
          <Input label="Valor (R$)" placeholder="0,00" type="number" value={amount} onChange={(e) => setAmount(e.target.value)} required />
          <Input label="Competência" placeholder="2026-04" value={yearMonth} onChange={(e) => setYearMonth(e.target.value)} required />
          <Input label="Data de vencimento" type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
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
                    <th className="px-4 py-3 font-medium">Código do imóvel</th>
                    <th className="px-4 py-3 font-medium">Imóvel</th>
                    <th className="px-4 py-3 font-medium">Categoria</th>
                    <th className="px-4 py-3 font-medium">Vencimento</th>
                    <th className="px-4 py-3 font-medium text-right">Valor</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                    <th className="px-4 py-3"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {expenses.map((exp) => (
                    <tr key={exp.id} className="hover:bg-slate-50">
                      <td className="px-4 py-3 font-medium text-slate-900">{exp.property_code || '—'}</td>
                      <td className="px-4 py-3 text-slate-600">{exp.property_name || '—'}</td>
                      <td className="px-4 py-3 text-slate-600">{exp.category_name || '—'}</td>
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
                              onClick={() => markPaidMutation.mutate(exp.id)}
                              disabled={markPaidMutation.isPending}
                            >
                              <span className="text-xs text-green-600">Pagar</span>
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => setDeleteConfirm(exp.id)}
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
        title="Excluir Despesa"
        message="Tem certeza que deseja excluir esta despesa? Esta ação não pode ser desfeita."
        confirmLabel="Excluir"
        variant="danger"
        isLoading={deleteMutation.isPending}
        onConfirm={() => deleteConfirm && deleteMutation.mutate(deleteConfirm)}
        onCancel={() => setDeleteConfirm(null)}
      />
    </PageContainer>
  )
}
