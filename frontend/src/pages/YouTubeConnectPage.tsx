import { useEffect } from 'react'
import { Layout } from '../components/Layout'
import { Spinner } from '../components/Spinner'

/**
 * Frontend route: /youtube/connect
 *
 * This page immediately redirects the browser to the backend OAuth endpoint
 * which in turn redirects to Google's consent screen.
 * Users navigate here from the Settings page — they never see the backend URL.
 */
export function YouTubeConnectPage() {
  useEffect(() => {
    const base = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
    window.location.href = `${base}/youtube/connect`
  }, [])

  return (
    <Layout>
      <div className="flex flex-col items-center justify-center py-24 gap-4 text-gray-500">
        <Spinner label="Redirecting to Google…" />
        <p className="text-sm">You'll be redirected to Google to connect your YouTube account.</p>
      </div>
    </Layout>
  )
}
