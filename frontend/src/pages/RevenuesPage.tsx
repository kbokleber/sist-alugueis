import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { revenuesApi } from '@/api/revenues'
import { propertiesApi } from '@/api/properties'
import PageContainer from '@/components/layout/PageContainer'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { formatMoney } from '@/lib/utils'
import { Plus, Trash2, TrendingUp } from 'lucide-react'

export default function RevenuesPage() {
  const [showForm, setShowForm] = useState(false)
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
      queryClient.invalidateQueries({ queryKey: ['revenues'] })
      resetForm()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: revenuesApi.delete,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['revenues'] }),
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
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate({
      property_id: propertyId,
      guest_name: guestName,
      date: date,
      nights: Number(nights),
      gross_amount: Number(grossAmount),
      cleaning_fee: Number(cleaningFee),
      platform_fee: Number(platformFee),
      net_amount: Number(netAmount),
      year_month: yearMonth,
      listing_source: listingSource,
    })
  }

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
          <CardHeader><h2 className="text-base font-medium">Nova Receita</h2></CardHeader>
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
      ) : revenues.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-slate-500">
            <TrendingUp className="mx-auto h-12 w-12 text-slate-300 mb-3" />
            <p className="font-medium">Nenhuma receita cadastrada</p>
          </CardContent>
        </Card>
      ) : (
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
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            if (confirm('Excluir esta receita?')) deleteMutation.mutate(rev.id)
                          }}
                        >
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
