import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  connectYouTube,
  disconnectYouTube,
  getYouTubeAccount,
  publishToYouTube,
} from '../api/youtube'
import { ApiError } from '../api/client'

export function useYouTubeAccount() {
  return useQuery({
    queryKey: ['youtube-account'],
    queryFn: getYouTubeAccount,
    retry: (failureCount, error) => {
      // Don't retry 404 — it just means not connected
      if (error instanceof ApiError && error.status === 404) return false
      return failureCount < 2
    },
  })
}

export function useConnectYouTube() {
  return { connect: connectYouTube }
}

export function useDisconnectYouTube() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: disconnectYouTube,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['youtube-account'] })
    },
  })
}

export function usePublishToYouTube(projectId: number) {
  return useMutation({
    mutationFn: (opts?: { title?: string; description?: string; privacy?: string }) =>
      publishToYouTube(projectId, opts),
  })
}
