import { apiFetch } from './client'

export interface YouTubeAccount {
  id: number
  channel_id: string | null
  channel_name: string | null
  channel_thumbnail: string | null
  connected_at: string
}

export interface YouTubePublishResult {
  youtube_video_id: string
  youtube_url: string
  title: string
}

/** Fetch the connected YouTube account (throws ApiError 404 if not connected). */
export const getYouTubeAccount = () =>
  apiFetch<YouTubeAccount>('/youtube/account')

/** Redirect the browser to the Google OAuth consent screen (backend route). */
export const connectYouTube = () => {
  const base = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
  window.location.href = `${base}/youtube/connect`
}

/** Disconnect (delete) the stored YouTube account. */
export const disconnectYouTube = () =>
  apiFetch<void>('/youtube/disconnect', { method: 'DELETE' })

/** Publish a completed project to YouTube. */
export const publishToYouTube = (
  projectId: number,
  opts?: { title?: string; description?: string; privacy?: string },
) =>
  apiFetch<YouTubePublishResult>(
    `/youtube/projects/${projectId}/publish`,
    {
      method: 'POST',
      body: JSON.stringify(opts ?? {}),
    },
  )
