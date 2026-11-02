import { useState } from 'react'
import { ImageIcon, ZoomIn } from 'lucide-react'
import { ImageLightbox } from '@/components/ui/ImageLightbox'

interface InventoryItemThumbProps {
  name: string
  imageUrl?: string | null
  size?: 'sm' | 'md' | 'lg'
  className?: string
  /** Desativa o clique para ampliar (ex.: dentro de outro lightbox). */
  disableZoom?: boolean
}

const SIZE_CLASSES: Record<NonNullable<InventoryItemThumbProps['size']>, string> = {
  sm: 'h-11 w-11',
  md: 'h-14 w-14',
  lg: 'h-16 w-16',
}

const ICON_CLASSES: Record<NonNullable<InventoryItemThumbProps['size']>, string> = {
  sm: 'h-4 w-4',
  md: 'h-6 w-6',
  lg: 'h-6 w-6',
}

/**
 * Miniatura do item de inventário.
 *
 * Sem foto (ou com foto quebrada) mostra um placeholder neutro.
 * Com foto, o clique abre a imagem em tela cheia (lightbox).
 */
export function InventoryItemThumb({
  name,
  imageUrl,
  size = 'md',
  className = '',
  disableZoom = false,
}: InventoryItemThumbProps) {
  const [hasError, setHasError] = useState(false)
  const [zoomOpen, setZoomOpen] = useState(false)

  if (!imageUrl || hasError) {
    return (
      <div
        className={`flex ${SIZE_CLASSES[size]} shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-400 ${className}`}
      >
        <ImageIcon className={ICON_CLASSES[size]} />
      </div>
    )
  }

  return (
    <>
      <button
        type="button"
        onClick={() => !disableZoom && setZoomOpen(true)}
        disabled={disableZoom}
        aria-label={disableZoom ? name : `Ampliar foto de ${name}`}
        className={`group relative ${SIZE_CLASSES[size]} shrink-0 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm transition focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-1 ${
          disableZoom ? 'cursor-default' : 'cursor-zoom-in active:scale-95'
        }`}
      >
        <img
          src={imageUrl}
          alt={name}
          loading="lazy"
          className="h-full w-full object-cover"
          onError={() => setHasError(true)}
        />
        {!disableZoom ? (
          <span
            aria-hidden
            className="absolute inset-0 flex items-center justify-center bg-slate-900/0 text-white opacity-0 transition group-hover:bg-slate-900/40 group-hover:opacity-100"
          >
            <ZoomIn className="h-5 w-5" />
          </span>
        ) : null}
      </button>

      {!disableZoom ? (
        <ImageLightbox
          src={imageUrl}
          alt={name}
          open={zoomOpen}
          onClose={() => setZoomOpen(false)}
        />
      ) : null}
    </>
  )
}
