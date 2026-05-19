import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getGenerationStatus } from '../api/projects'

export function useGenerationStatus(projectId: number, active: boolean) {
  const queryClient = useQueryClient()

  return useQuery({
    queryKey: ['generation-status', projectId],
    queryFn: async () => {
      const status = await getGenerationStatus(projectId)
      if (status.status === 'VIDEO_READY') {
        queryClient.invalidateQueries({ queryKey: ['project', projectId] })
      }
      return status
    },
    enabled: active,
    refetchInterval: active ? 3000 : false,
  })
}
