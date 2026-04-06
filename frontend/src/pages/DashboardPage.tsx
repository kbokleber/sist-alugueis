import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '@/api/dashboard'
import PageContainer from '@/components/layout/PageContainer'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { formatMoney } from '@/lib/utils'
import { TrendingUp, TrendingDown, Home, Moon } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart as RePie, Pie, Cell, Legend } from 'recharts'
import { useState } from 'react'

const COLORS = ['#2563EB', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899']

export default function DashboardPage() {
  const [yearMonth] = useState(() => {
    const now = new Date()
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  })

  const { data: overview, isLoading } = useQuery({
    queryKey: ['dashboard', 'overview', yearMonth],
    queryFn: () => dashboardApi.overview(yearMonth),
  })

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
      label: 'Receitas do Mês',
      value: formatMoney(overview?.total_revenue ?? 0),
      icon: TrendingUp,
      color: 'text-green-600 bg-green-50',
    },
    {
      label: 'Despesas do Mês',
      value: formatMoney(overview?.total_expenses ?? 0),
      icon: TrendingDown,
      color: 'text-red-600 bg-red-50',
    },
    {
      label: 'Resultado Líquido',
      value: formatMoney(overview?.total_net_result ?? 0),
      icon: overview?.total_net_result && overview.total_net_result >= 0 ? TrendingUp : TrendingDown,
      color: overview?.total_net_result && overview.total_net_result >= 0 ? 'text-green-600 bg-green-50' : 'text-red-600 bg-red-50',
    },
    {
      label: 'Noites Ocupadas',
      value: String(overview?.total_nights ?? 0),
      icon: Moon,
      color: 'text-blue-600 bg-blue-50',
    },
  ]

  return (
    <PageContainer title="Dashboard">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className={`rounded-lg p-2 ${stat.color}`}>
                  <stat.icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs text-slate-500">{stat.label}</p>
                  <p className="text-lg font-semibold text-slate-900">{stat.value}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Per-property summary */}
      {overview?.properties && overview.properties.length > 0 && (
        <Card>
          <CardHeader>
            <h2 className="text-base font-medium text-slate-900">Resumo por Imóvel</h2>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-left text-slate-500">
                    <th className="pb-3 font-medium">Imóvel</th>
                    <th className="pb-3 font-medium text-right">Receitas</th>
                    <th className="pb-3 font-medium text-right">Despesas</th>
                    <th className="pb-3 font-medium text-right">Resultado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {overview.properties.map((prop) => (
                    <tr key={prop.id}>
                      <td className="py-3 font-medium text-slate-900">{prop.name}</td>
                      <td className="py-3 text-right text-green-600">{formatMoney(prop.total_revenue)}</td>
                      <td className="py-3 text-right text-red-600">{formatMoney(prop.total_expenses)}</td>
                      <td className={`py-3 text-right font-medium ${prop.net_result >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatMoney(prop.net_result)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {(!overview?.properties || overview.properties.length === 0) && (
        <Card>
          <CardContent className="py-12 text-center text-slate-500">
            <Home className="mx-auto h-12 w-12 text-slate-300 mb-3" />
            <p className="font-medium">Nenhum imóvel cadastrado</p>
            <p className="text-sm mt-1">Cadastre um imóvel para ver o dashboard</p>
          </CardContent>
        </Card>
      )}
    </PageContainer>
  )
}
