import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createProject } from '../api/projects'

export function useCreateProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (topic: string) => createProject(topic),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['projects'] }),
  })
}
