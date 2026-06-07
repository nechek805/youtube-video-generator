import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { confirmEmail } from '../api/auth'

export function ConfirmEmailPage() {
  const [params] = useSearchParams()
  const token = params.get('token') ?? ''
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!token) {
      setStatus('error')
      setMessage('No confirmation token found in the URL.')
      return
    }
    confirmEmail(token)
      .then((res) => {
        setMessage(res.message)
        setStatus('success')
      })
      .catch((err) => {
        setMessage((err as Error).message ?? 'Confirmation failed.')
        setStatus('error')
      })
  }, [token])

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm rounded-xl border border-gray-200 bg-white p-8 text-center shadow-sm">
        <h1 className="mb-4 text-2xl font-semibold text-gray-900">Email confirmation</h1>
        {status === 'loading' && (
          <p className="text-sm text-gray-500">Confirming your email…</p>
        )}
        {status === 'success' && (
          <p className="text-sm text-gray-700">
            {message}{' '}
            <Link to="/login" className="text-indigo-600 hover:underline">
              Sign in now
            </Link>
            .
          </p>
        )}
        {status === 'error' && (
          <p className="text-sm text-red-600">{message}</p>
        )}
      </div>
    </div>
  )
}
