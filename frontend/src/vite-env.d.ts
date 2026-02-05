/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_MSAL_CLIENT_ID: string
  readonly VITE_MSAL_AUTHORITY: string
  readonly VITE_MSAL_REDIRECT_URI: string
  readonly VITE_MSAL_POST_LOGOUT_REDIRECT_URI: string
  readonly VITE_API_BASE_URI: string
  readonly VITE_API_SCOPE: string
  readonly MODE: string
  readonly BASE_URL: string
  readonly PROD: boolean
  readonly DEV: boolean
  readonly SSR: boolean
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}