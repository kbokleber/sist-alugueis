import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { revenuesApi } from '@/api/revenues'
import { propertiesApi } from '@/api/properties'
import PageContainer from '@/components/layout/PageContainer'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { toast } from '@/stores/toastStore'
import { formatMoney } from '@/lib/utils'
import { Plus, Pencil, Trash2, TrendingUp, Loader2 } from 'lucide-react'
import type { Revenue } from '@/types/revenue.types'

export default function RevenuesPage() {
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<Revenue | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)

  const [propertyId, setPropertyId] = useState('')
  const [guestName, setGuestName] = useState('')
  const [date, setDate] = useState('')
  const [nights, setNights] = useState('')
  const [grossAmount, setGrossAmount] = useState('')
  const [cleaningFee, setCleaningFee] = useState('0')
  const [platformFee, setPlatformFee] = useState('0')
  const [netAmount, setNetAmount] = useState('')
  const [yearMonth, setYearMonth] = useState('')
  const [listingSource, setListingSource] = useState('')

  const queryClient = useQueryClient()

  const { data: revenues = [], isLoading } = useQuery({
    queryKey: ['revenues'],
    queryFn: () => revenuesApi.list(),
  })

  const { data: properties = [] } = useQuery({
    queryKey: ['properties'],
    queryFn: propertiesApi.list,
  })

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
    setNights('')
    setGrossAmount('')
    setCleaningFee('0')
    setPlatformFee('0')
    setNetAmount('')
    setYearMonth('')
    setListingSource('')
    setShowForm(false)
    setEditing(null)
  }

  const handleEdit = (rev: Revenue) => {
    setEditing(rev)
    setPropertyId(rev.property_id)
    setGuestName(rev.guest_name)
    setDate(rev.date)
    setNights(String(rev.nights))
    setGrossAmount(String(rev.gross_amount))
    setCleaningFee(String(rev.cleaning_fee))
    setPlatformFee(String(rev.platform_fee))
    setNetAmount(String(rev.net_amount))
    setYearMonth(rev.year_month)
    setListingSource(rev.listing_source || '')
    setShowForm(true)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const data = {
      property_id: propertyId,
      guest_name: guestName,
      date,
      nights: Number(nights),
      gross_amount: Number(grossAmount),
      cleaning_fee: Number(cleaningFee),
      platform_fee: Number(platformFee),
      net_amount: Number(netAmount),
      year_month: yearMonth,
      listing_source: listingSource || undefined,
    }
    if (editing) {
      updateMutation.mutate({ id: editing.id, data })
    } else {
      createMutation.mutate(data)
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending
  const totalGross = revenues.reduce((sum, r) => sum + r.gross_amount, 0)
  const totalNet = revenues.reduce((sum, r) => sum + r.net_amount, 0)

  return (
    <PageContainer
      title="Receitas"
      action={
        <Button onClick={() => setShowForm(!showForm)}>
          <Plus className="h-4 w-4 mr-1" /> Nova Receita
        </Button>
      }
    >
      {/* Summary */}
      <div className="grid gap-4 sm:grid-cols-3 mb-6">
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
            <p className="text-xs text-slate-500">Registros</p>
            <p className="text-xl font-semibold text-slate-900">{revenues.length}</p>
          </CardContent>
        </Card>
      </div>

      {showForm && (
        <Card className="mb-6">
          <CardHeader>
            <h2 className="text-base font-medium">{editing ? 'Editar Receita' : 'Nova Receita'}</h2>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <select
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
                value={propertyId}
                onChange={(e) => setPropertyId(e.target.value)}
                required
              >
                <option value="">Selecione o imóvel</option>
                {properties.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
              <Input placeholder="Nome do hóspede" value={guestName} onChange={(e) => setGuestName(e.target.value)} required />
              <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
              <Input placeholder="Noites" type="number" value={nights} onChange={(e) => setNights(e.target.value)} required />
              <Input placeholder="Valor bruto (R$)" type="number" value={grossAmount} onChange={(e) => setGrossAmount(e.target.value)} required />
              <Input placeholder="Taxa de limpeza (R$)" type="number" value={cleaningFee} onChange={(e) => setCleaningFee(e.target.value)} />
              <Input placeholder="Taxa plataforma (R$)" type="number" value={platformFee} onChange={(e) => setPlatformFee(e.target.value)} />
              <Input placeholder="Valor líquido (R$)" type="number" value={netAmount} onChange={(e) => setNetAmount(e.target.value)} required />
              <Input placeholder="Ano-mês (ex: 2026-04)" value={yearMonth} onChange={(e) => setYearMonth(e.target.value)} required />
              <Input placeholder="Origem (AIRBNB, DIRECT...)" value={listingSource} onChange={(e) => setListingSource(e.target.value)} />
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
                    <th className="px-4 py-3 font-medium">Hóspede</th>
                    <th className="px-4 py-3 font-medium">Imóvel</th>
                    <th className="px-4 py-3 font-medium">Data</th>
                    <th className="px-4 py-3 font-medium text-right">Noites</th>
                    <th className="px-4 py-3 font-medium text-right">Valor Bruto</th>
                    <th className="px-4 py-3 font-medium text-right">Taxas</th>
                    <th className="px-4 py-3 font-medium text-right">Valor Líquido</th>
                    <th className="px-4 py-3"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {revenues.map((rev) => (
                    <tr key={rev.id} className="hover:bg-slate-50">
                      <td className="px-4 py-3 font-medium text-slate-900">{rev.guest_name}</td>
                      <td className="px-4 py-3 text-slate-600">{rev.property_name || '—'}</td>
                      <td className="px-4 py-3 text-slate-600">{rev.date}</td>
                      <td className="px-4 py-3 text-right">{rev.nights}</td>
                      <td className="px-4 py-3 text-right text-green-600">{formatMoney(rev.gross_amount)}</td>
                      <td className="px-4 py-3 text-right text-red-500">
                        {formatMoney(rev.cleaning_fee + rev.platform_fee)}
                      </td>
                      <td className="px-4 py-3 text-right font-medium text-slate-900">{formatMoney(rev.net_amount)}</td>
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
