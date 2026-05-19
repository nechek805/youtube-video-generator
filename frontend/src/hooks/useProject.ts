import { useQuery } from '@tanstack/react-query'
import { getProject } from '../api/projects'

export function useProject(id: number) {
  return useQuery({
    queryKey: ['project', id],
    queryFn: () => getProject(id),
    enabled: !!id,
  })
}
