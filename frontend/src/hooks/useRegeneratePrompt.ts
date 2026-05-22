import { useMutation, useQueryClient } from '@tanstack/react-query'
import { regeneratePrompt } from '../api/projects'

export function useRegeneratePrompt(projectId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => regeneratePrompt(projectId),
    onSuccess: (data) => queryClient.setQueryData(['project', projectId], data),
    onSettled: () =>
      queryClient.invalidateQueries({ queryKey: ['project', projectId] }),
  })
}
