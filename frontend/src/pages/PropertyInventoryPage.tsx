import { useMemo, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, ClipboardList, ImageIcon, Loader2, Pencil, Plus, Trash2, Upload } from 'lucide-react'
import { inventoryCategoriesApi, inventoryItemsApi, type InventoryItemPayload } from '@/api/inventory'
import { propertiesApi } from '@/api/properties'
import PageContainer from '@/components/layout/PageContainer'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card, CardContent } from '@/components/ui/Card'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { FormModal } from '@/components/ui/FormModal'
import { Input } from '@/components/ui/Input'
import { toast } from '@/stores/toastStore'
import type { InventoryItem } from '@/types/inventory.types'

const selectClassName =
  'rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500'

function emptyToNull(value: string): string | null {
  const trimmed = value.trim()
  return trimmed || null
}

function itemDetailLine(item: InventoryItem): string | null {
  const parts = [
    item.brand,
    item.model,
    item.color ? `Cor: ${item.color}` : null,
    item.serial_number ? `Nº série: ${item.serial_number}` : null,
  ].filter(Boolean)
  return parts.length ? parts.join(' · ') : null
}

function InventoryItemThumb({ name, imageUrl }: { name: string; imageUrl?: string | null }) {
  const [hasError, setHasError] = useState(false)
  if (!imageUrl || hasError) {
    return (
      <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-400">
        <ImageIcon className="h-6 w-6" />
      </div>
    )
  }
  return (
    <img
      src={imageUrl}
      alt={name}
      className="h-14 w-14 shrink-0 rounded-lg object-cover"
      onError={() => setHasError(true)}
    />
  )
}

