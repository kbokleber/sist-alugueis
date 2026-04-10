import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ChevronLeft, ChevronRight, CalendarDays, ArrowLeft } from 'lucide-react'
import { propertiesApi } from '@/api/properties'
import { revenuesApi } from '@/api/revenues'
import PageContainer from '@/components/layout/PageContainer'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { FormModal } from '@/components/ui/FormModal'
import type { Revenue } from '@/types/revenue.types'

const WEEKDAY_LABELS = ['seg.', 'ter.', 'qua.', 'qui.', 'sex.', 'sáb.', 'dom.']

function formatIsoDate(date: Date): string {
  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

function addDays(date: Date, amount: number): Date {
  const value = new Date(date)
  value.setDate(value.getDate() + amount)
  return value
}

function startOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), 1)
}

function endOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth() + 1, 0)
}

function startOfCalendarGrid(date: Date): Date {
  const firstDay = startOfMonth(date)
  const dayOffset = (firstDay.getDay() + 6) % 7
  return addDays(firstDay, -dayOffset)
}

function endOfCalendarGrid(date: Date): Date {
  const lastDay = endOfMonth(date)
  const dayOffset = (7 - ((lastDay.getDay() + 6) % 7) - 1 + 7) % 7
  return addDays(lastDay, dayOffset)
}

function sameDay(left: Date, right: Date): boolean {
  return formatIsoDate(left) === formatIsoDate(right)
}

function formatMonthTitle(date: Date): string {
  return new Intl.DateTimeFormat('pt-BR', {
    month: 'short',
    year: '2-digit',
  }).format(date)
}

function formatPeriod(start: string | null, end: string | null): string {
  if (!start && !end) return 'Data não informada'
  const fmt = (value: string) => new Intl.DateTimeFormat('pt-BR').format(new Date(`${value}T00:00:00`))
  if (start && end) return `${fmt(start)} a ${fmt(end)}`
  return fmt(start || end || '')
}

function getStayStart(revenue: Revenue): Date {
  const base = revenue.checkin_date || revenue.date
  return new Date(`${base}T00:00:00`)
}

function getStayEndInclusive(revenue: Revenue): Date {
  if (!revenue.checkout_date) {
    return getStayStart(revenue)
  }

  const checkout = new Date(`${revenue.checkout_date}T00:00:00`)
  const checkin = getStayStart(revenue)
  const end = addDays(checkout, -1)
  return end >= checkin ? end : checkin
}

function getReservationLabel(revenue: Revenue): string {
  if (revenue.external_id) {
    return `${revenue.external_id} - ${revenue.guest_name}`
  }

  return revenue.guest_name
}

function formatMoney(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value)
}

