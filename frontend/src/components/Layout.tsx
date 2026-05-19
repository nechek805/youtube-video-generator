import { useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { logout } from '../api/auth'
import { useCurrentUser } from '../hooks/useCurrentUser'

export function Layout({ children }: { children: React.ReactNode }) {
  const { data: user } = useCurrentUser()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const handleLogout = async () => {
    await logout()
    queryClient.clear()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="border-b border-gray-200 bg-white px-6 py-3 flex items-center justify-between">
        <Link to="/" className="text-lg font-semibold text-indigo-600">
          VideoGen
        </Link>
        {user && (
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-500">{user.email}</span>
            <button
              onClick={handleLogout}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100"
            >
              Logout
            </button>
          </div>
        )}
      </nav>
      <main className="mx-auto max-w-3xl px-4 py-8">{children}</main>
    </div>
  )
}
