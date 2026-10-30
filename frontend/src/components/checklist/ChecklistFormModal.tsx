import { useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  AlertTriangle,
  ArrowLeft,
  Camera,
  CheckCircle2,
  ChevronRight,
  Loader2,
  RotateCcw,
  Trash2,
} from 'lucide-react'
import { checklistsApi } from '@/api/inventory'
import { propertiesApi } from '@/api/properties'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { FormModal } from '@/components/ui/FormModal'
import { isChecklistProfile } from '@/lib/appProfile'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/stores/authStore'
import { toast } from '@/stores/toastStore'
import type {
  ChecklistItem,
  ChecklistItemCondition,
  ChecklistType,
  StayChecklist,
} from '@/types/inventory.types'

const fieldClassName =
  'w-full rounded-xl border border-slate-300 bg-white px-3 py-3 text-base text-slate-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 disabled:bg-slate-100'

const conditionOptions: Array<{ value: ChecklistItemCondition; label: string }> = [
  { value: 'ok', label: 'OK' },
  { value: 'missing', label: 'Faltando' },
  { value: 'damaged', label: 'Danificado' },
  { value: 'other', label: 'Outro' },
]

const consumableConditionOptions: Array<{ value: ChecklistItemCondition; label: string }> = [
  { value: 'ok', label: 'Estoque ok' },
  { value: 'missing', label: 'Falta repor' },
  { value: 'damaged', label: 'Impróprio / sujo' },
  { value: 'other', label: 'Outro' },
]

type DraftItem = {
  id: string
  quantity_found: string
  condition: ChecklistItemCondition
  incident_notes: string
  incident_image_url: string
}

function toDraft(items: ChecklistItem[]): Record<string, DraftItem> {
  return Object.fromEntries(
    items.map((item) => [
      item.id,
      {
        id: item.id,
        quantity_found:
          item.quantity_found === null || item.quantity_found === undefined
            ? String(item.quantity_expected)
            : String(item.quantity_found),
        condition: item.condition,
        incident_notes: item.incident_notes || '',
        incident_image_url: item.incident_image_url || '',
      },
    ])
  )
}

function typeLabel(type: ChecklistType) {
  return type === 'checkin' ? 'Checklist de entrada' : 'Checklist de saída'
}

function itemHasIssue(
  draft: DraftItem,
  expected: number
): boolean {
  const found = Number(draft.quantity_found)
  return (
    draft.condition !== 'ok' ||
    Boolean(draft.incident_notes.trim()) ||
    Boolean(draft.incident_image_url.trim()) ||
    (!Number.isNaN(found) && found !== expected)
  )
}

function draftItemPayload(item: DraftItem) {
  return {
    id: item.id,
    quantity_found: Number(item.quantity_found) || 0,
    condition: item.condition,
    incident_notes: item.incident_notes.trim() || null,
    incident_image_url: item.incident_image_url.trim() || null,
  }
}

interface ChecklistFormModalProps {
  open: boolean
  revenueId: string | null
  checklistType: ChecklistType | null
  onClose: () => void
}