export default function PropertyInventoryPage() {
  const { propertyId = '' } = useParams()
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<InventoryItem | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<InventoryItem | null>(null)
  const [filterCategoryId, setFilterCategoryId] = useState('all')
  const [search, setSearch] = useState('')

  const [name, setName] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [quantityExpected, setQuantityExpected] = useState('1')
  const [color, setColor] = useState('')
  const [serialNumber, setSerialNumber] = useState('')
  const [brand, setBrand] = useState('')
  const [model, setModel] = useState('')
  const [imageUrl, setImageUrl] = useState('')
  const [notes, setNotes] = useState('')
  const [isConsumable, setIsConsumable] = useState(false)

  const { data: property } = useQuery({
    queryKey: ['properties', propertyId],
    queryFn: () => propertiesApi.get(propertyId),
    enabled: !!propertyId,
  })

  const { data: categories = [] } = useQuery({
    queryKey: ['inventory-categories', propertyId],
    queryFn: () => inventoryCategoriesApi.list(propertyId),
    enabled: !!propertyId,
  })

  const { data: items = [], isLoading } = useQuery({
    queryKey: ['inventory-items', propertyId, filterCategoryId, search],
    queryFn: () =>
      inventoryItemsApi.list(propertyId, {
        category_id: filterCategoryId === 'all' ? undefined : filterCategoryId,
        q: search.trim() || undefined,
      }),
    enabled: !!propertyId,
  })

  const grouped = useMemo(() => {
    const map = new Map<string, InventoryItem[]>()
    for (const item of items) {
      const key = item.category_name || 'Sem categoria'
      const list = map.get(key) || []
      list.push(item)
      map.set(key, list)
    }
    return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b))
  }, [items])

  const resetForm = () => {
    setName('')
    setCategoryId(categories[0]?.id || '')
    setQuantityExpected('1')
    setColor('')
    setSerialNumber('')
    setBrand('')
    setModel('')
    setImageUrl('')
    setNotes('')
    setIsConsumable(false)
    setEditing(null)
    setShowForm(false)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const createMutation = useMutation({
    mutationFn: (data: InventoryItemPayload) => inventoryItemsApi.create(propertyId, data),
    onSuccess: async () => {
      toast.success('Item adicionado ao inventário!')
      await queryClient.invalidateQueries({ queryKey: ['inventory-items', propertyId] })
      resetForm()
    },
    onError: () => toast.error('Erro ao criar item de inventário.'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: InventoryItemPayload }) =>
      inventoryItemsApi.update(id, data),
    onSuccess: async () => {
      toast.success('Item atualizado!')
      await queryClient.invalidateQueries({ queryKey: ['inventory-items', propertyId] })
      resetForm()
    },
    onError: () => toast.error('Erro ao atualizar item.'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => inventoryItemsApi.delete(id),
    onSuccess: async () => {
      toast.success('Item removido do inventário.')
      await queryClient.invalidateQueries({ queryKey: ['inventory-items', propertyId] })
      setDeleteConfirm(null)
    },
    onError: () => toast.error('Não foi possível remover o item.'),
  })

  const uploadImageMutation = useMutation({
    mutationFn: propertiesApi.uploadImage,
    onSuccess: (uploadedImageUrl) => {
      setImageUrl(uploadedImageUrl)
      toast.success('Foto adicionada!')
    },
    onError: () => toast.error('Não foi possível enviar a foto. Use JPG, PNG ou WEBP até 5 MB.'),
  })

  const isPending =
    createMutation.isPending ||
    updateMutation.isPending ||
    deleteMutation.isPending ||
    uploadImageMutation.isPending

  const handleNew = () => {
    resetForm()
    setCategoryId(categories[0]?.id || '')
    setShowForm(true)
  }

  const handleEdit = (item: InventoryItem) => {
    setEditing(item)
    setName(item.name)
    setCategoryId(item.category_id)
    setQuantityExpected(String(item.quantity_expected))
    setColor(item.color || '')
    setSerialNumber(item.serial_number || '')
    setBrand(item.brand || '')
    setModel(item.model || '')
    setImageUrl(item.image_url || '')
    setNotes(item.notes || '')
    setIsConsumable(Boolean(item.is_consumable))
    setShowForm(true)
  }

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    uploadImageMutation.mutate(file)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!categoryId) {
      toast.error('Cadastre uma categoria de inventário antes.')
      return
    }
    const payload: InventoryItemPayload = {
      category_id: categoryId,
      name: name.trim(),
      quantity_expected: Math.max(1, Number(quantityExpected) || 1),
      color: emptyToNull(color),
      serial_number: emptyToNull(serialNumber),
      brand: emptyToNull(brand),
      model: emptyToNull(model),
      image_url: emptyToNull(imageUrl),
      notes: emptyToNull(notes),
      is_consumable: isConsumable,
    }
    if (!payload.name) {
      toast.error('Informe o nome do item.')
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
      title={`Inventário${property ? ` — ${property.name}` : ''}`}
      subtitle="Lista fixa deste imóvel. Usada nos checklists internos de entrada/saída."
      action={
        <div className="flex max-w-full flex-wrap justify-end gap-2">
          <Link to="/properties">
            <Button variant="outline" className="h-11">
              <ArrowLeft className="mr-1 h-4 w-4" /> Imóveis
            </Button>
          </Link>
          <Link to={`/inventory-categories?property=${propertyId}`}>
            <Button variant="outline" className="h-11">Categorias</Button>
          </Link>
          <Button className="h-11" onClick={handleNew} disabled={categories.length === 0}>
            <Plus className="mr-1 h-4 w-4" /> Novo item
          </Button>
        </div>
      }
    >
      <div className="mb-4 flex flex-wrap gap-3">
        <Input
          label="Buscar"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Nome, marca, série, cor..."
        />
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-slate-700">Categoria</label>
          <select
            className={selectClassName}
            value={filterCategoryId}
            onChange={(e) => setFilterCategoryId(e.target.value)}
          >
            <option value="all">Todas</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {categories.length === 0 && (
        <Card className="mb-4 border-amber-200 bg-amber-50">
          <CardContent className="p-4 text-sm text-amber-900">
            Cadastre categorias deste imóvel antes de adicionar itens.{' '}
            <Link
              className="font-medium underline"
              to={`/inventory-categories?property=${propertyId}`}
            >
              Ir para categorias
            </Link>
          </CardContent>
        </Card>
      )}

      <FormModal
        open={showForm}
        title={editing ? 'Editar item' : 'Novo item do inventário'}
        description={
          editing
            ? undefined
            : 'Detalhes e foto ficam no inventário; no check-in/check-out só aparece nome e quantidade.'
        }
        onClose={resetForm}
      >
        <form onSubmit={handleSubmit} className="grid gap-4 sm:grid-cols-2">
          <Input
            label="Nome"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder={editing ? undefined : 'Ex.: TV, Micro-ondas'}
            required
          />
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-slate-700">Categoria</label>
            <select
              className={selectClassName}
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              required
            >
              <option value="" disabled>
                Selecione
              </option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>
          <Input
            label={isConsumable ? 'Quantidade mínima' : 'Quantidade esperada'}
            type="number"
            min="1"
            value={quantityExpected}
            onChange={(e) => setQuantityExpected(e.target.value)}
            required
          />
          <label className="flex items-center gap-2 self-end pb-2 text-sm text-slate-700 sm:col-span-1">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
              checked={isConsumable}
              onChange={(e) => setIsConsumable(e.target.checked)}
            />
            Insumo / consumível
            {!editing ? (
              <span className="text-xs text-slate-500">(papel, lençol, sabonete…)</span>
            ) : null}
          </label>
          <Input
            label="Cor"
            value={color}
            onChange={(e) => setColor(e.target.value)}
            placeholder={editing ? undefined : 'Ex.: Preto, Branco'}
          />
          <Input
            label="Marca"
            value={brand}
            onChange={(e) => setBrand(e.target.value)}
            placeholder={editing ? undefined : 'Ex.: Samsung'}
          />
          <Input
            label="Modelo"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder={editing ? undefined : 'Ex.: UN43T5300'}
          />
          <div className="sm:col-span-2">
            <Input
              label="Número de série"
              value={serialNumber}
              onChange={(e) => setSerialNumber(e.target.value)}
              placeholder={editing ? undefined : 'Opcional'}
            />
          </div>
          <div className="flex flex-col gap-2 sm:col-span-2">
            <span className="text-sm font-medium text-slate-700">Foto do item</span>
            <div className="flex flex-wrap items-center gap-3">
              <InventoryItemThumb name={name || 'Item'} imageUrl={imageUrl} />
              <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                onChange={handleImageUpload}
                className="hidden"
                id="inventory-item-image-upload"
              />
              <Button
                type="button"
                variant="outline"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploadImageMutation.isPending}
              >
                {uploadImageMutation.isPending ? (
                  <Loader2 className="mr-1 h-4 w-4 animate-spin" />
                ) : (
                  <Upload className="mr-1 h-4 w-4" />
                )}
                {uploadImageMutation.isPending ? 'Enviando...' : 'Selecionar foto'}
              </Button>
              {imageUrl ? (
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => {
                    setImageUrl('')
                    if (fileInputRef.current) fileInputRef.current.value = ''
                  }}
                >
                  Remover foto
                </Button>
              ) : null}
            </div>
            {!editing ? (
              <span className="text-xs text-slate-500">JPG, PNG ou WEBP, até 5 MB.</span>
            ) : null}
          </div>
          <div className="sm:col-span-2">
            <Input
              label="Outros detalhes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder={
                editing ? undefined : 'Ex.: controle na gaveta, arranhão leve na lateral'
              }
            />
          </div>
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

      {isLoading && (
        <div className="flex items-center justify-center py-12 text-slate-500">
          <Loader2 className="mr-2 h-8 w-8 animate-spin" />
          Carregando inventário...
        </div>
      )}

      {!isLoading && items.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center text-slate-500">
            <ClipboardList className="mx-auto mb-3 h-12 w-12 text-slate-300" />
            <p className="font-medium">Inventário vazio</p>
            <p className="mt-1 text-sm">Adicione os itens fixos deste imóvel.</p>
          </CardContent>
        </Card>
      )}

      {!isLoading &&
        grouped.map(([categoryName, categoryItems]) => (
          <div key={categoryName} className="mb-6">
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
              {categoryName}
            </h2>
            <div className="space-y-2">
              {categoryItems.map((item) => {
                const details = itemDetailLine(item)
                return (
                  <Card key={item.id}>
                    <CardContent className="flex items-center justify-between gap-3 p-4">
                      <div className="flex min-w-0 items-center gap-3">
                        <InventoryItemThumb name={item.name} imageUrl={item.image_url} />
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <h3 className="font-medium text-slate-900">{item.name}</h3>
                            <Badge variant="default">
                              {item.is_consumable ? 'Mín.' : 'Qtd.'} {item.quantity_expected}
                            </Badge>
                            {item.is_consumable ? (
                              <Badge variant="info">Insumo</Badge>
                            ) : null}
                          </div>
                          {details ? (
                            <p className="mt-1 truncate text-sm text-slate-600">{details}</p>
                          ) : null}
                          {item.notes ? (
                            <p className="mt-0.5 truncate text-sm text-slate-500">{item.notes}</p>
                          ) : null}
                        </div>
                      </div>
                      <div className="flex shrink-0 gap-2">
                        <Button size="sm" variant="outline" className="h-10 w-10" onClick={() => handleEdit(item)}>
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button size="sm" variant="ghost" className="h-10 w-10" onClick={() => setDeleteConfirm(item)}>
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </div>
        ))}

      <ConfirmDialog
        open={!!deleteConfirm}
        title="Remover item"
        message="O item será desativado e deixará de entrar em novos checklists."
        confirmLabel="Remover"
        variant="danger"
        isLoading={deleteMutation.isPending}
        onConfirm={() => deleteConfirm && deleteMutation.mutate(deleteConfirm.id)}
        onCancel={() => setDeleteConfirm(null)}
      />
    </PageContainer>
  )
}
