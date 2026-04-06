import PageContainer from '@/components/layout/PageContainer'
import { Card, CardContent } from '@/components/ui/Card'
import { PieChart as RePie, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import { PieChart } from 'lucide-react'

export default function ClosingPage() {
  return (
    <PageContainer title="Fechamento Mensal">
      <Card>
        <CardContent className="py-12 text-center text-slate-500">
          <PieChart className="mx-auto h-12 w-12 text-slate-300 mb-3" />
          <p className="font-medium">Fechamento Mensal</p>
          <p className="text-sm mt-1">Gere o fechamento de cada imóvel ao final do mês</p>
          <p className="text-sm mt-2 text-slate-400">Disponível em breve via API: POST /api/v1/closing/generate</p>
        </CardContent>
      </Card>
    </PageContainer>
  )
}
