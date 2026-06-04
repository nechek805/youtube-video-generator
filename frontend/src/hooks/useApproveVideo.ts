import { useMutation, useQueryClient } from '@tanstack/react-query'
import { approveVideo } from '../api/projects'

export function useApproveVideo(projectId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (approved: boolean) => approveVideo(projectId, approved),
    onSuccess: (data) => queryClient.setQueryData(['project', projectId], data),
    onSettled: () =>
      queryClient.invalidateQueries({ queryKey: ['project', projectId] }),
  })
}
