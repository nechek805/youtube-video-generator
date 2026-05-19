import { useMutation, useQueryClient } from '@tanstack/react-query'
import { approvePrompt } from '../api/projects'

export function useApprovePrompt(projectId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (editedPrompt?: string | null) => approvePrompt(projectId, editedPrompt),
    onSuccess: (data) => queryClient.setQueryData(['project', projectId], data),
  })
}
