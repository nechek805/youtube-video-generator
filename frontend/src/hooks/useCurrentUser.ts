import { useQuery } from '@tanstack/react-query'
import { getCurrentUser } from '../api/auth'

export function useCurrentUser() {
  return useQuery({
    queryKey: ['me'],
    queryFn: getCurrentUser,
    retry: false,
    staleTime: 5 * 60 * 1000,
  })
}
