import { useState } from 'react'
import { publishYouTubeStub } from '../../api/projects'
import { VideoPlayer } from '../VideoPlayer'
import type { Project } from '../../types/project'

export function CompletedStep({ project }: { project: Project }) {
  const [publishMsg, setPublishMsg] = useState<string | null>(null)
  const [publishErr, setPublishErr] = useState<string | null>(null)
  const [publishing, setPublishing] = useState(false)

  const handlePublish = async () => {
    setPublishing(true)
    setPublishErr(null)
    try {
      const res = await publishYouTubeStub(project.id)
      setPublishMsg(res.message)
    } catch (e) {
      setPublishErr((e as Error).message)
    } finally {
      setPublishing(false)
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
          disabled={publishing}
          className="rounded-lg border border-red-500 px-5 py-2.5 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-60"
        >
          {publishing ? 'Publishing…' : 'Publish to YouTube (stub)'}
        </button>
        {publishMsg && <p className="mt-2 text-sm text-gray-500">{publishMsg}</p>}
        {publishErr && <p className="mt-2 text-sm text-red-600">{publishErr}</p>}
      </div>
    </div>
  )
}
