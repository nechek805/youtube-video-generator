import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { YOUTUBE_CONNECT_PATH } from '../../api/youtube'
import { VideoPlayer } from '../VideoPlayer'
import { usePublishToYouTube, useYouTubeAccount } from '../../hooks/useYouTubeAccount'
import type { Project } from '../../types/project'

export function CompletedStep({ project }: { project: Project }) {
  const navigate = useNavigate()
  const { data: ytAccount } = useYouTubeAccount()
  const publish = usePublishToYouTube(project.id)
  const [publishResult, setPublishResult] = useState<{ url: string; title: string } | null>(null)

  const handlePublish = async () => {
    if (!ytAccount) {
      navigate(YOUTUBE_CONNECT_PATH)
      return
    }
    try {
      const res = await publish.mutateAsync()
      setPublishResult({ url: res.youtube_url, title: res.title })
    } catch {
      // error shown via publish.error below
    }
  }

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-green-200 bg-green-50 p-4">
        <p className="font-medium text-green-800">Your video project is complete!</p>
      </div>

      <div>
        <h2 className="mb-2 font-medium text-gray-800">Final Video</h2>
        <VideoPlayer url={project.video_url} />
        {project.video_url && (
          <a
            href={project.video_url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-2 inline-block text-sm text-indigo-600 hover:underline"
          >
            Download video ↗
          </a>
        )}
      </div>

      <div className="space-y-2">
        <h2 className="font-medium text-gray-800">YouTube Title</h2>
        <p className="rounded-lg border border-gray-200 bg-white p-3 text-sm">
          {project.title}
        </p>
      </div>

      <div className="space-y-2">
        <h2 className="font-medium text-gray-800">YouTube Description</h2>
        <pre className="whitespace-pre-wrap rounded-lg border border-gray-200 bg-white p-3 text-sm font-sans">
          {project.description}
        </pre>
      </div>

      {project.tags && project.tags.length > 0 && (
        <div className="space-y-2">
          <h2 className="font-medium text-gray-800">Tags</h2>
          <div className="flex flex-wrap gap-2">
            {project.tags.map((t) => (
              <span
                key={t}
                className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700"
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-2">
        <h2 className="font-medium text-gray-800">Video Prompt Used</h2>
        <pre className="whitespace-pre-wrap rounded-lg border border-gray-200 bg-gray-50 p-3 text-xs font-mono text-gray-600">
          {project.edited_prompt ?? project.generated_prompt}
        </pre>
      </div>

      <div>
        <button
          onClick={handlePublish}
          disabled={publish.isPending}
          className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-60"
        >
          {/* YouTube icon */}
          <svg viewBox="0 0 24 24" className="w-4 h-4 fill-white" xmlns="http://www.w3.org/2000/svg">
            <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
          </svg>
          {publish.isPending ? 'Publishing…' : 'Publish to YouTube'}
        </button>

        {!ytAccount && (
          <p className="mt-2 text-xs text-gray-400">
            No YouTube account connected — clicking will take you to connect it first.
          </p>
        )}

        {publishResult && (
          <div className="mt-3 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
            ✅ Published! <a href={publishResult.url} target="_blank" rel="noopener noreferrer" className="underline font-medium">Watch on YouTube ↗</a>
          </div>
        )}

        {publish.error && (
          <p className="mt-2 text-sm text-red-600">{(publish.error as Error).message}</p>
        )}
      </div>
    </div>
  )
}
