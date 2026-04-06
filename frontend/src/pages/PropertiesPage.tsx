import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { propertiesApi } from '@/api/properties'
import PageContainer from '@/components/layout/PageContainer'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { formatMoney } from '@/lib/utils'
import { Plus, Pencil, Trash2, Building } from 'lucide-react'

export default function PropertiesPage() {
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [address, setAddress] = useState('')
  const [propertyValue, setPropertyValue] = useState('')
  const queryClient = useQueryClient()

  const { data: properties = [], isLoading } = useQuery({
    queryKey: ['properties'],
    queryFn: propertiesApi.list,
  })

  const createMutation = useMutation({
    mutationFn: (data: { name: string; address: string; property_value: number }) =>
      propertiesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['properties'] })
      resetForm()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: propertiesApi.delete,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['properties'] }),
  })

  const resetForm = () => {
    setName('')
    setAddress('')
    setPropertyValue('')
    setShowForm(false)
    setEditing(null)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate({
      name,
      address,
      property_value: Number(propertyValue),
    })
  }

  return (
    <PageContainer
      title="Imóveis"
      action={
        <Button onClick={() => setShowForm(!showForm)}>
          <Plus className="h-4 w-4 mr-1" /> Novo Imóvel
        </Button>
      }
    >
      {showForm && (
        <Card className="mb-6">
          <CardHeader>
            <h2 className="text-base font-medium">{editing ? 'Editar Imóvel' : 'Novo Imóvel'}</h2>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="grid gap-4 sm:grid-cols-3">
              <Input
                label="Nome do Imóvel"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Ex: Apartamento Andorinha"
                required
              />
              <Input
                label="Endereço"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="Endereço completo"
              />
              <Input
                label="Valor do Imóvel (R$)"
                type="number"
                value={propertyValue}
                onChange={(e) => setPropertyValue(e.target.value)}
                placeholder="500000"
                required
              />
              <div className="sm:col-span-3 flex gap-2">
                <Button type="submit" disabled={createMutation.isPending}>
                  {createMutation.isPending ? 'Salvando...' : 'Salvar'}
                </Button>
                <Button type="button" variant="outline" onClick={resetForm}>
                  Cancelar
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {isLoading ? (
        <div className="text-center py-12 text-slate-500">Carregando...</div>
      ) : properties.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-slate-500">
            <Building className="mx-auto h-12 w-12 text-slate-300 mb-3" />
            <p className="font-medium">Nenhum imóvel cadastrado</p>
            <p className="text-sm mt-1">Clique em "Novo Imóvel" para começar</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {properties.map((property) => (
            <Card key={property.id}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-slate-900">{property.name}</h3>
                    <p className="text-sm text-slate-500 mt-1">{property.address || 'Sem endereço'}</p>
                    <div className="mt-3 space-y-1">
                      <p className="text-sm">
                        <span className="text-slate-500">Valor:</span>{' '}
                        <span className="font-medium text-slate-900">{formatMoney(property.property_value)}</span>
                      </p>
                      <p className="text-sm">
                        <span className="text-slate-500">Deprec.:</span>{' '}
                        <span className="font-medium text-slate-900">{property.monthly_depreciation_percent}%/mês</span>
                      </p>
                    </div>
                  </div>
                  <Badge variant={property.is_active ? 'success' : 'default'}>
                    {property.is_active ? 'Ativo' : 'Inativo'}
                  </Badge>
                </div>
                <div className="mt-4 flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => setEditing(property.id)}>
                    <Pencil className="h-3 w-3" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      if (confirm('Excluir este imóvel?')) {
                        deleteMutation.mutate(property.id)
                      }
                    }}
                  >
                    <Trash2 className="h-3 w-3 text-red-500" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </PageContainer>
  )
}
