import { apiFetch } from './client'
import type { User } from '../types/user'

export const login = (email: string, password: string) =>
  apiFetch<{ message: string }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })

export const register = (email: string, password: string) =>
  apiFetch<{ message: string }>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })

export const logout = () =>
  apiFetch<{ message: string }>('/auth/logout', { method: 'POST' })

export const confirmEmail = (token: string) =>
  apiFetch<{ message: string }>(
    `/auth/confirm-email?token=${encodeURIComponent(token)}`,
  )

export const getCurrentUser = () => apiFetch<User>('/users/get-me')
