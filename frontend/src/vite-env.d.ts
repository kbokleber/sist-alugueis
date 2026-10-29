/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Data/hora em que o bundle foi gerado (pt-BR, injetada no vite.config). */
  readonly VITE_APP_BUILD_AT: string
  readonly VITE_API_BASE_URL?: string
  readonly VITE_APP_NAME?: string
  readonly VITE_APP_VERSION?: string
  readonly VITE_KEYCLOAK_URL?: string
  readonly VITE_KEYCLOAK_REALM?: string
  readonly VITE_KEYCLOAK_CLIENT_ID?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
