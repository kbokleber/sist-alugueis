import type { AppProfile, User } from '@/types/auth.types'

export function normalizeAppProfile(profile?: string | null): AppProfile {
  return profile === 'checklist' ? 'checklist' : 'full'
}

export function isChecklistProfile(user?: User | null): boolean {
  return normalizeAppProfile(user?.app_profile) === 'checklist'
}

export function homePathForUser(user?: User | null): string {
  return isChecklistProfile(user) ? '/conferencias' : '/dashboard'
}
