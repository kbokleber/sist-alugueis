import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { expensesApi, categoriesApi } from '@/api/expenses'
import { propertiesApi } from '@/api/properties'
import PageContainer from '@/components/layout/PageContainer'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { formatMoney } from '@/lib/utils'
import { Plus, Trash2, TrendingDown } from 'lucide-react'

export default function ExpensesPage() {
  const [showForm, setShowForm] = useState(false)
  const [propertyId, setPropertyId] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [name, setName] = useState('')
  const [amount, setAmount] = useState('')
  const [yearMonth, setYearMonth] = useState('')
  const [dueDate, setDueDate] = useState('')
  const [status, setStatus] = useState<'PENDING' | 'PAID' | 'CANCELLED'>('PENDING')
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
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      resetForm()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: expensesApi.delete,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['expenses'] }),
  })

  const markPaidMutation = useMutation({
    mutationFn: expensesApi.markPaid,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['expenses'] }),
  })

  const resetForm = () => {
    setPropertyId('')
    setCategoryId('')
    setName('')
    setAmount('')
    setYearMonth('')
    setDueDate('')
    setStatus('PENDING')
    setShowForm(false)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate({
      property_id: propertyId,
      category_id: categoryId,
      name,
      amount: Number(amount),
      year_month: yearMonth,
      due_date: dueDate || undefined,
      status,
    })
  }

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
          <CardHeader><h2 className="text-base font-medium">Nova Despesa</h2></CardHeader>
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
                <Button type="submit" disabled={createMutation.isPending}>
                  {createMutation.isPending ? 'Salvando...' : 'Salvar'}
                </Button>
                <Button type="button" variant="outline" onClick={resetForm}>Cancelar</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {isLoading ? (
        <div className="text-center py-12 text-slate-500">Carregando...</div>
      ) : expenses.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-slate-500">
            <TrendingDown className="mx-auto h-12 w-12 text-slate-300 mb-3" />
            <p className="font-medium">Nenhuma despesa cadastrada</p>
          </CardContent>
        </Card>
      ) : (
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
                      <td className="px-4 py-3 flex gap-1">
                        {exp.status === 'PENDING' && (
                          <Button size="sm" variant="ghost" onClick={() => markPaidMutation.mutate(exp.id)}>
                            <span className="text-xs text-green-600">Pagar</span>
                          </Button>
                        )}
                        <Button size="sm" variant="ghost" onClick={() => {
                          if (confirm('Excluir?')) deleteMutation.mutate(exp.id)
                        }}>
                          <Trash2 className="h-3 w-3 text-red-500" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </PageContainer>
  )
}
