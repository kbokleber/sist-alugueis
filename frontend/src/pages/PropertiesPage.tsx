import { useRef, useState, type ChangeEvent } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { propertiesApi } from '@/api/properties'
import PageContainer from '@/components/layout/PageContainer'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { FormModal } from '@/components/ui/FormModal'
import { toast } from '@/stores/toastStore'
import { formatMoney } from '@/lib/utils'
import { Plus, Pencil, Trash2, Building, Loader2, Upload } from 'lucide-react'
import type { Property } from '@/types/property.types'

function PropertyImage({ property }: { property: Property }) {
  const [hasError, setHasError] = useState(false)

  if (!property.image_url || hasError) {
    return (
      <div className="flex h-40 w-full items-center justify-center rounded-lg bg-slate-100 text-slate-400">
        <Building className="h-10 w-10" />
      </div>
    )
  }

  return (
    <img
      src={property.image_url}
      alt={property.name}
      className="h-40 w-full rounded-lg bg-slate-50 object-contain"
      onError={() => setHasError(true)}
    />
  )
}

function PropertyImagePreview({ name, imageUrl }: { name: string; imageUrl: string }) {
  const [hasError, setHasError] = useState(false)

  if (!imageUrl || hasError) {
    return (
      <div className="flex h-32 w-full items-center justify-center rounded-lg border border-dashed border-slate-300 bg-slate-50 text-slate-400">
        <Building className="h-8 w-8" />
      </div>
    )
  }

  return (
    <img
      src={imageUrl}
      alt={name || 'Preview do imóvel'}
      className="h-32 w-full rounded-lg bg-slate-50 object-contain"
      onError={() => setHasError(true)}
    />
  )
}

