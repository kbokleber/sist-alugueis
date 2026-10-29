import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/types/auth.types'
import { queryClient } from '@/lib/queryClient'
import { keycloak, logoutKeycloak } from '@/auth/keycloak'

export type AuthProvider = 'legacy' | 'keycloak' | null

interface AuthState {
  user: User | null
  token: string | null
  authProvider: AuthProvider
  isAuthenticated: boolean
  hydrated: boolean
  login: (user: User, token: string, provider?: AuthProvider) => void
  logout: () => void
  setUser: (user: User) => void
  setToken: (token: string | null) => void
  setHydrated: (hydrated: boolean) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      authProvider: null,
      isAuthenticated: false,
      hydrated: false,
      login: (user, token, provider = 'legacy') => {
        queryClient.clear()
        set({ user, token, authProvider: provider, isAuthenticated: true })
      },
      logout: () => {
        const provider = get().authProvider
        queryClient.clear()
        set({ user: null, token: null, authProvider: null, isAuthenticated: false })
        if (provider === 'keycloak' || keycloak?.authenticated) {
          logoutKeycloak()
          return
        }
      },
      setUser: (user) => {
        queryClient.clear()
        set({ user })
      },
      setToken: (token) => set({ token }),
      setHydrated: (hydrated) => set({ hydrated }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        authProvider: state.authProvider,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHydrated(true)
      },
    }
  )
)
