import { useMutation, useQueryClient } from '@tanstack/react-query'
import { approveMetadata } from '../api/projects'

export function useApproveMetadata(projectId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ title, description }: { title?: string | null; description?: string | null }) =>
      approveMetadata(projectId, title, description),
    onSuccess: (data) => queryClient.setQueryData(['project', projectId], data),
  })
}
