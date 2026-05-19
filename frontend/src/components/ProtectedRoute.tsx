import { Navigate } from 'react-router-dom'
import { useCurrentUser } from '../hooks/useCurrentUser'
import { Spinner } from './Spinner'

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { data: user, isLoading, isError } = useCurrentUser()

  if (isLoading) return <Spinner label="Loading…" />
  if (isError || !user) return <Navigate to="/login" replace />
  return <>{children}</>
}