export default function PropertyCalendarPage() {
  const { propertyId } = useParams<{ propertyId: string }>()
  const [currentMonth, setCurrentMonth] = useState(() => startOfMonth(new Date()))
  const [selectedReservation, setSelectedReservation] = useState<Revenue | null>(null)

  const calendarStart = useMemo(() => startOfCalendarGrid(currentMonth), [currentMonth])
  const calendarEnd = useMemo(() => endOfCalendarGrid(currentMonth), [currentMonth])

  const { data: property, isLoading: isPropertyLoading } = useQuery({
    queryKey: ['property', propertyId],
    queryFn: () => propertiesApi.get(propertyId!),
    enabled: Boolean(propertyId),
  })

  const { data: reservations = [], isLoading: isReservationsLoading } = useQuery({
    queryKey: ['property-calendar', propertyId, formatIsoDate(calendarStart), formatIsoDate(calendarEnd)],
    queryFn: () =>
      revenuesApi.calendar({
        property_id: propertyId!,
        start_date: formatIsoDate(calendarStart),
        end_date: formatIsoDate(calendarEnd),
      }),
    enabled: Boolean(propertyId),
  })

  const weeks = useMemo(() => {
    const values: Date[][] = []
    let cursor = new Date(calendarStart)

    while (cursor <= calendarEnd) {
      const week: Date[] = []
      for (let index = 0; index < 7; index += 1) {
        week.push(new Date(cursor))
        cursor = addDays(cursor, 1)
      }
      values.push(week)
    }

    return values
  }, [calendarStart, calendarEnd])

  const monthTitle = useMemo(() => formatMonthTitle(currentMonth), [currentMonth])
  const today = useMemo(() => new Date(), [])

  return (
    <PageContainer
      title="Calendário por Imóvel"
      subtitle={property ? property.name : 'Visualização mensal das reservas já feitas'}
      action={
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
        >
          <ArrowLeft className="h-4 w-4" />
          Voltar ao dashboard
        </Link>
      }
    >
      <Card>
        <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <CalendarDays className="h-5 w-5 text-slate-600" />
            <h2 className="text-base font-medium text-slate-900">Agenda mensal</h2>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentMonth((value) => new Date(value.getFullYear(), value.getMonth() - 1, 1))}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <div className="min-w-28 text-center text-sm font-semibold capitalize text-slate-900">
              {monthTitle}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentMonth((value) => new Date(value.getFullYear(), value.getMonth() + 1, 1))}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isPropertyLoading || isReservationsLoading ? (
            <div className="py-16 text-center text-slate-500">Carregando calendário...</div>
          ) : !propertyId ? (
            <div className="py-16 text-center text-slate-500">Imóvel não informado.</div>
          ) : (
            <div className="overflow-x-auto">
              <div className="min-w-[980px]">
                <div className="grid grid-cols-7 border-b border-slate-200 bg-slate-50">
                  {WEEKDAY_LABELS.map((label) => (
                    <div key={label} className="px-3 py-2 text-center text-xs font-medium uppercase tracking-wide text-slate-500">
                      {label}
                    </div>
                  ))}
                </div>

                {weeks.map((week, weekIndex) => {
                  const weekStart = week[0]
                  const weekEnd = week[6]
                  const weekReservations = reservations
                    .map((revenue) => {
                      const start = getStayStart(revenue)
                      const end = getStayEndInclusive(revenue)
                      if (end < weekStart || start > weekEnd) return null

                      const visibleStart = start < weekStart ? weekStart : start
                      const visibleEnd = end > weekEnd ? weekEnd : end
                      const startIndex = Math.floor((visibleStart.getTime() - weekStart.getTime()) / 86400000)
                      const endIndex = Math.floor((visibleEnd.getTime() - weekStart.getTime()) / 86400000)

                      return {
                        revenue,
                        start,
                        end,
                        startIndex,
                        endIndex,
                      }
                    })
                    .filter((item): item is NonNullable<typeof item> => item !== null)
                    .sort((left, right) => left.start.getTime() - right.start.getTime())

                  const lanes: Array<Array<typeof weekReservations[number]>> = []
                  weekReservations.forEach((reservation) => {
                    const lane = lanes.find((currentLane) => {
                      const lastItem = currentLane[currentLane.length - 1]
                      return lastItem.endIndex < reservation.startIndex
                    })
                    if (lane) {
                      lane.push(reservation)
                    } else {
                      lanes.push([reservation])
                    }
                  })

                  return (
                    <div key={`${weekIndex}-${formatIsoDate(weekStart)}`} className="border-b border-slate-200">
                      <div className="grid grid-cols-7">
                        {week.map((day) => {
                          const isCurrentMonth = day.getMonth() === currentMonth.getMonth()
                          const isToday = sameDay(day, today)
                          return (
                            <div
                              key={formatIsoDate(day)}
                              className={`min-h-[96px] border-r border-slate-100 p-2 last:border-r-0 ${
                                isCurrentMonth ? 'bg-white' : 'bg-slate-50'
                              }`}
                            >
                              <div className="flex items-center justify-between">
                                <span className={`text-xs font-medium ${isCurrentMonth ? 'text-slate-700' : 'text-slate-400'}`}>
                                  {day.getDate()}
                                </span>
                                {isToday && (
                                  <span className="rounded-full bg-primary-50 px-2 py-0.5 text-[11px] font-medium text-primary-700">
                                    hoje
                                  </span>
                                )}
                              </div>
                            </div>
                          )
                        })}
                      </div>

                      <div className="space-y-2 px-2 py-2">
                        {lanes.length > 0 ? (
                          lanes.map((lane, laneIndex) => (
                            <div
                              key={`${weekIndex}-lane-${laneIndex}`}
                              className="grid gap-2"
                              style={{ gridTemplateColumns: 'repeat(7, minmax(0, 1fr))' }}
                            >
                              {lane.map(({ revenue, startIndex, endIndex }) => (
                                <button
                                  key={revenue.id}
                                  type="button"
                                  className="flex h-8 items-center rounded-full bg-sky-600 px-3 text-left text-xs font-medium text-white shadow-sm transition-colors hover:bg-sky-700"
                                  style={{ gridColumn: `${startIndex + 1} / ${endIndex + 2}` }}
                                  title={`${getReservationLabel(revenue)} - ${formatPeriod(revenue.checkin_date, revenue.checkout_date)}`}
                                  onClick={() => setSelectedReservation(revenue)}
                                >
                                  <span className="truncate">{getReservationLabel(revenue)}</span>
                                </button>
                              ))}
                            </div>
                          ))
                        ) : (
                          <div className="py-1 text-xs text-slate-400">Sem reservas nesta semana</div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <FormModal
        open={selectedReservation !== null}
        title={selectedReservation ? getReservationLabel(selectedReservation) : 'Reserva'}
        description={selectedReservation ? 'Detalhes da reserva selecionada' : undefined}
        onClose={() => setSelectedReservation(null)}
      >
        {selectedReservation ? (
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Hóspede</p>
              <p className="mt-1 text-sm font-semibold text-slate-900">{selectedReservation.guest_name}</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Reserva</p>
              <p className="mt-1 text-sm font-semibold text-slate-900">{selectedReservation.external_id || 'Não informado'}</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Entrada</p>
              <p className="mt-1 text-sm font-semibold text-slate-900">
                {selectedReservation.checkin_date ? formatPeriod(selectedReservation.checkin_date, null) : 'Não informada'}
              </p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Saída</p>
              <p className="mt-1 text-sm font-semibold text-slate-900">
                {selectedReservation.checkout_date ? formatPeriod(selectedReservation.checkout_date, null) : 'Não informada'}
              </p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Valor líquido</p>
              <p className="mt-1 text-sm font-semibold text-slate-900">{formatMoney(selectedReservation.net_amount)}</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Valor bruto</p>
              <p className="mt-1 text-sm font-semibold text-slate-900">{formatMoney(selectedReservation.gross_amount)}</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Limpeza</p>
              <p className="mt-1 text-sm font-semibold text-slate-900">{formatMoney(selectedReservation.cleaning_fee)}</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Taxa da plataforma</p>
              <p className="mt-1 text-sm font-semibold text-slate-900">{formatMoney(selectedReservation.platform_fee)}</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Noites</p>
              <p className="mt-1 text-sm font-semibold text-slate-900">{selectedReservation.nights}</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Origem</p>
              <p className="mt-1 text-sm font-semibold text-slate-900">{selectedReservation.listing_source || 'Não informada'}</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 sm:col-span-2">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Observações</p>
              <p className="mt-1 text-sm text-slate-700">{selectedReservation.notes || 'Sem observações.'}</p>
            </div>
          </div>
        ) : null}
      </FormModal>
    </PageContainer>
  )
}
