import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { expensesApi, categoriesApi } from '@/api/expenses'
import { propertiesApi } from '@/api/properties'
import PageContainer from '@/components/layout/PageContainer'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { toast } from '@/stores/toastStore'
import { formatMoney } from '@/lib/utils'
import { Plus, Pencil, Trash2, TrendingDown, Loader2 } from 'lucide-react'
import type { Expense } from '@/types/expense.types'

export default function ExpensesPage() {
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<Expense | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)

  const [propertyId, setPropertyId] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [name, setName] = useState('')
  const [amount, setAmount] = useState('')
  const [yearMonth, setYearMonth] = useState('')
  const [dueDate, setDueDate] = useState('')

  const queryClient = useQueryClient()

  const { data: expenses = [], isLoading } = useQuery({
    queryKey: ['expenses'],
    queryFn: () => expensesApi.list(),
  })

  const { data: properties = [] } = useQuery({
    queryKey: ['properties'],
    queryFn: propertiesApi.list,
  })

  const { data: categories = [] } = useQuery({
    queryKey: ['categories'],
    queryFn: categoriesApi.list,
  })

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
            <p className="text-xl font-semibold text-slate-900">{expenses.length}</p>
          </CardContent>
        </Card>
      </div>

      {showForm && (
        <Card className="mb-6">
          <CardHeader>
            <h2 className="text-base font-medium">{editing ? 'Editar Despesa' : 'Nova Despesa'}</h2>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <select
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
                value={propertyId}
                onChange={(e) => setPropertyId(e.target.value)}
                required
              >
                <option value="">Imóvel</option>
                {properties.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
              <select
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value)}
                required
              >
                <option value="">Categoria</option>
                {categories.filter((c) => c.type === 'EXPENSE').map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
              <Input placeholder="Descrição" value={name} onChange={(e) => setName(e.target.value)} required />
              <Input placeholder="Valor (R$)" type="number" value={amount} onChange={(e) => setAmount(e.target.value)} required />
              <Input placeholder="Ano-mês (ex: 2026-04)" value={yearMonth} onChange={(e) => setYearMonth(e.target.value)} required />
              <Input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
              <div className="lg:col-span-3 flex gap-2">
                <Button type="submit" disabled={isPending}>
                  {isPending ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : null}
                  {isPending ? 'Salvando...' : 'Salvar'}
                </Button>
                <Button type="button" variant="outline" onClick={resetForm}>Cancelar</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

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
                    <th className="px-4 py-3 font-medium">Descrição</th>
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
                      <td className="px-4 py-3 font-medium text-slate-900">{exp.name}</td>
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