export default function ChecklistFormModal({
  open,
  revenueId,
  checklistType,
  onClose,
}: ChecklistFormModalProps) {
  const queryClient = useQueryClient()
  const user = useAuthStore((state) => state.user)
  const canReopen = !isChecklistProfile(user)
  const [checklistId, setChecklistId] = useState<string | null>(null)
  const [draftItems, setDraftItems] = useState<Record<string, DraftItem>>({})
  const [generalNotes, setGeneralNotes] = useState('')
  const [bootstrapping, setBootstrapping] = useState(false)
  const [activeCategory, setActiveCategory] = useState<string | null>(null)
  const [confirmedCategories, setConfirmedCategories] = useState<Record<string, boolean>>({})
  const [uploadingItemId, setUploadingItemId] = useState<string | null>(null)
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose

  const { data: checklist, isLoading, isFetching } = useQuery({
    queryKey: ['checklist', checklistId],
    queryFn: () => checklistsApi.get(checklistId!),
    enabled: open && !!checklistId,
  })

  useEffect(() => {
    if (!open || !revenueId || !checklistType) {
      setChecklistId(null)
      setDraftItems({})
      setGeneralNotes('')
      setBootstrapping(false)
      setActiveCategory(null)
      setConfirmedCategories({})
      return
    }

    let cancelled = false
    const bootstrap = async () => {
      setBootstrapping(true)
      setChecklistId(null)
      setActiveCategory(null)
      setConfirmedCategories({})
      try {
        const created = await checklistsApi.create(revenueId, checklistType)
        if (cancelled) return
        queryClient.setQueryData(['checklist', created.id], created)
        setChecklistId(created.id)
        setDraftItems(toDraft(created.items))
        setGeneralNotes(created.general_notes || '')
        setConfirmedCategories({})
        await queryClient.invalidateQueries({ queryKey: ['conferences'] })
      } catch (err: unknown) {
        if (!cancelled) {
          const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data
            ?.detail
          toast.error(
            detail ||
              'Não foi possível abrir o checklist. Cadastre o inventário do imóvel antes.'
          )
          onCloseRef.current()
        }
      } finally {
        if (!cancelled) setBootstrapping(false)
      }
    }

    void bootstrap()
    return () => {
      cancelled = true
    }
  }, [open, revenueId, checklistType])

  useEffect(() => {
    if (!checklist) return
    setDraftItems(toDraft(checklist.items))
    setGeneralNotes(checklist.general_notes || '')
  }, [checklist])

  const grouped = useMemo(() => {
    if (!checklist) return [] as Array<[string, ChecklistItem[]]>
    const map = new Map<string, ChecklistItem[]>()
    const ordered = [...checklist.items].sort((a, b) => a.sort_order - b.sort_order)
    for (const item of ordered) {
      const key = item.category_name || 'Sem categoria'
      const list = map.get(key) || []
      list.push(item)
      map.set(key, list)
    }
    return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b))
  }, [checklist])

  const categoryNames = useMemo(() => grouped.map(([name]) => name), [grouped])

  const categoryStats = useMemo(() => {
    return Object.fromEntries(
      grouped.map(([categoryName, items]) => {
        const issues = items.filter((item) => {
          const draft = draftItems[item.id]
          if (!draft) return false
          return itemHasIssue(draft, item.quantity_expected)
        }).length
        return [
          categoryName,
          {
            total: items.length,
            issues,
            confirmed: Boolean(confirmedCategories[categoryName]),
          },
        ]
      })
    ) as Record<string, { total: number; issues: number; confirmed: boolean }>
  }, [grouped, draftItems, confirmedCategories])

  const allCategoriesConfirmed =
    categoryNames.length > 0 && categoryNames.every((name) => confirmedCategories[name])

  const incidentCount = useMemo(() => {
    return Object.values(draftItems).filter((item) => {
      const original = checklist?.items.find((line) => line.id === item.id)
      return itemHasIssue(item, original?.quantity_expected ?? 0)
    }).length
  }, [draftItems, checklist])

  const saveMutation = useMutation({
    mutationFn: () =>
      checklistsApi.updateItems(checklistId!, {
        general_notes: generalNotes,
        items: Object.values(draftItems).map(draftItemPayload),
      }),
    onSuccess: async (data: StayChecklist) => {
      toast.success('Checklist salvo.')
      setDraftItems(toDraft(data.items))
      setGeneralNotes(data.general_notes || '')
      await queryClient.invalidateQueries({ queryKey: ['checklist', checklistId] })
      await queryClient.invalidateQueries({ queryKey: ['revenue-checklists', revenueId] })
    },
    onError: () => toast.error('Erro ao salvar checklist.'),
  })

  const completeMutation = useMutation({
    mutationFn: async () => {
      await checklistsApi.updateItems(checklistId!, {
        general_notes: generalNotes,
        items: Object.values(draftItems).map(draftItemPayload),
      })
      return checklistsApi.complete(checklistId!)
    },
    onSuccess: async () => {
      toast.success('Checklist concluído.')
      await queryClient.invalidateQueries({ queryKey: ['checklist', checklistId] })
      await queryClient.invalidateQueries({ queryKey: ['revenue-checklists', revenueId] })
      await queryClient.invalidateQueries({ queryKey: ['conferences'] })
      await queryClient.invalidateQueries({ queryKey: ['revenues'] })
      onClose()
    },
    onError: () => toast.error('Erro ao concluir checklist.'),
  })

  const reopenMutation = useMutation({
    mutationFn: () => checklistsApi.reopen(checklistId!),
    onSuccess: async (data) => {
      toast.success('Checklist marcado como não feito. Pode refazer agora.')
      setDraftItems(toDraft(data.items))
      setGeneralNotes(data.general_notes || '')
      setConfirmedCategories({})
      setActiveCategory(null)
      await queryClient.invalidateQueries({ queryKey: ['checklist', checklistId] })
      await queryClient.invalidateQueries({ queryKey: ['revenue-checklists', revenueId] })
      await queryClient.invalidateQueries({ queryKey: ['conferences'] })
      await queryClient.invalidateQueries({ queryKey: ['revenues'] })
    },
    onError: () => toast.error('Não foi possível reabrir o checklist.'),
  })

  const isReadOnly = checklist?.status === 'completed'
  const busy =
    bootstrapping ||
    isLoading ||
    isFetching ||
    saveMutation.isPending ||
    completeMutation.isPending ||
    reopenMutation.isPending ||
    Boolean(uploadingItemId)

  const updateDraft = (id: string, patch: Partial<DraftItem>) => {
    setDraftItems((prev) => ({
      ...prev,
      [id]: { ...prev[id], ...patch },
    }))
    // Se mexer nos itens, a categoria deixa de estar "confirmada"
    const item = checklist?.items.find((line) => line.id === id)
    if (item) {
      const categoryName = item.category_name || 'Sem categoria'
      setConfirmedCategories((prev) => ({ ...prev, [categoryName]: false }))
    }
  }

  const confirmActiveCategory = () => {
    if (!activeCategory) return
    setConfirmedCategories((prev) => ({ ...prev, [activeCategory]: true }))
    const currentIndex = categoryNames.indexOf(activeCategory)
    const next = categoryNames[currentIndex + 1]
    if (next) {
      setActiveCategory(next)
      toast.success(`${activeCategory} conferida. Agora: ${next}`)
    } else {
      setActiveCategory(null)
      toast.success(`${activeCategory} conferida. Todas as áreas foram percorridas.`)
    }
  }

  const handleIncidentPhoto = async (itemId: string, file: File | undefined) => {
    if (!file) return
    const allowed = ['image/jpeg', 'image/png', 'image/webp']
    if (!allowed.includes(file.type) && !file.type.startsWith('image/')) {
      toast.error('Use foto JPG, PNG ou WEBP.')
      return
    }
    setUploadingItemId(itemId)
    try {
      const imageUrl = await propertiesApi.uploadImage(file)
      updateDraft(itemId, { incident_image_url: imageUrl })
      toast.success('Foto da intercorrência anexada.')
    } catch {
      toast.error('Não foi possível anexar a foto. Tente novamente.')
    } finally {
      setUploadingItemId(null)
    }
  }

  const activeItems = useMemo(() => {
    if (!activeCategory) return []
    return grouped.find(([name]) => name === activeCategory)?.[1] || []
  }, [grouped, activeCategory])

  const modalTitle = activeCategory
    ? `${activeCategory}`
    : checklistType
      ? typeLabel(checklistType)
      : 'Checklist'

  const modalDescription = activeCategory
    ? 'Confira os itens desta área. Depois marque como conferida.'
    : 'Entre em cada área, faça a conferência e avance. Áreas prontas ficam verdes.'

  return (
    <FormModal
      open={open}
      fullHeight
      title={modalTitle}
      description={modalDescription}
      onClose={onClose}
    >
      {busy && !checklist ? (
        <div className="flex items-center justify-center py-16 text-slate-500">
          <Loader2 className="mr-2 h-6 w-6 animate-spin" />
          Preparando checklist...
        </div>
      ) : (
        <div className="space-y-4 pb-28 sm:pb-4">
          {activeCategory ? (
            <>
              <button
                type="button"
                className="inline-flex items-center gap-1 text-sm font-medium text-slate-600"
                onClick={() => setActiveCategory(null)}
              >
                <ArrowLeft className="h-4 w-4" />
                Todas as áreas
              </button>

              <div className="space-y-3">
                {activeItems.map((item) => {
                  const draft = draftItems[item.id]
                  if (!draft) return null
                  const needsNotes = draft.condition !== 'ok'
                  const hasIssue = itemHasIssue(draft, item.quantity_expected)
                  return (
                    <article
                      key={item.id}
                      className={cn(
                        'rounded-2xl border p-3.5 shadow-sm',
                        hasIssue
                          ? 'border-amber-300 bg-amber-50'
                          : 'border-slate-200 bg-slate-50'
                      )}
                    >
                      <div className="mb-3">
                        <div className="flex flex-wrap items-center gap-2">
                          <h4 className="text-base font-semibold leading-snug text-slate-900">
                            {item.item_name}
                          </h4>
                          {item.is_consumable ? (
                            <Badge variant="info">Insumo</Badge>
                          ) : null}
                        </div>
                        <p className="mt-0.5 text-sm text-slate-500">
                          {item.is_consumable
                            ? `Mínimo no imóvel: ${item.quantity_expected}`
                            : `Esperado: ${item.quantity_expected}`}
                        </p>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div className="flex flex-col gap-1.5">
                          <label className="text-sm font-medium text-slate-700">
                            {item.is_consumable ? 'Qtd. no local' : 'Encontrado'}
                          </label>
                          <input
                            type="number"
                            min={0}
                            inputMode="numeric"
                            className={fieldClassName}
                            value={draft.quantity_found}
                            disabled={isReadOnly}
                            onChange={(e) =>
                              updateDraft(item.id, { quantity_found: e.target.value })
                            }
                          />
                        </div>
                        <div className="flex flex-col gap-1.5">
                          <label className="text-sm font-medium text-slate-700">
                            {item.is_consumable ? 'Situação' : 'Condição'}
                          </label>
                          <select
                            className={fieldClassName}
                            value={draft.condition}
                            disabled={isReadOnly}
                            onChange={(e) =>
                              updateDraft(item.id, {
                                condition: e.target.value as ChecklistItemCondition,
                              })
                            }
                          >
                            {(item.is_consumable
                              ? consumableConditionOptions
                              : conditionOptions
                            ).map((option) => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>

                      {(hasIssue || needsNotes || draft.incident_notes || draft.incident_image_url) && (
                        <div className="mt-3 space-y-3">
                          <div className="flex flex-col gap-1.5">
                            <label className="text-sm font-medium text-slate-700">
                              Intercorrência
                            </label>
                            <textarea
                              className={`${fieldClassName} min-h-[96px]`}
                              placeholder={
                                item.is_consumable
                                  ? 'Ex.: só restava 1 rolo; repor no armário'
                                  : 'Ex.: sofá do living rasgado no braço esquerdo'
                              }
                              value={draft.incident_notes}
                              disabled={isReadOnly}
                              onChange={(e) =>
                                updateDraft(item.id, { incident_notes: e.target.value })
                              }
                            />
                          </div>

                          <div className="flex flex-col gap-2">
                            <span className="text-sm font-medium text-slate-700">
                              Foto da intercorrência
                            </span>
                            {draft.incident_image_url ? (
                              <img
                                src={draft.incident_image_url}
                                alt={`Intercorrência — ${item.item_name}`}
                                className="max-h-56 w-full rounded-xl object-cover"
                              />
                            ) : null}
                            {!isReadOnly ? (
                              <div className="flex flex-wrap gap-2">
                                <label className="inline-flex">
                                  <input
                                    type="file"
                                    accept="image/jpeg,image/png,image/webp,image/*"
                                    capture="environment"
                                    className="hidden"
                                    disabled={busy}
                                    onChange={(e) => {
                                      const file = e.target.files?.[0]
                                      void handleIncidentPhoto(item.id, file)
                                      e.target.value = ''
                                    }}
                                  />
                                  <span
                                    className={cn(
                                      'inline-flex h-11 cursor-pointer items-center justify-center rounded-lg border border-slate-300 bg-white px-3 text-sm font-medium text-slate-700',
                                      busy && 'pointer-events-none opacity-50'
                                    )}
                                  >
                                    {uploadingItemId === item.id ? (
                                      <Loader2 className="mr-1 h-4 w-4 animate-spin" />
                                    ) : (
                                      <Camera className="mr-1 h-4 w-4" />
                                    )}
                                    {draft.incident_image_url ? 'Trocar foto' : 'Tirar / anexar foto'}
                                  </span>
                                </label>
                                {draft.incident_image_url ? (
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    className="h-11"
                                    disabled={busy}
                                    onClick={() => updateDraft(item.id, { incident_image_url: '' })}
                                  >
                                    <Trash2 className="mr-1 h-4 w-4 text-red-500" />
                                    Remover
                                  </Button>
                                ) : null}
                              </div>
                            ) : null}
                            <span className="text-xs text-slate-500">
                              No celular abre a câmera. Formatos: JPG, PNG ou WEBP (até 5 MB).
                            </span>
                          </div>
                        </div>
                      )}
                    </article>
                  )
                })}
              </div>

              {!isReadOnly && (
                <div className="fixed inset-x-0 bottom-0 z-40 border-t border-slate-200 bg-white/95 p-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] backdrop-blur sm:static sm:border-0 sm:bg-transparent sm:p-0 sm:pb-0 sm:backdrop-blur-none">
                  <Button
                    type="button"
                    className="h-12 w-full text-base"
                    disabled={busy}
                    onClick={confirmActiveCategory}
                  >
                    <CheckCircle2 className="mr-1 h-4 w-4" />
                    {activeCategory} conferida
                  </Button>
                </div>
              )}
            </>
          ) : (
            <>
              {incidentCount > 0 ? (
                <div className="flex items-start gap-2 rounded-2xl border border-amber-200 bg-amber-50 px-3 py-3 text-sm text-amber-900">
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                  <span>{incidentCount} item(ns) com intercorrência no total.</span>
                </div>
              ) : (
                <div className="flex items-start gap-2 rounded-2xl border border-emerald-200 bg-emerald-50 px-3 py-3 text-sm text-emerald-900">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
                  <span>Entre em cada ambiente e confira os itens.</span>
                </div>
              )}

              {checklist ? (
                <div className="space-y-2">
                  <div className="flex flex-wrap gap-2">
                    <Badge variant={checklist.status === 'completed' ? 'success' : 'default'}>
                      {checklist.status === 'completed' ? 'Concluído' : 'Rascunho'}
                    </Badge>
                    <Badge variant={allCategoriesConfirmed ? 'success' : 'default'}>
                      {Object.values(confirmedCategories).filter(Boolean).length}/
                      {categoryNames.length} áreas
                    </Badge>
                  </div>
                  {checklist.status === 'completed' && checklist.performed_by_name ? (
                    <p className="text-sm text-slate-600">
                      Concluído por{' '}
                      <span className="font-medium text-slate-900">
                        {checklist.performed_by_name}
                      </span>
                      {checklist.performed_at
                        ? ` · ${new Date(checklist.performed_at).toLocaleString('pt-BR')}`
                        : null}
                    </p>
                  ) : null}
                </div>
              ) : null}

              <div className="space-y-3">
                {grouped.map(([categoryName, items]) => {
                  const stats = categoryStats[categoryName]
                  const confirmed = stats?.confirmed
                  return (
                    <button
                      key={categoryName}
                      type="button"
                      onClick={() => setActiveCategory(categoryName)}
                      className={cn(
                        'flex w-full items-center gap-3 rounded-2xl border px-4 py-4 text-left transition-colors',
                        confirmed
                          ? 'border-emerald-300 bg-emerald-50'
                          : 'border-slate-200 bg-white hover:bg-slate-50'
                      )}
                    >
                      <div
                        className={cn(
                          'flex h-11 w-11 shrink-0 items-center justify-center rounded-full',
                          confirmed ? 'bg-emerald-500 text-white' : 'bg-slate-100 text-slate-500'
                        )}
                      >
                        {confirmed ? (
                          <CheckCircle2 className="h-5 w-5" />
                        ) : (
                          <span className="text-sm font-semibold">{items.length}</span>
                        )}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-base font-semibold text-slate-900">{categoryName}</p>
                        <p className="text-sm text-slate-500">
                          {confirmed
                            ? stats.issues > 0
                              ? `Conferida · ${stats.issues} intercorrência(s)`
                              : 'Conferida'
                            : `${items.length} item(ns) · tocar para conferir`}
                        </p>
                      </div>
                      <ChevronRight className="h-5 w-5 shrink-0 text-slate-400" />
                    </button>
                  )
                })}
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-slate-700">
                  Observações gerais da visita
                </label>
                <textarea
                  className={`${fieldClassName} min-h-[96px]`}
                  placeholder="Qualquer coisa fora do comum na visita"
                  value={generalNotes}
                  disabled={isReadOnly}
                  onChange={(e) => setGeneralNotes(e.target.value)}
                />
              </div>

              {isReadOnly && canReopen ? (
                <div className="rounded-2xl border border-amber-200 bg-amber-50 p-3">
                  <p className="mb-2 text-sm text-amber-900">
                    Checklist concluído
                    {checklist?.performed_by_name
                      ? ` por ${checklist.performed_by_name}`
                      : ''}
                    . Se houve erro, marque como não feito para refazer.
                  </p>
                  <Button
                    type="button"
                    variant="outline"
                    className="h-11 w-full border-amber-300 text-amber-900 hover:bg-amber-100"
                    disabled={busy}
                    onClick={() => reopenMutation.mutate()}
                  >
                    {reopenMutation.isPending ? (
                      <Loader2 className="mr-1 h-4 w-4 animate-spin" />
                    ) : (
                      <RotateCcw className="mr-1 h-4 w-4" />
                    )}
                    Marcar como não feito
                  </Button>
                </div>
              ) : null}

              {!isReadOnly && (
                <div className="fixed inset-x-0 bottom-0 z-40 border-t border-slate-200 bg-white/95 p-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] backdrop-blur sm:static sm:border-0 sm:bg-transparent sm:p-0 sm:pb-0 sm:backdrop-blur-none">
                  <div className="mx-auto flex max-w-3xl flex-col gap-2 sm:flex-row sm:justify-end">
                    <Button
                      type="button"
                      variant="outline"
                      className="h-12 w-full text-base sm:w-auto"
                      disabled={busy}
                      onClick={() => saveMutation.mutate()}
                    >
                      {saveMutation.isPending ? (
                        <Loader2 className="mr-1 h-4 w-4 animate-spin" />
                      ) : null}
                      Salvar rascunho
                    </Button>
                    <Button
                      type="button"
                      className="h-12 w-full text-base sm:w-auto"
                      disabled={busy || !allCategoriesConfirmed}
                      onClick={() => completeMutation.mutate()}
                    >
                      {completeMutation.isPending ? (
                        <Loader2 className="mr-1 h-4 w-4 animate-spin" />
                      ) : null}
                      {allCategoriesConfirmed
                        ? 'Concluir checklist'
                        : 'Conferir todas as áreas'}
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </FormModal>
  )
}
