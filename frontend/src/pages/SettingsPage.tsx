import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Layout } from '../components/Layout'
import { Spinner } from '../components/Spinner'
import { ApiError } from '../api/client'
import { YOUTUBE_CONNECT_PATH } from '../api/youtube'
import {
  useDisconnectYouTube,
  useYouTubeAccount,
} from '../hooks/useYouTubeAccount'

export function SettingsPage() {
  const { data: account, isLoading, error } = useYouTubeAccount()
  const disconnect = useDisconnectYouTube()
  const [searchParams] = useSearchParams()
  const [banner, setBanner] = useState<string | null>(null)

  // Show success banner when Google redirects back with ?youtube=connected
  useEffect(() => {
    if (searchParams.get('youtube') === 'connected') {
      setBanner('YouTube account connected successfully!')
    }
  }, [searchParams])

  const notConnected = error instanceof ApiError && error.status === 404

  return (
    <Layout>
      <h1 className="text-2xl font-semibold text-gray-900 mb-8">Settings</h1>

      {banner && (
        <div className="mb-6 rounded-lg bg-green-50 border border-green-200 px-4 py-3 text-green-800 text-sm flex items-center justify-between">
          <span>✅ {banner}</span>
          <button onClick={() => setBanner(null)} className="text-green-600 hover:text-green-800">✕</button>
        </div>
      )}

      {/* YouTube Section */}
      <div className="rounded-xl border border-gray-200 bg-white p-6">
        <div className="flex items-center gap-3 mb-4">
          {/* YouTube logo */}
          <svg viewBox="0 0 24 24" className="w-7 h-7 fill-red-600" xmlns="http://www.w3.org/2000/svg">
            <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
          </svg>
          <h2 className="text-lg font-medium text-gray-900">YouTube Account</h2>
        </div>

        {isLoading && <Spinner label="Checking connection…" />}

        {!isLoading && notConnected && (
          <div>
            <p className="text-sm text-gray-500 mb-4">
              Connect your YouTube account to publish generated videos directly from the app.
            </p>
            <Link
              to={YOUTUBE_CONNECT_PATH}
              className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 transition-colors"
            >
              Connect YouTube Account
            </Link>
          </div>
        )}

        {!isLoading && account && (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {account.channel_thumbnail && (
                <img
                  src={account.channel_thumbnail}
                  alt={account.channel_name ?? 'Channel'}
                  className="w-10 h-10 rounded-full object-cover"
                />
              )}
              <div>
                <p className="font-medium text-gray-900">
                  {account.channel_name ?? 'Unknown channel'}
                </p>
                <p className="text-xs text-gray-400">
                  Connected {new Date(account.connected_at).toLocaleDateString()}
                </p>
              </div>
            </div>
            <button
              onClick={() => disconnect.mutate()}
              disabled={disconnect.isPending}
              className="rounded-md border border-red-200 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 disabled:opacity-50 transition-colors"
            >
              {disconnect.isPending ? 'Disconnecting…' : 'Disconnect'}
            </button>
          </div>
        )}

        {!isLoading && error && !notConnected && (
          <p className="text-sm text-red-500">
            Failed to load account: {(error as Error).message}
          </p>
        )}
      </div>
    </Layout>
  )
}
