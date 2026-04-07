import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Loader2, Pencil, Plus, Tag, Trash2 } from 'lucide-react'
import { categoriesApi } from '@/api/categories'
import type { CategoryPayload } from '@/api/categories'
import PageContainer from '@/components/layout/PageContainer'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card, CardContent } from '@/components/ui/Card'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { FormModal } from '@/components/ui/FormModal'
import { Input } from '@/components/ui/Input'
import { useAuthStore } from '@/stores/authStore'
import { toast } from '@/stores/toastStore'
import type { Category, CategoryType } from '@/types/expense.types'

const selectClassName =
  'rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500'

type CategoryFilter = 'ALL' | CategoryType

const filterOptions: Array<{ value: CategoryFilter; label: string }> = [
  { value: 'ALL', label: 'Todas' },
  { value: 'EXPENSE', label: 'Despesas' },
  { value: 'REVENUE', label: 'Receitas' },
]

export default function CategoriesPage() {
  const queryClient = useQueryClient()
  const currentUserId = useAuthStore((state) => state.user?.id)
  const isSuperuser = useAuthStore((state) => state.user?.is_superuser ?? false)

  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<Category | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<Category | null>(null)
  const [filterType, setFilterType] = useState<CategoryFilter>('ALL')

  const [name, setName] = useState('')
  const [type, setType] = useState<CategoryType>('EXPENSE')
  const [color, setColor] = useState('#4f46e5')
  const [icon, setIcon] = useState('')

  const { data: allCategories = [], isLoading } = useQuery({
    queryKey: ['categories', currentUserId],
    queryFn: () => categoriesApi.list(),
    refetchOnMount: 'always',
  })

  const visibleCategories = useMemo(() => {
    if (isSuperuser) return allCategories
    return allCategories.filter((category) => category.user_id === currentUserId)
  }, [allCategories, currentUserId, isSuperuser])

  const categories = useMemo(() => {
    if (filterType === 'ALL') return visibleCategories
    return visibleCategories.filter((category) => category.type === filterType)
  }, [visibleCategories, filterType])

  const stats = useMemo(
    () => ({
      total: visibleCategories.length,
      expenses: visibleCategories.filter((category) => category.type === 'EXPENSE').length,
      revenues: visibleCategories.filter((category) => category.type === 'REVENUE').length,
    }),
    [visibleCategories]
  )

  const invalidateCategoryQueries = async () => {
    await queryClient.invalidateQueries({ queryKey: ['categories'] })
    await queryClient.invalidateQueries({ queryKey: ['expenses'] })
  }

  const createMutation = useMutation({
    mutationFn: categoriesApi.create,
    onSuccess: async () => {
      toast.success('Categoria criada com sucesso!')
      await invalidateCategoryQueries()
      resetForm()
    },
    onError: () => {
      toast.error('Erro ao criar categoria.')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CategoryPayload> }) =>
      categoriesApi.update(id, data),
    onSuccess: async () => {
      toast.success('Categoria atualizada com sucesso!')
      await invalidateCategoryQueries()
      resetForm()
    },
    onError: () => {
      toast.error('Erro ao atualizar categoria.')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: categoriesApi.delete,
    onSuccess: async () => {
      toast.success('Categoria excluida com sucesso!')
      await invalidateCategoryQueries()
      setDeleteConfirm(null)
    },
    onError: () => {
      toast.error('Nao foi possivel excluir a categoria.')
      setDeleteConfirm(null)
    },
  })

  const isPending =
    createMutation.isPending || updateMutation.isPending || deleteMutation.isPending

  const resetForm = () => {
    setName('')
    setType('EXPENSE')
    setColor('#4f46e5')
    setIcon('')
    setEditing(null)
    setShowForm(false)
  }

  const handleNew = () => {
    resetForm()
    setShowForm(true)
  }

  const handleEdit = (category: Category) => {
    setEditing(category)
    setName(category.name)
    setType(category.type)
    setColor(category.color || '#4f46e5')
    setIcon(category.icon || '')
    setShowForm(true)
  }

  const handleDeleteRequest = (category: Category) => {
    if (category.is_system) {
      toast.error('Categorias padrao nao podem ser excluidas.')
      return
    }
    setDeleteConfirm(category)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const payload = {
      name,
      type,
      color: color || null,
      icon: icon.trim() || null,
    }

    if (editing) {
      updateMutation.mutate({ id: editing.id, data: payload })
      return
    }

    createMutation.mutate(payload)
  }

  return (
    <PageContainer
      title="Categorias"
      subtitle="Gerencie as categorias usadas em receitas e despesas."
      action={
        <Button onClick={handleNew}>
          <Plus className="mr-1 h-4 w-4" />
          Nova Categoria
        </Button>
      }
    >
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-slate-500">Total</p>
            <p className="text-xl font-semibold text-slate-900">{stats.total}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-slate-500">Despesas</p>
            <p className="text-xl font-semibold text-red-600">{stats.expenses}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-slate-500">Receitas</p>
            <p className="text-xl font-semibold text-green-600">{stats.revenues}</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="flex flex-col gap-4 p-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-medium text-slate-900">Filtrar categorias</p>
            <p className="text-sm text-slate-500">Escolha o tipo que deseja visualizar.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {filterOptions.map((option) => (
              <Button
                key={option.value}
                type="button"
                variant={filterType === option.value ? 'primary' : 'outline'}
                onClick={() => setFilterType(option.value)}
              >
                {option.label}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      <FormModal
        open={showForm}
        title={editing ? 'Editar categoria' : 'Nova categoria'}
        description="Defina o nome, tipo, cor e icone da categoria."
        onClose={resetForm}
      >
        <form onSubmit={handleSubmit} className="grid gap-4 md:grid-cols-2">
          <Input
            label="Nome"
            placeholder="Ex.: Lavanderia"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />

          <label className="flex flex-col gap-1">
            <span className="text-sm font-medium text-slate-700">Tipo</span>
            <select
              className={selectClassName}
              value={type}
              onChange={(e) => setType(e.target.value as CategoryType)}
              required
            >
              <option value="EXPENSE">Despesa</option>
              <option value="REVENUE">Receita</option>
            </select>
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-sm font-medium text-slate-700">Cor</span>
            <input
              type="color"
              className="h-11 w-full rounded-lg border border-slate-300 bg-white px-2 py-1"
              value={color}
              onChange={(e) => setColor(e.target.value)}
            />
          </label>

          <Input
            label="Icone"
            placeholder="Ex.: home, wrench, sparkles"
            value={icon}
            onChange={(e) => setIcon(e.target.value)}
          />

          <div className="md:col-span-2 flex justify-end gap-2 border-t border-slate-200 pt-4">
            <Button type="button" variant="outline" onClick={resetForm}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createMutation.isPending || updateMutation.isPending}>
              {createMutation.isPending || updateMutation.isPending ? (
                <Loader2 className="mr-1 h-4 w-4 animate-spin" />
              ) : null}
              {editing ? 'Salvar alteracoes' : 'Criar categoria'}
            </Button>
          </div>
        </form>
      </FormModal>

      {isLoading && (
        <div className="flex items-center justify-center py-12 text-slate-500">
          <Loader2 className="mr-2 h-8 w-8 animate-spin" />
          Carregando...
        </div>
      )}

      {!isLoading && categories.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center text-slate-500">
            <Tag className="mx-auto mb-3 h-12 w-12 text-slate-300" />
            <p className="font-medium">Nenhuma categoria encontrada</p>
            <p className="mt-1 text-sm">Crie uma categoria para organizar receitas e despesas.</p>
          </CardContent>
        </Card>
      )}

      {!isLoading && categories.length > 0 && (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-left text-slate-500">
                    <th className="px-4 py-3 font-medium">Categoria</th>
                    <th className="px-4 py-3 font-medium">Tipo</th>
                    <th className="px-4 py-3 font-medium">Cor</th>
                    <th className="px-4 py-3 font-medium">Icone</th>
                    <th className="px-4 py-3 font-medium">Origem</th>
                    <th className="px-4 py-3 font-medium text-right">Acoes</th>
                  </tr>
                </thead>
                <tbody>
                  {categories.map((category) => (
                    <tr key={category.id} className="border-b border-slate-100 last:border-b-0">
                      <td className="px-4 py-3 font-medium text-slate-900">{category.name}</td>
                      <td className="px-4 py-3">
                        <Badge variant={category.type === 'EXPENSE' ? 'danger' : 'success'}>
                          {category.type === 'EXPENSE' ? 'Despesa' : 'Receita'}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2 text-slate-600">
                          <span
                            className="h-4 w-4 rounded-full border border-slate-200"
                            style={{ backgroundColor: category.color || '#cbd5e1' }}
                          />
                          <span>{category.color || 'Sem cor'}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-slate-600">{category.icon || '-'}</td>
                      <td className="px-4 py-3">
                        <Badge variant={category.is_system ? 'info' : 'default'}>
                          {category.is_system ? 'Padrao' : 'Personalizada'}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex justify-end gap-2">
                          <Button type="button" size="sm" variant="outline" onClick={() => handleEdit(category)}>
                            <Pencil className="h-3 w-3" />
                          </Button>
                          <Button
                            type="button"
                            size="sm"
                            variant="ghost"
                            onClick={() => handleDeleteRequest(category)}
                            disabled={isPending}
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
        title="Excluir categoria"
        message={`Tem certeza que deseja excluir a categoria "${deleteConfirm?.name}"?`}
        confirmLabel="Excluir"
        variant="danger"
        isLoading={deleteMutation.isPending}
        onConfirm={() => deleteConfirm && deleteMutation.mutate(deleteConfirm.id)}
        onCancel={() => setDeleteConfirm(null)}
      />
    </PageContainer>
  )
}
