import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { Loader2, Pencil, Plus, Tags, Trash2 } from 'lucide-react'
import { inventoryCategoriesApi } from '@/api/inventory'
import { propertiesApi } from '@/api/properties'
import PageContainer from '@/components/layout/PageContainer'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card, CardContent } from '@/components/ui/Card'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { FormModal } from '@/components/ui/FormModal'
import { Input } from '@/components/ui/Input'
import { toast } from '@/stores/toastStore'
import type { InventoryCategory } from '@/types/inventory.types'

const selectClassName =
  'h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm text-slate-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500'

export default function InventoryCategoriesPage() {
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<InventoryCategory | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<InventoryCategory | null>(null)
  const [name, setName] = useState('')
  const [sortOrder, setSortOrder] = useState('0')
  const [propertyId, setPropertyId] = useState(searchParams.get('property') || '')

  const { data: properties = [] } = useQuery({
    queryKey: ['properties'],
    queryFn: () => propertiesApi.list(),
  })

  useEffect(() => {
    if (!propertyId && properties.length === 1) {
      setPropertyId(properties[0].id)
    }
  }, [properties, propertyId])

  useEffect(() => {
    const current = searchParams.get('property') || ''
    if (current === propertyId) return
    const next = new URLSearchParams(searchParams)
    if (propertyId) next.set('property', propertyId)
    else next.delete('property')
    setSearchParams(next, { replace: true })
  }, [propertyId, searchParams, setSearchParams])

  const selectedProperty = useMemo(
    () => properties.find((p) => p.id === propertyId) || null,
    [properties, propertyId]
  )

  const { data: categories = [], isLoading } = useQuery({
    queryKey: ['inventory-categories', propertyId],
    queryFn: () => inventoryCategoriesApi.list(propertyId),
    enabled: !!propertyId,
  })

  const sorted = useMemo(
    () => [...categories].sort((a, b) => a.sort_order - b.sort_order || a.name.localeCompare(b.name)),
    [categories]
  )

  const resetForm = () => {
    setName('')
    setSortOrder(String((sorted[sorted.length - 1]?.sort_order || 0) + 1))
    setEditing(null)
    setShowForm(false)
  }

  const createMutation = useMutation({
    mutationFn: (data: { name: string; sort_order: number }) =>
      inventoryCategoriesApi.create(propertyId, data),
    onSuccess: async () => {
      toast.success('Categoria criada!')
      await queryClient.invalidateQueries({ queryKey: ['inventory-categories', propertyId] })
      resetForm()
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast.error(detail || 'Erro ao criar categoria.')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: { name: string; sort_order: number } }) =>
      inventoryCategoriesApi.update(id, data),
    onSuccess: async () => {
      toast.success('Categoria atualizada!')
      await queryClient.invalidateQueries({ queryKey: ['inventory-categories', propertyId] })
      resetForm()
    },
    onError: () => toast.error('Erro ao atualizar categoria.'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => inventoryCategoriesApi.delete(id),
    onSuccess: async () => {
      toast.success('Categoria removida.')
      await queryClient.invalidateQueries({ queryKey: ['inventory-categories', propertyId] })
      setDeleteConfirm(null)
    },
    onError: () => toast.error('Não foi possível remover a categoria.'),
  })

  const isPending =
    createMutation.isPending || updateMutation.isPending || deleteMutation.isPending

  const handleEdit = (category: InventoryCategory) => {
    setEditing(category)
    setName(category.name)
    setSortOrder(String(category.sort_order))
    setShowForm(true)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const payload = { name: name.trim(), sort_order: Number(sortOrder) || 0 }
    if (!payload.name) {
      toast.error('Informe o nome da categoria.')
      return
    }
    if (editing) {
      updateMutation.mutate({ id: editing.id, data: payload })
    } else {
      createMutation.mutate(payload)
    }
  }

  return (
    <PageContainer
      title="Categorias de inventário"
      subtitle="Cada imóvel tem suas próprias categorias (ambientes)."
      action={
        <Button
          className="h-11"
          disabled={!propertyId}
          onClick={() => {
            resetForm()
            setShowForm(true)
          }}
        >
          <Plus className="mr-1 h-4 w-4" /> Nova categoria
        </Button>
      }
    >
      <div className="mb-4 max-w-md">
        <label className="mb-1 block text-sm font-medium text-slate-700">Imóvel</label>
        <select
          className={selectClassName}
          value={propertyId}
          onChange={(e) => setPropertyId(e.target.value)}
        >
          <option value="">Selecione o imóvel</option>
          {properties.map((property) => (
            <option key={property.id} value={property.id}>
              {property.name}
            </option>
          ))}
        </select>
      </div>

      <FormModal
        open={showForm}
        title={editing ? 'Editar categoria' : 'Nova categoria'}
        description={
          editing
            ? undefined
            : selectedProperty
              ? `Ambiente do imóvel ${selectedProperty.name}. Ex.: Sala, Banheiro, Cozinha.`
              : undefined
        }
        onClose={resetForm}
      >
        <form onSubmit={handleSubmit} className="grid gap-4 sm:grid-cols-2">
          <Input
            label="Nome"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder={editing ? undefined : 'Cozinha'}
            required
          />
          <Input
            label="Ordem"
            type="number"
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value)}
          />
          <div className="sm:col-span-2 flex justify-end gap-2 border-t border-slate-200 pt-4">
            <Button type="button" variant="outline" onClick={resetForm}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : null}
              {editing ? 'Salvar' : 'Criar'}
            </Button>
          </div>
        </form>
      </FormModal>

      {!propertyId && (
        <Card>
          <CardContent className="py-12 text-center text-slate-500">
            <Tags className="mx-auto mb-3 h-12 w-12 text-slate-300" />
            <p className="font-medium">Selecione um imóvel</p>
            <p className="mt-1 text-sm">As categorias são específicas de cada imóvel.</p>
          </CardContent>
        </Card>
      )}

      {propertyId && isLoading && (
        <div className="flex items-center justify-center py-12 text-slate-500">
          <Loader2 className="mr-2 h-8 w-8 animate-spin" />
          Carregando...
        </div>
      )}

      {propertyId && !isLoading && sorted.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center text-slate-500">
            <Tags className="mx-auto mb-3 h-12 w-12 text-slate-300" />
            <p className="font-medium">Nenhuma categoria neste imóvel</p>
            <p className="mt-1 text-sm">Crie ambientes como Sala, Banheiro ou Cozinha.</p>
          </CardContent>
        </Card>
      )}

      {propertyId && !isLoading && sorted.length > 0 && (
        <div className="space-y-2">
          {sorted.map((category) => (
            <Card key={category.id}>
              <CardContent className="flex items-center justify-between gap-3 p-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-slate-900">{category.name}</h3>
                    <Badge variant={category.is_active ? 'success' : 'default'}>
                      {category.is_active ? 'Ativa' : 'Inativa'}
                    </Badge>
                  </div>
                  <p className="text-sm text-slate-500">Ordem: {category.sort_order}</p>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => handleEdit(category)}>
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setDeleteConfirm(category)}>
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <ConfirmDialog
        open={!!deleteConfirm}
        title="Excluir categoria"
        message={`Remover "${deleteConfirm?.name}" deste imóvel?`}
        confirmLabel="Excluir"
        variant="danger"
        isLoading={deleteMutation.isPending}
        onConfirm={() => deleteConfirm && deleteMutation.mutate(deleteConfirm.id)}
        onCancel={() => setDeleteConfirm(null)}
      />
    </PageContainer>
  )
}
