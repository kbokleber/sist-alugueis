import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { X } from 'lucide-react'

interface ImageLightboxProps {
  src: string | null | undefined
  alt?: string
  open: boolean
  onClose: () => void
}

/**
 * Visualizador de imagem em tela cheia (lightbox).
 *
 * Mobile-first:
 * - abre com toque/clique na miniatura;
 * - fecha tocando fora, no X ou no botao "Voltar";
 * - bloqueia o scroll do fundo enquanto aberto;
 * - suporta pinch-zoom nativo (img com touch-action).
 */
export function ImageLightbox({ src, alt = '', open, onClose }: ImageLightboxProps) {
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    if (!open) return
    setLoaded(false)
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKeyDown)
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = previousOverflow
    }
  }, [open, onClose])

  if (!open || !src) return null

  return createPortal(
    <div
      role="dialog"
      aria-modal="true"
      aria-label={alt || 'Imagem ampliada'}
      className="fixed inset-0 z-[100] flex flex-col bg-slate-950/95 backdrop-blur-sm"
      onClick={onClose}
    >
      <header className="flex items-center justify-between gap-3 px-3 py-3 text-white sm:px-5">
        <span className="min-w-0 truncate text-sm font-medium">{alt}</span>
        <button
          type="button"
          onClick={onClose}
          aria-label="Fechar"
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white/10 transition hover:bg-white/20 focus:outline-none focus:ring-2 focus:ring-white/60"
        >
          <X className="h-5 w-5" />
        </button>
      </header>

      <div
        className="relative flex min-h-0 flex-1 items-center justify-center overflow-auto p-3 sm:p-6"
        onClick={(event) => event.stopPropagation()}
      >
        {/*
          A img precisa estar montada para disparar o onLoad, entao ela sempre
          e renderizada; enquanto nao carrega, fica invisivel sobre o spinner.
        */}
        <img
          src={src}
          alt={alt}
          onLoad={() => setLoaded(true)}
          onError={() => setLoaded(true)}
          className={
            loaded
              ? 'max-h-full max-w-full rounded-lg object-contain shadow-2xl'
              : 'hidden'
          }
        />
        {!loaded ? (
          <div className="absolute h-10 w-10 animate-spin rounded-full border-2 border-white/30 border-t-white" />
        ) : null}
      </div>

      <footer className="px-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-2 text-center sm:px-5">
        <button
          type="button"
          onClick={onClose}
          className="inline-flex h-11 items-center justify-center rounded-xl bg-white/10 px-5 text-sm font-medium text-white transition hover:bg-white/20 focus:outline-none focus:ring-2 focus:ring-white/60"
        >
          Voltar
        </button>
      </footer>
    </div>,
    document.body
  )
}
