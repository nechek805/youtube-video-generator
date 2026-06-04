import { useMutation, useQueryClient } from '@tanstack/react-query'
import { savePrompt } from '../api/projects'

export function useSavePrompt(projectId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (editedPrompt: string) => savePrompt(projectId, editedPrompt),
    onSuccess: (data) => queryClient.setQueryData(['project', projectId], data),
    onSettled: () =>
      queryClient.invalidateQueries({ queryKey: ['project', projectId] }),
  })
}
