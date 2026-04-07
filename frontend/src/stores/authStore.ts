import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/types/auth.types'
import { queryClient } from '@/lib/queryClient'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  hydrated: boolean
  login: (user: User, token: string) => void
  logout: () => void
  setUser: (user: User) => void
  setHydrated: (hydrated: boolean) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      hydrated: false,
      login: (user, token) => {
        queryClient.clear()
        set({ user, token, isAuthenticated: true })
      },
      logout: () => {
        queryClient.clear()
        set({ user: null, token: null, isAuthenticated: false })
      },
      setUser: (user) => {
        queryClient.clear()
        set({ user })
      },
      setHydrated: (hydrated) => set({ hydrated }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHydrated(true)
      },
    }
  )
)
