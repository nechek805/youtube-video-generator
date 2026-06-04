import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getGenerationStatus } from '../api/projects'

export function useGenerationStatus(projectId: number, active: boolean) {
  const queryClient = useQueryClient()

  return useQuery({
    queryKey: ['generation-status', projectId],
    queryFn: async () => {
      const status = await getGenerationStatus(projectId)
      // Once the video step is no longer GENERATING, refresh the
      // canonical project query so the UI advances to the next phase.
      if (status.video_status !== 'GENERATING') {
        queryClient.invalidateQueries({ queryKey: ['project', projectId] })
      }
      return status
    },
    enabled: active,
    refetchInterval: active ? 3000 : false,
  })
}