export default function PropertiesPage() {
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<Property | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)

  const [code, setCode] = useState('')
  const [name, setName] = useState('')
  const [address, setAddress] = useState('')
  const [imageUrl, setImageUrl] = useState('')
  const [propertyValue, setPropertyValue] = useState('')
  const [depreciation, setDepreciation] = useState('0.5')
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const queryClient = useQueryClient()

  const { data: properties = [], isLoading } = useQuery({
    queryKey: ['properties'],
    queryFn: propertiesApi.list,
  })

  const createMutation = useMutation({
    mutationFn: (data: { code?: string; name: string; address: string; image_url?: string; property_value: number; monthly_depreciation_percent: number }) =>
      propertiesApi.create(data),
    onSuccess: () => {
      toast.success('Imóvel criado com sucesso!')
      queryClient.invalidateQueries({ queryKey: ['properties'] })
      resetForm()
    },
    onError: () => {
      toast.error('Erro ao criar imóvel. Verifique os dados.')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof propertiesApi.update>[1] }) =>
      propertiesApi.update(id, data),
    onSuccess: () => {
      toast.success('Imóvel atualizado com sucesso!')
      queryClient.invalidateQueries({ queryKey: ['properties'] })
      resetForm()
    },
    onError: () => {
      toast.error('Erro ao atualizar imóvel.')
    },
  })

  const uploadImageMutation = useMutation({
    mutationFn: propertiesApi.uploadImage,
    onSuccess: (uploadedImageUrl) => {
      setImageUrl(uploadedImageUrl)
      toast.success('Imagem enviada com sucesso!')
    },
    onError: () => {
      toast.error('Erro ao enviar imagem do imóvel.')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: propertiesApi.delete,
    onSuccess: () => {
      toast.success('Imóvel excluído com sucesso!')
      setDeleteConfirm(null)
      queryClient.invalidateQueries({ queryKey: ['properties'] })
    },
    onError: () => {
      toast.error('Erro ao excluir imóvel.')
      setDeleteConfirm(null)
    },
  })

  const resetForm = () => {
    setCode('')
    setName('')
    setAddress('')
    setImageUrl('')
    setPropertyValue('')
    setDepreciation('0.5')
    setShowForm(false)
    setEditing(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleEdit = (property: Property) => {
    setEditing(property)
    setCode(property.code || '')
    setName(property.name)
    setAddress(property.address || '')
    setImageUrl(property.image_url || '')
    setPropertyValue(String(property.property_value))
    setDepreciation(String(property.monthly_depreciation_percent))
    setShowForm(true)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const data = {
      code: code || undefined,
      name,
      address: address || undefined,
      image_url: imageUrl || undefined,
      property_value: Number(propertyValue),
      monthly_depreciation_percent: Number(depreciation),
    }
    if (editing) {
      updateMutation.mutate({ id: editing.id, data })
    } else {
      createMutation.mutate(data)
    }
  }

  const handleImageUpload = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    uploadImageMutation.mutate(file)
  }

  const isPending = createMutation.isPending || updateMutation.isPending || uploadImageMutation.isPending

  return (
    <PageContainer
      title="Imóveis"
      action={
        <Button onClick={() => setShowForm(true)}>
          <Plus className="h-4 w-4 mr-1" /> Novo Imóvel
        </Button>
      }
    >
      <FormModal
        open={showForm}
        title={editing ? 'Editar imóvel' : 'Novo imóvel'}
        description="Preencha os dados do imóvel antes de salvar."
        onClose={resetForm}
      >
        <form onSubmit={handleSubmit} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Input
            label="Código do Imóvel"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="Ex: IMV-001"
          />
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
          <div className="flex flex-col gap-2 sm:col-span-2 lg:col-span-4">
            <span className="text-sm font-medium text-slate-700">Imagem do imóvel</span>
            <PropertyImagePreview name={name} imageUrl={imageUrl} />
            <div className="flex flex-wrap items-center gap-3">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                onChange={handleImageUpload}
                className="hidden"
                id="property-image-upload"
              />
              <Button
                type="button"
                variant="outline"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploadImageMutation.isPending}
              >
                {uploadImageMutation.isPending ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <Upload className="mr-1 h-4 w-4" />}
                {uploadImageMutation.isPending ? 'Enviando imagem...' : 'Selecionar imagem'}
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
                  Remover imagem
                </Button>
              ) : null}
              <span className="text-xs text-slate-500">Formatos: JPG, PNG ou WEBP, até 5 MB.</span>
            </div>
          </div>
          <Input
            label="Valor do Imóvel (R$)"
            type="number"
            value={propertyValue}
            onChange={(e) => setPropertyValue(e.target.value)}
            placeholder="500000"
            required
          />
          <Input
            label="Depreciação (%/mês)"
            type="number"
            step="0.1"
            value={depreciation}
            onChange={(e) => setDepreciation(e.target.value)}
            placeholder="0.5"
          />
          <div className="sm:col-span-2 lg:col-span-4 flex justify-end gap-2 border-t border-slate-200 pt-4">
            <Button type="button" variant="outline" onClick={resetForm}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : null}
              {isPending ? 'Salvando...' : editing ? 'Salvar alterações' : 'Criar imóvel'}
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

      {!isLoading && properties.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center text-slate-500">
            <Building className="mx-auto h-12 w-12 text-slate-300 mb-3" />
            <p className="font-medium">Nenhum imóvel cadastrado</p>
            <p className="text-sm mt-1">Clique em "Novo Imóvel" para começar</p>
          </CardContent>
        </Card>
      )}

      {!isLoading && properties.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {properties.map((property) => (
            <Card key={property.id} className="mx-auto w-full max-w-sm">
              <CardContent className="p-4">
                <div className="mb-4">
                  <PropertyImage property={property} />
                </div>
                <div className="flex items-start justify-between">
                  <div className="min-w-0 flex-1">
                    <h3 className="font-semibold text-slate-900 truncate">{property.name}</h3>
                    <p className="text-sm text-slate-500 mt-1 truncate">Código: {property.code || 'Sem código'}</p>
                    <p className="text-sm text-slate-500 mt-1 truncate">{property.address || 'Sem endereço'}</p>
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
                  <Button size="sm" variant="outline" onClick={() => handleEdit(property)}>
                    <Pencil className="h-3 w-3" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setDeleteConfirm(property.id)}
                  >
                    <Trash2 className="h-3 w-3 text-red-500" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <ConfirmDialog
        open={!!deleteConfirm}
        title="Excluir Imóvel"
        message="Tem certeza que deseja excluir este imóvel? Esta ação não pode ser desfeita."
        confirmLabel="Excluir"
        variant="danger"
        isLoading={deleteMutation.isPending}
        onConfirm={() => deleteConfirm && deleteMutation.mutate(deleteConfirm)}
        onCancel={() => setDeleteConfirm(null)}
      />
    </PageContainer>
  )
}
