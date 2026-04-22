/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Data/hora em que o bundle foi gerado (pt-BR, injetada no vite.config). */
  readonly VITE_APP_BUILD_AT: string
}
