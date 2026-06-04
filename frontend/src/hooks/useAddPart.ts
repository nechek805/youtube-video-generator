import { useMutation, useQueryClient } from '@tanstack/react-query'
import { addPart, finalizeParts } from '../api/projects'

export function useAddPart(projectId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => addPart(projectId),
    onSuccess: (data) => {
      qc.setQueryData(['project', projectId], data)
    },
  })
}

export function useFinalizeParts(projectId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => finalizeParts(projectId),
    onSuccess: (data) => {
      qc.setQueryData(['project', projectId], data)
    },
  })
}
