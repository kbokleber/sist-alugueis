import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '@/api/dashboard'
import PageContainer from '@/components/layout/PageContainer'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { formatMoney, currentYearMonth } from '@/lib/utils'
import { TrendingUp, TrendingDown, Home, Moon, Calendar, PieChart as PieChartIcon } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart as RePie, Pie, Cell, Legend } from 'recharts'
import { useState, useMemo } from 'react'

const COLORS = ['#2563EB', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16']
const DEFAULT_CATEGORY_COLOR = '#BDBDBD'

const renderPieLabel = ({ percent }: { percent?: number }) => {
  if (!percent || percent < 0.04) return ''
  return `${(percent * 100).toFixed(0)}%`
}

export default function DashboardPage() {
  const [endMonth, setEndMonth] = useState(currentYearMonth)
  const [startMonth, setStartMonth] = useState(() => `${currentYearMonth().slice(0, 4)}-01`)
  const [selectedProperty, setSelectedProperty] = useState<string>('all')

  const { data: overview, isLoading } = useQuery({
    queryKey: ['dashboard', 'overview', startMonth, endMonth],
    queryFn: () => dashboardApi.overview(startMonth, endMonth),
    enabled: startMonth <= endMonth,
  })

  const { data: barData } = useQuery({
    queryKey: ['dashboard', 'chartBar', selectedProperty, startMonth, endMonth],
    queryFn: () => dashboardApi.chartBar(
      selectedProperty === 'all' ? undefined : selectedProperty,
      startMonth,
      endMonth
    ),
    enabled: !isLoading && startMonth <= endMonth,
  })

  const { data: pieData } = useQuery({
    queryKey: ['dashboard', 'chartPie', selectedProperty, startMonth, endMonth],
    queryFn: () => dashboardApi.chartPie(
      selectedProperty === 'all' ? undefined : selectedProperty,
      startMonth,
      endMonth
    ),
    enabled: !isLoading && startMonth <= endMonth,
  })

  const propertyOptions = useMemo(() => {
    if (!overview?.properties) return []
    return [{ id: 'all', name: 'Todos os Imóveis' }, ...overview.properties]
  }, [overview?.properties])

  const filteredProperties = useMemo(() => {
    if (!overview?.properties) return []
    if (selectedProperty === 'all') return overview.properties
    return overview.properties.filter((property) => property.id === selectedProperty)
  }, [overview?.properties, selectedProperty])

  const filteredOverview = useMemo(() => {
    const totalRevenue = filteredProperties.reduce((sum, property) => sum + property.total_revenue, 0)
    const totalExpenses = filteredProperties.reduce((sum, property) => sum + property.total_expenses, 0)
    const totalNetResult = filteredProperties.reduce((sum, property) => sum + property.net_result, 0)
    const totalPendingReceivables = filteredProperties.reduce((sum, property) => sum + property.pending_receivables, 0)
    const totalNights = filteredProperties.reduce((sum, property) => sum + (property.total_nights || 0), 0)
    const totalBookings = filteredProperties.reduce((sum, property) => sum + (property.total_bookings || 0), 0)

    return {
      total_properties: filteredProperties.length,
      total_revenue: totalRevenue,
      total_expenses: totalExpenses,
      total_net_result: totalNetResult,
      total_pending_receivables: totalPendingReceivables,
      total_nights: totalNights,
      total_bookings: totalBookings,
    }
  }, [filteredProperties])

  const pieChartColors = useMemo(() => {
    const rawColors = pieData?.datasets[0]?.backgroundColor ?? []
    return rawColors.map((color, index) => {
      if (!color || color.toUpperCase() === DEFAULT_CATEGORY_COLOR) {
        return COLORS[index % COLORS.length]
      }
      return color
    })
  }, [pieData])

  if (isLoading) {
    return (
      <PageContainer title="Dashboard">
        <div className="flex items-center justify-center h-64">
          <div className="text-slate-500">Carregando...</div>
        </div>
      </PageContainer>
    )
  }

  const stats = [
    {
      label: 'Receitas do Período',
      value: formatMoney(filteredOverview.total_revenue),
      icon: TrendingUp,
      color: 'text-green-600 bg-green-50',
    },
    {
      label: 'Despesas do Período',
      value: formatMoney(filteredOverview.total_expenses),
      icon: TrendingDown,
      color: 'text-red-600 bg-red-50',
    },
    {
      label: 'Resultado Líquido',
      value: formatMoney(filteredOverview.total_net_result),
      icon: filteredOverview.total_net_result >= 0 ? TrendingUp : TrendingDown,
      color: filteredOverview.total_net_result >= 0 ? 'text-green-600 bg-green-50' : 'text-red-600 bg-red-50',
    },
    {
      label: 'Pendências de recebimentos',
      value: formatMoney(filteredOverview.total_pending_receivables),
      icon: TrendingDown,
      color: 'text-red-700 bg-red-100',
    },
    {
      label: 'Noites Ocupadas',
      value: String(filteredOverview.total_nights),
      icon: Moon,
      color: 'text-blue-600 bg-blue-50',
    },
    {
      label: 'Aluguéis',
      value: String(filteredOverview.total_bookings),
      icon: Calendar,
      color: 'text-purple-600 bg-purple-50',
    },
    {
      label: 'Imóveis',
      value: String(filteredOverview.total_properties),
      icon: Home,
      color: 'text-amber-600 bg-amber-50',
    },
  ]

  return (
    <PageContainer title="Dashboard">
      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-slate-600">Início:</label>
              <input
                type="month"
                value={startMonth}
                onChange={(e) => setStartMonth(e.target.value)}
                max={endMonth}
                className="px-3 py-1.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-slate-600">Fim:</label>
              <input
                type="month"
                value={endMonth}
                onChange={(e) => setEndMonth(e.target.value)}
                min={startMonth}
                className="px-3 py-1.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-slate-600">Imóvel:</label>
              <select
                value={selectedProperty}
                onChange={(e) => setSelectedProperty(e.target.value)}
                className="px-3 py-1.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {propertyOptions.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
          </div>
          {startMonth > endMonth && (
            <p className="mt-3 text-sm text-red-600">O mês inicial deve ser menor ou igual ao mês final.</p>
          )}
        </CardContent>
      </Card>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-7 mb-6">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <CardContent className="p-3 sm:p-4">
              <div className="flex items-center gap-2 sm:gap-3">
                <div className={`rounded-lg p-1.5 sm:p-2 ${stat.color}`}>
                  <stat.icon className="h-4 w-4 sm:h-5 sm:w-5" />
                </div>
                <div className="min-w-0">
                  <p className="text-xs text-slate-500 truncate">{stat.label}</p>
                  <p className="text-sm sm:text-lg font-semibold text-slate-900 truncate">{stat.value}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Bar Chart */}
        <Card>
          <CardHeader>
            <h2 className="text-base font-medium text-slate-900">Receitas vs Despesas</h2>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              {barData && barData.labels && barData.labels.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={barData.labels.map((label, i) => ({
                    month: label,
                    receitas: barData.datasets[0]?.data?.[i] ?? 0,
                    despesas: barData.datasets[1]?.data?.[i] ?? 0,
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                    <XAxis dataKey="month" tick={{ fontSize: 12 }} stroke="#64748B" />
                    <YAxis tick={{ fontSize: 12 }} stroke="#64748B" tickFormatter={(v) => `R$ ${v / 1000}k`} />
                    <Tooltip 
                      formatter={(value: number) => formatMoney(value)}
                      contentStyle={{ borderRadius: '8px', border: '1px solid #E2E8F0' }}
                    />
                    <Legend />
                    <Bar dataKey="receitas" name="Receitas" fill="#10B981" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="despesas" name="Despesas" fill="#EF4444" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full text-slate-400 text-sm">
                  Sem dados para exibir
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Pie Chart */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <PieChartIcon className="h-5 w-5 text-slate-600" />
              <h2 className="text-base font-medium text-slate-900">Despesas por Categoria</h2>
            </div>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              {pieData && pieData.labels && pieData.labels.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <RePie>
                    <Pie
                      data={pieData.labels.map((label, i) => ({
                        name: label,
                        value: pieData.datasets[0]?.data?.[i] ?? 0,
                      }))}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={2}
                      dataKey="value"
                      label={renderPieLabel}
                      labelLine={false}
                    >
                      {pieData.datasets[0]?.data?.map((_, i) => (
                        <Cell key={`cell-${i}`} fill={pieChartColors[i] || COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip 
                      formatter={(value: number, _name, item) => {
                        const payload = item?.payload as { value?: number } | undefined
                        const total = pieData.datasets[0]?.data?.reduce((sum, current) => sum + current, 0) ?? 0
                        const currentValue = payload?.value ?? value
                        const percentage = total > 0 ? (currentValue / total) * 100 : 0
                        return [`${formatMoney(currentValue)} (${percentage.toFixed(1)}%)`, 'Valor']
                      }}
                      contentStyle={{ borderRadius: '8px', border: '1px solid #E2E8F0' }}
                    />
                    <Legend formatter={(value, _entry, index) => {
                      const currentValue = pieData.datasets[0]?.data?.[index] ?? 0
                      const total = pieData.datasets[0]?.data?.reduce((sum, current) => sum + current, 0) ?? 0
                      const percentage = total > 0 ? (currentValue / total) * 100 : 0
                      return `${value} (${percentage.toFixed(1)}%)`
                    }} />
                  </RePie>
                </ResponsiveContainer>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-slate-400 text-sm">
                  <PieChartIcon className="h-12 w-12 mb-2" />
                  <p>Sem despesas por categoria para exibir</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Per-property summary */}
      <Card>
        <CardHeader>
          <h2 className="text-base font-medium text-slate-900">Resumo por Imóvel</h2>
        </CardHeader>
        <CardContent>
          {filteredProperties.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-left text-slate-500">
                    <th className="pb-3 font-medium">Imóvel</th>
                    <th className="pb-3 font-medium text-right">Receitas</th>
                    <th className="pb-3 font-medium text-right">Despesas</th>
                    <th className="pb-3 font-medium text-right">Noites</th>
                    <th className="pb-3 font-medium text-right">Aluguéis</th>
                    <th className="pb-3 font-medium text-right">Resultado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredProperties.map((prop) => (
                    <tr key={prop.id}>
                      <td className="py-3 font-medium text-slate-900">{prop.name}</td>
                      <td className="py-3 text-right text-green-600">{formatMoney(prop.total_revenue)}</td>
                      <td className="py-3 text-right text-red-600">{formatMoney(prop.total_expenses)}</td>
                      <td className="py-3 text-right text-slate-600">{prop.total_nights || 0}</td>
                      <td className="py-3 text-right text-slate-600">{prop.total_bookings || 0}</td>
                      <td className={`py-3 text-right font-medium ${prop.net_result >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatMoney(prop.net_result)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-12 text-center text-slate-500">
              <Home className="mx-auto h-12 w-12 text-slate-300 mb-3" />
              <p className="font-medium">Nenhum imóvel cadastrado</p>
              <p className="text-sm mt-1">Cadastre um imóvel para ver o dashboard</p>
            </div>
          )}
        </CardContent>
      </Card>
    </PageContainer>
  )
}
