import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { closingApi } from '@/api/closing'
import { propertiesApi } from '@/api/properties'
import PageContainer from '@/components/layout/PageContainer'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { formatMoney, formatDate, formatMonth, currentYearMonth } from '@/lib/utils'
import { FileText, Download, Plus, CheckCircle, Clock } from 'lucide-react'
import { useState, useMemo } from 'react'

export default function ClosingPage() {
  const queryClient = useQueryClient()
  const [selectedProperty, setSelectedProperty] = useState<string>('')
  const [selectedYearMonth, setSelectedYearMonth] = useState(currentYearMonth)
  const [showGenerateModal, setShowGenerateModal] = useState(false)
  const [selectedClosing, setSelectedClosing] = useState<any>(null)

  const { data: properties } = useQuery({
    queryKey: ['properties'],
    queryFn: propertiesApi.list,
  })

  const { data: closings, isLoading: closingsLoading } = useQuery({
    queryKey: ['closings', selectedProperty],
    queryFn: () => closingApi.list(selectedProperty || undefined),
  })

  const generateMutation = useMutation({
    mutationFn: closingApi.generate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['closings'] })
      setShowGenerateModal(false)
    },
  })

  const handleGenerate = () => {
    if (!selectedProperty) {
      alert('Selecione um imóvel')
      return
    }
    generateMutation.mutate({
      property_id: selectedProperty,
      year_month: selectedYearMonth,
    })
  }

  const handleViewClosing = (closing: any) => {
    setSelectedClosing(closing)
  }

  const statusConfig: Record<string, { color: string; icon: any; label: string }> = {
    OPEN: { color: 'bg-slate-100 text-slate-700', icon: Clock, label: 'Aberto' },
    CLOSED: { color: 'bg-green-100 text-green-700', icon: CheckCircle, label: 'Fechado' },
  }

  const propertyMap = useMemo(() => {
    if (!properties?.items) return {}
    return properties.items.reduce((acc: any, p: any) => {
      acc[p.id] = p.name
      return acc
    }, {})
  }, [properties])

  return (
    <PageContainer title="Fechamento Mensal">
      {/* Header Actions */}
      <div className="flex flex-wrap gap-4 mb-6">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <label className="text-sm font-medium text-slate-600 shrink-0">Imóvel:</label>
          <select
            value={selectedProperty}
            onChange={(e) => setSelectedProperty(e.target.value)}
            className="px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 flex-1 min-w-[150px]"
          >
            <option value="">Todos os imóveis</option>
            {properties?.items?.map((p: any) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </div>
        <Button onClick={() => setShowGenerateModal(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          Gerar Fechamento
        </Button>
      </div>

      {/* Closings List */}
      <Card>
        <CardHeader>
          <h2 className="text-base font-medium text-slate-900">Fechamentos</h2>
        </CardHeader>
        <CardContent>
          {closingsLoading ? (
            <div className="py-12 text-center text-slate-500">Carregando...</div>
          ) : closings?.data && closings.data.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-left text-slate-500">
                    <th className="pb-3 font-medium">Imóvel</th>
                    <th className="pb-3 font-medium">Período</th>
                    <th className="pb-3 font-medium text-right">Receitas</th>
                    <th className="pb-3 font-medium text-right">Despesas</th>
                    <th className="pb-3 font-medium text-right">Resultado</th>
                    <th className="pb-3 font-medium text-center">Status</th>
                    <th className="pb-3 font-medium text-center">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {closings.data.map((closing: any) => {
                    const status = statusConfig[closing.status] || statusConfig.OPEN
                    const StatusIcon = status.icon
                    return (
                      <tr key={closing.id}>
                        <td className="py-3 font-medium text-slate-900">
                          {propertyMap[closing.property_id] || closing.property_id}
                        </td>
                        <td className="py-3 text-slate-600">{formatMonth(closing.year_month)}</td>
                        <td className="py-3 text-right text-green-600">{formatMoney(closing.total_revenue)}</td>
                        <td className="py-3 text-right text-red-600">{formatMoney(closing.total_expenses)}</td>
                        <td className={`py-3 text-right font-medium ${closing.net_result >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {formatMoney(closing.net_result)}
                        </td>
                        <td className="py-3 text-center">
                          <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${status.color}`}>
                            <StatusIcon className="h-3 w-3" />
                            {status.label}
                          </span>
                        </td>
                        <td className="py-3 text-center">
                          <Button variant="ghost" size="sm" onClick={() => handleViewClosing(closing)}>
                            Ver
                          </Button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-12 text-center text-slate-500">
              <FileText className="mx-auto h-12 w-12 text-slate-300 mb-3" />
              <p className="font-medium">Nenhum fechamento encontrado</p>
              <p className="text-sm mt-1">Clique em "Gerar Fechamento" para criar um</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Generate Modal */}
      {showGenerateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md">
            <CardHeader>
              <h3 className="text-lg font-semibold text-slate-900">Gerar Fechamento</h3>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Imóvel</label>
                <select
                  value={selectedProperty}
                  onChange={(e) => setSelectedProperty(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Selecione um imóvel</option>
                  {properties?.items?.map((p: any) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Mês de Referência</label>
                <input
                  type="month"
                  value={selectedYearMonth}
                  onChange={(e) => setSelectedYearMonth(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <Button variant="outline" onClick={() => setShowGenerateModal(false)} className="flex-1">
                  Cancelar
                </Button>
                <Button 
                  onClick={handleGenerate} 
                  disabled={generateMutation.isPending || !selectedProperty}
                  className="flex-1"
                >
                  {generateMutation.isPending ? 'Gerando...' : 'Gerar'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Closing Detail Modal */}
      {selectedClosing && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-slate-900">
                  Fechamento - {propertyMap[selectedClosing.property_id] || selectedClosing.property_id}
                </h3>
                <Button variant="ghost" size="sm" onClick={() => setSelectedClosing(null)}>
                  ✕
                </Button>
              </div>
              <p className="text-sm text-slate-500">{formatMonth(selectedClosing.year_month)}</p>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Summary KPIs */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-green-50 rounded-lg p-3">
                  <p className="text-xs text-green-600 font-medium">Receitas</p>
                  <p className="text-lg font-semibold text-green-700">{formatMoney(selectedClosing.total_revenue)}</p>
                </div>
                <div className="bg-red-50 rounded-lg p-3">
                  <p className="text-xs text-red-600 font-medium">Despesas</p>
                  <p className="text-lg font-semibold text-red-700">{formatMoney(selectedClosing.total_expenses)}</p>
                </div>
                <div className="bg-blue-50 rounded-lg p-3">
                  <p className="text-xs text-blue-600 font-medium">Resultado Bruto</p>
                  <p className="text-lg font-semibold text-blue-700">{formatMoney(selectedClosing.total_revenue - selectedClosing.total_expenses)}</p>
                </div>
                <div className={`rounded-lg p-3 ${selectedClosing.net_result >= 0 ? 'bg-green-50' : 'bg-red-50'}`}>
                  <p className={`text-xs font-medium ${selectedClosing.net_result >= 0 ? 'text-green-600' : 'text-red-600'}`}>Resultado Líquido</p>
                  <p className={`text-lg font-semibold ${selectedClosing.net_result >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                    {formatMoney(selectedClosing.net_result)}
                  </p>
                </div>
              </div>

              {/* Details */}
              <div className="border-t border-slate-200 pt-4">
                <h4 className="text-sm font-medium text-slate-900 mb-3">Detalhes</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Noites Ocupadas</span>
                    <span className="font-medium">{selectedClosing.total_nights}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Aluguéis</span>
                    <span className="font-medium">{selectedClosing.total_bookings}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Taxa de Limpeza</span>
                    <span className="font-medium text-red-600">-{formatMoney(selectedClosing.cleaning_total)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Taxa de Plataforma</span>
                    <span className="font-medium text-red-600">-{formatMoney(selectedClosing.platform_fee_total)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Depreciação</span>
                    <span className="font-medium text-red-600">-{formatMoney(selectedClosing.depreciation_value)}</span>
                  </div>
                  <div className="flex justify-between border-t border-slate-100 pt-2">
                    <span className="text-slate-500">Outras Despesas</span>
                    <span className="font-medium text-red-600">-{formatMoney(selectedClosing.other_expenses)}</span>
                  </div>
                </div>
              </div>

              {/* Status & Notes */}
              <div className="border-t border-slate-200 pt-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium text-slate-900">Status</span>
                  <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${statusConfig[selectedClosing.status]?.color || ''}`}>
                    {statusConfig[selectedClosing.status]?.label || selectedClosing.status}
                  </span>
                </div>
                {selectedClosing.notes && (
                  <div>
                    <p className="text-sm font-medium text-slate-700 mb-1">Observações</p>
                    <p className="text-sm text-slate-600 bg-slate-50 rounded-lg p-3">{selectedClosing.notes}</p>
                  </div>
                )}
                {selectedClosing.created_at && (
                  <p className="text-xs text-slate-400 mt-3">
                    Criado em: {formatDate(selectedClosing.created_at)}
                  </p>
                )}
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-4">
                {selectedClosing.status === 'OPEN' && (
                  <Button 
                    variant="outline" 
                    className="flex-1 gap-2"
                    onClick={() => {
                      closingApi.close(selectedClosing.property_id, selectedClosing.year_month)
                      setSelectedClosing(null)
                    }}
                  >
                    <CheckCircle className="h-4 w-4" />
                    Fechar Período
                  </Button>
                )}
                <Button 
                  variant="outline" 
                  className="flex-1 gap-2"
                  onClick={() => closingApi.exportCsv(selectedClosing.property_id, selectedClosing.year_month)}
                >
                  <Download className="h-4 w-4" />
                  Exportar CSV
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </PageContainer>
  )
}
