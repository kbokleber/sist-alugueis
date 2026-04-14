import { useEffect, useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { revenuesApi } from '@/api/revenues'
import { propertiesApi } from '@/api/properties'
import PageContainer from '@/components/layout/PageContainer'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { FormModal } from '@/components/ui/FormModal'
import { toast } from '@/stores/toastStore'
import { useAuthStore } from '@/stores/authStore'
import { currentYearMonth, formatDate, formatMoney } from '@/lib/utils'
import { Plus, Pencil, Trash2, TrendingUp, Loader2, ChevronLeft, ChevronRight, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react'
import type { Revenue } from '@/types/revenue.types'

type RevenueSortField =
  | 'external_id'
  | 'property_name'
  | 'date'
  | 'year_month'
  | 'nights'
  | 'gross_amount'
  | 'cleaning_fee'
  | 'platform_fee'
  | 'pending_amount'
  | 'net_after_pending'

type SortDirection = 'asc' | 'desc'

const calculateGrossAmount = (netAmount: number, cleaningFee: number, platformFee: number) =>
  netAmount + cleaningFee + platformFee

const calculateCompetenceMonth = (checkinDate: string, fallbackDate: string) => {
  const reference = checkinDate || fallbackDate
  if (!reference) return ''
  const [yearPart, monthPart] = reference.split('-')
  const baseYear = Number(yearPart)
  const baseMonth = Number(monthPart)
  if (!baseYear || !baseMonth) return ''
  const monthIndex = baseMonth + 1
  const year = monthIndex === 13 ? baseYear + 1 : baseYear
  const month = String(monthIndex === 13 ? 1 : monthIndex).padStart(2, '0')
  return `${year}-${month}`
}

const formatCompetenceYearMonth = (yearMonth: string) => yearMonth.replace('-', '/')

export default function RevenuesPage() {
  const currentMonth = currentYearMonth()
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<Revenue | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)

  const [propertyId, setPropertyId] = useState('')
  const [guestName, setGuestName] = useState('')
  const [date, setDate] = useState('')
  const [checkinDate, setCheckinDate] = useState('')
  const [checkoutDate, setCheckoutDate] = useState('')
  const [nights, setNights] = useState('')
  const [grossAmount, setGrossAmount] = useState('')
  const [cleaningFee, setCleaningFee] = useState('0')
  const [platformFee, setPlatformFee] = useState('0')
  const [netAmount, setNetAmount] = useState('')
  const [pendingAmount, setPendingAmount] = useState('')
  const [yearMonth, setYearMonth] = useState('')
  const [listingSource, setListingSource] = useState('')
  const [externalId, setExternalId] = useState('')
  const [notes, setNotes] = useState('')
  const [filterPropertyId, setFilterPropertyId] = useState('all')
  const [filterStartMonth, setFilterStartMonth] = useState(currentMonth)
  const [filterEndMonth, setFilterEndMonth] = useState(currentMonth)
  const [filterExternalId, setFilterExternalId] = useState('')
  const [page, setPage] = useState(1)
  const [sortField, setSortField] = useState<RevenueSortField>('year_month')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
  const perPage = 20

  const queryClient = useQueryClient()
  const userId = useAuthStore((state) => state.user?.id)
  const hasInvalidRange =
    Boolean(filterStartMonth) && Boolean(filterEndMonth) && filterStartMonth > filterEndMonth

  const { data, isLoading: isRevenuesLoading } = useQuery({
    queryKey: ['revenues', userId, filterPropertyId, filterStartMonth, filterEndMonth, filterExternalId, page],
    queryFn: () =>
      revenuesApi.list({
        property_id: filterPropertyId !== 'all' ? filterPropertyId : undefined,
        start_month: filterStartMonth || undefined,
        end_month: filterEndMonth || undefined,
        external_id: filterExternalId.trim() || undefined,
        page,
        per_page: perPage,
      }),
    enabled: !hasInvalidRange,
    refetchOnMount: 'always',
  })

  const revenues = data?.data || []
  const meta = data?.meta || { total: 0, page: 1, per_page: perPage, total_pages: 1 }

  const { data: properties = [], isLoading: isPropertiesLoading } = useQuery({
    queryKey: ['properties', userId],
    queryFn: propertiesApi.list,
    refetchOnMount: 'always',
  })
  const isLoading = isRevenuesLoading || isPropertiesLoading

  const createMutation = useMutation({
    mutationFn: revenuesApi.create,
    onSuccess: () => {
      toast.success('Receita criada com sucesso!')
      queryClient.invalidateQueries({ queryKey: ['revenues'] })
      resetForm()
    },
    onError: () => {
      toast.error('Erro ao criar receita. Verifique os dados.')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof revenuesApi.update>[1] }) =>
      revenuesApi.update(id, data),
    onSuccess: () => {
      toast.success('Receita atualizada com sucesso!')
      queryClient.invalidateQueries({ queryKey: ['revenues'] })
      resetForm()
    },
    onError: () => {
      toast.error('Erro ao atualizar receita.')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: revenuesApi.delete,
    onSuccess: () => {
      toast.success('Receita excluída com sucesso!')
      setDeleteConfirm(null)
      queryClient.invalidateQueries({ queryKey: ['revenues'] })
    },
    onError: () => {
      toast.error('Erro ao excluir receita.')
      setDeleteConfirm(null)
    },
  })

  const resetForm = () => {
    setPropertyId('')
    setGuestName('')
    setDate('')
    setCheckinDate('')
    setCheckoutDate('')
    setNights('')
    setGrossAmount('')
    setCleaningFee('0')
    setPlatformFee('0')
    setNetAmount('')
    setPendingAmount('')
    setYearMonth('')
    setListingSource('')
    setExternalId('')
    setNotes('')
    setShowForm(false)
    setEditing(null)
  }

  const handleEdit = (rev: Revenue) => {
    setEditing(rev)
    setPropertyId(rev.property_id)
    setGuestName(rev.guest_name)
    setDate(rev.date)
    setCheckinDate(rev.checkin_date || '')
    setCheckoutDate(rev.checkout_date || '')
    setNights(String(rev.nights))
    setGrossAmount(String(rev.gross_amount))
    setCleaningFee(String(rev.cleaning_fee))
    setPlatformFee(String(rev.platform_fee))
    setNetAmount(String(rev.net_amount))
    setPendingAmount(rev.pending_amount != null ? String(rev.pending_amount) : '')
    setYearMonth(rev.year_month)
    setListingSource(rev.listing_source || '')
    setExternalId(rev.external_id || '')
    setNotes(rev.notes || '')
    setShowForm(true)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const computedYearMonth = calculateCompetenceMonth(checkinDate, date)

    const data = {
      property_id: propertyId,
      guest_name: guestName,
      date,
      checkin_date: checkinDate || undefined,
      checkout_date: checkoutDate || undefined,
      nights: Number(nights),
      gross_amount: Number(grossAmount || 0),
      cleaning_fee: Number(cleaningFee),
      platform_fee: Number(platformFee),
      net_amount: Number(netAmount || 0),
      pending_amount: Number(pendingAmount || 0),
      year_month: editing ? yearMonth : computedYearMonth,
      listing_source: listingSource || undefined,
      external_id: externalId || undefined,
      notes: notes || undefined,
    }
    if (editing) {
      updateMutation.mutate({ id: editing.id, data })
    } else {
      createMutation.mutate(data)
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending
  const summaryTotals = data?.meta?.totals
  const totalGross = summaryTotals?.total_gross ?? revenues.reduce((sum, r) => sum + r.gross_amount, 0)
  const totalPending = summaryTotals?.total_pending ?? revenues.reduce((sum, r) => sum + (r.pending_amount || 0), 0)
  const totalNet =
    summaryTotals?.total_net_after_pending ??
    revenues.reduce((sum, r) => sum + (r.net_amount - (r.pending_amount || 0)), 0)
  const sortedRevenues = useMemo(() => {
    const items = [...revenues]
    items.sort((left, right) => {
      const getValue = (revenue: Revenue) => {
        switch (sortField) {
          case 'external_id':
            return revenue.external_id || ''
          case 'property_name':
            return revenue.property_name || ''
          case 'date':
            return revenue.date || ''
          case 'year_month':
            return revenue.year_month || ''
          case 'nights':
            return revenue.nights || 0
          case 'gross_amount':
            return revenue.gross_amount || 0
          case 'cleaning_fee':
            return revenue.cleaning_fee || 0
          case 'platform_fee':
            return revenue.platform_fee || 0
          case 'pending_amount':
            return revenue.pending_amount || 0
          case 'net_after_pending':
            return revenue.net_amount - (revenue.pending_amount || 0)
          default:
            return ''
        }
      }

      const leftValue = getValue(left)
      const rightValue = getValue(right)

      if (typeof leftValue === 'number' && typeof rightValue === 'number') {
        return sortDirection === 'asc' ? leftValue - rightValue : rightValue - leftValue
      }

      const result = String(leftValue).localeCompare(String(rightValue), 'pt-BR', { sensitivity: 'base' })
      return sortDirection === 'asc' ? result : -result
    })
    return items
  }, [revenues, sortDirection, sortField])
  const handleSort = (field: RevenueSortField) => {
    if (sortField === field) {
      setSortDirection((currentDirection) => (currentDirection === 'asc' ? 'desc' : 'asc'))
      return
    }
    setSortField(field)
    setSortDirection('asc')
  }
  const sortIcon = (field: RevenueSortField) => {
    if (sortField !== field) return <ArrowUpDown className="h-3.5 w-3.5 text-slate-400" />
    return sortDirection === 'asc'
      ? <ArrowUp className="h-3.5 w-3.5 text-primary-600" />
      : <ArrowDown className="h-3.5 w-3.5 text-primary-600" />
  }

  useEffect(() => {
    if (editing) return

    const computedGrossAmount = calculateGrossAmount(
      Number(netAmount || 0),
      Number(cleaningFee || 0),
      Number(platformFee || 0)
    )
    setGrossAmount(String(computedGrossAmount))
  }, [netAmount, cleaningFee, platformFee, editing])

  useEffect(() => {
    if (!editing) {
      setYearMonth(calculateCompetenceMonth(checkinDate, date))
    }
  }, [checkinDate, date, editing])

  return (
    <PageContainer
      title="Receitas"
      action={
        <Button onClick={() => setShowForm(!showForm)}>
          <Plus className="h-4 w-4 mr-1" /> Nova Receita
        </Button>
      }
    >
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="grid gap-3 md:grid-cols-5">
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
                {properties.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-600">Reserva</label>
              <Input
                placeholder="Ex.: EX19J"
                value={filterExternalId}
                onChange={(e) => {
                  setFilterExternalId(e.target.value)
                  setPage(1)
                }}
              />
            </div>
            <div className="flex items-end">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setFilterPropertyId('all')
                  setFilterStartMonth('')
                  setFilterEndMonth('')
                  setFilterExternalId('')
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

      {/* Summary */}
      <div className="grid gap-4 sm:grid-cols-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-slate-500">Total Bruto</p>
            <p className="text-xl font-semibold text-green-600">{formatMoney(totalGross)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-slate-500">Total Líquido</p>
            <p className="text-xl font-semibold text-green-700">{formatMoney(totalNet)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-slate-500">Total de Pendências</p>
            <p className="text-xl font-semibold text-red-700">{formatMoney(totalPending)}</p>
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
        title={editing ? 'Editar receita' : 'Nova receita'}
        description="Preencha os campos abaixo para salvar a receita."
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
              {properties.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </label>
          <Input label="Hóspede" placeholder="Nome do hóspede" value={guestName} onChange={(e) => setGuestName(e.target.value)} required />
          <Input label="Código da reserva" placeholder="Ex.: HY55J" value={externalId} onChange={(e) => setExternalId(e.target.value)} />
          <Input label="Data lançamento" type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
          <Input label="Entrada do hóspede" type="date" value={checkinDate} onChange={(e) => setCheckinDate(e.target.value)} />
          <Input label="Saída do hóspede" type="date" value={checkoutDate} onChange={(e) => setCheckoutDate(e.target.value)} />
          <Input label="Noites" placeholder="Quantidade de noites" type="number" value={nights} onChange={(e) => setNights(e.target.value)} required />
          <Input
            label="Valor líquido (R$)"
            placeholder="0,00"
            type="number"
            value={netAmount}
            onChange={(e) => setNetAmount(e.target.value)}
            required
          />
          <Input
            label="Taxa de limpeza (R$)"
            placeholder="0,00"
            type="number"
            value={cleaningFee}
            onChange={(e) => setCleaningFee(e.target.value)}
            required
          />
          <Input
            label="Taxa da plataforma (R$)"
            placeholder="0,00"
            type="number"
            value={platformFee}
            onChange={(e) => setPlatformFee(e.target.value)}
            required
          />
          <Input
            label="Valor bruto (R$)"
            placeholder="0,00"
            type="number"
            value={grossAmount}
            onChange={(e) => setGrossAmount(e.target.value)}
            readOnly={!editing}
            required
          />
          <Input
            label="Pendência de recebimento (R$)"
            placeholder="0,00"
            type="number"
            min="0"
            step="0.01"
            value={pendingAmount}
            onChange={(e) => setPendingAmount(e.target.value)}
          />
          <Input
            label="Competência"
            placeholder="2026-04"
            value={yearMonth}
            onChange={(e) => setYearMonth(e.target.value)}
            readOnly={!editing}
            required
          />
          <Input label="Origem da reserva" placeholder="AIRBNB, DIRECT..." value={listingSource} onChange={(e) => setListingSource(e.target.value)} />
          <label className="flex flex-col gap-1 md:col-span-2 xl:col-span-3">
            <span className="text-sm font-medium text-slate-700">Observações</span>
            <textarea
              className="min-h-24 rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              placeholder="Observações adicionais da receita"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </label>
          <div className="md:col-span-2 xl:col-span-3 flex justify-end gap-2 border-t border-slate-200 pt-4">
            <Button type="button" variant="outline" onClick={resetForm}>Cancelar</Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : null}
              {isPending ? 'Salvando...' : editing ? 'Salvar alterações' : 'Criar receita'}
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

      {!isLoading && revenues.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center text-slate-500">
            <TrendingUp className="mx-auto h-12 w-12 text-slate-300 mb-3" />
            <p className="font-medium">Nenhuma receita cadastrada</p>
            <p className="text-sm mt-1">Clique em "Nova Receita" para começar</p>
          </CardContent>
        </Card>
      )}

      {!isLoading && revenues.length > 0 && (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-left text-slate-500">
                    <th className="px-4 py-3 font-medium">
                      <button type="button" className="inline-flex items-center gap-1" onClick={() => handleSort('external_id')}>
                        Cód. Reserva
                        {sortIcon('external_id')}
                      </button>
                    </th>
                    <th className="px-4 py-3 font-medium">
                      <button type="button" className="inline-flex items-center gap-1" onClick={() => handleSort('property_name')}>
                        Imóvel
                        {sortIcon('property_name')}
                      </button>
                    </th>
                    <th className="px-4 py-3 font-medium">
                      <button type="button" className="inline-flex items-center gap-1" onClick={() => handleSort('date')}>
                        Lançamento
                        {sortIcon('date')}
                      </button>
                    </th>
                    <th className="px-4 py-3 font-medium">
                      <button type="button" className="inline-flex items-center gap-1" onClick={() => handleSort('year_month')}>
                        Competência
                        {sortIcon('year_month')}
                      </button>
                    </th>
                    <th className="px-4 py-3 font-medium text-right">
                      <button type="button" className="ml-auto inline-flex items-center gap-1" onClick={() => handleSort('nights')}>
                        Noites
                        {sortIcon('nights')}
                      </button>
                    </th>
                    <th className="px-4 py-3 font-medium text-right">
                      <button type="button" className="ml-auto inline-flex items-center gap-1" onClick={() => handleSort('gross_amount')}>
                        Valor Bruto
                        {sortIcon('gross_amount')}
                      </button>
                    </th>
                    <th className="px-4 py-3 font-medium text-right">
                      <button type="button" className="ml-auto inline-flex items-center gap-1" onClick={() => handleSort('cleaning_fee')}>
                        Taxa de Limpeza
                        {sortIcon('cleaning_fee')}
                      </button>
                    </th>
                    <th className="px-4 py-3 font-medium text-right">
                      <button type="button" className="ml-auto inline-flex items-center gap-1" onClick={() => handleSort('platform_fee')}>
                        Taxa da Plataforma
                        {sortIcon('platform_fee')}
                      </button>
                    </th>
                    <th className="px-4 py-3 font-medium text-right">
                      <button type="button" className="ml-auto inline-flex items-center gap-1" onClick={() => handleSort('pending_amount')}>
                        Pendência
                        {sortIcon('pending_amount')}
                      </button>
                    </th>
                    <th className="px-4 py-3 font-medium text-right">
                      <button type="button" className="ml-auto inline-flex items-center gap-1" onClick={() => handleSort('net_after_pending')}>
                        Valor Líquido
                        {sortIcon('net_after_pending')}
                      </button>
                    </th>
                    <th className="px-4 py-3"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {sortedRevenues.map((rev) => (
                    <tr
                      key={rev.id}
                      className={
                        rev.pending_amount && rev.pending_amount > 0
                          ? 'bg-red-100 hover:bg-red-200'
                          : 'hover:bg-slate-50'
                      }
                    >
                      <td className="px-4 py-3 text-slate-600">{rev.external_id || '—'}</td>
                      <td className="px-4 py-3 text-slate-600">{rev.property_name || '—'}</td>
                      <td className="px-4 py-3 text-slate-600">{rev.date ? formatDate(rev.date) : '—'}</td>
                      <td className="px-4 py-3 text-slate-600">{formatCompetenceYearMonth(rev.year_month)}</td>
                      <td className="px-4 py-3 text-right">{rev.nights}</td>
                      <td className="px-4 py-3 text-right text-green-600">{formatMoney(rev.gross_amount)}</td>
                      <td className="px-4 py-3 text-right text-red-500">{formatMoney(rev.cleaning_fee)}</td>
                      <td className="px-4 py-3 text-right text-red-500">{formatMoney(rev.platform_fee)}</td>
                      <td className="px-4 py-3 text-right font-medium text-red-700">
                        {rev.pending_amount && rev.pending_amount > 0 ? formatMoney(rev.pending_amount) : '—'}
                      </td>
                      <td className="px-4 py-3 text-right font-medium text-slate-900">
                        {formatMoney(rev.net_amount - (rev.pending_amount || 0))}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-1">
                          <Button size="sm" variant="outline" onClick={() => handleEdit(rev)}>
                            <Pencil className="h-3 w-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => setDeleteConfirm(rev.id)}
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
        title="Excluir Receita"
        message="Tem certeza que deseja excluir esta receita? Esta ação não pode ser desfeita."
        confirmLabel="Excluir"
        variant="danger"
        isLoading={deleteMutation.isPending}
        onConfirm={() => deleteConfirm && deleteMutation.mutate(deleteConfirm)}
        onCancel={() => setDeleteConfirm(null)}
      />
    </PageContainer>
  )
}
