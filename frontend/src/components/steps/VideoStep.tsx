import { ErrorMessage } from '../ErrorMessage'
import { Spinner } from '../Spinner'
import { VideoPlayer } from '../VideoPlayer'
import { useApprovePrompt } from '../../hooks/useApprovePrompt'
import { useApproveVideo } from '../../hooks/useApproveVideo'
import { useGenerationStatus } from '../../hooks/useGenerationStatus'
import type { Project } from '../../types/project'

export function VideoStep({ project }: { project: Project }) {
  const approveVideo = useApproveVideo(project.id)
  const retryPrompt = useApprovePrompt(project.id)

  // Poll while the backend (or async provider) is still generating
  useGenerationStatus(project.id, project.video_status === 'GENERATING')

  const busy = approveVideo.isPending || retryPrompt.isPending
  const mutError = (approveVideo.error || retryPrompt.error) as Error | null
  const vs = project.video_status

  if (vs === 'PENDING') {
    return <Spinner label="Preparing video generation…" />
  }

  if (vs === 'GENERATING') {
    return <Spinner label="Generating your video…" />
  }

  if (vs === 'FAILED') {
    return (
      <div className="space-y-4">
        <ErrorMessage message={project.error_message ?? 'Video generation failed.'} />
        <p className="text-sm text-gray-500">
          You can retry from the current prompt or go back to edit it.
        </p>
        <button
          onClick={() => retryPrompt.mutate(null)}
          disabled={busy}
          className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
        >
          {retryPrompt.isPending ? 'Retrying…' : 'Try again'}
        </button>
      </div>
    )
  }

  // vs === 'READY'
  return (
    <div className="space-y-4">
      <h2 className="font-medium text-gray-800">Review Your Video</h2>
      {mutError && <ErrorMessage message={mutError.message} />}
      <VideoPlayer url={project.video_url} />
      <div className="flex flex-wrap gap-3">
        <button
          onClick={() => approveVideo.mutate(true)}
          disabled={busy}
          className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
        >
          {approveVideo.isPending ? 'Processing…' : 'Approve Video'}
        </button>
        <button
          onClick={() => approveVideo.mutate(false)}
          disabled={busy}
          className="rounded-lg border border-gray-300 px-5 py-2.5 text-sm font-medium text-gray-600 hover:bg-gray-100 disabled:opacity-60"
        >
          Reject & Re-edit Prompt
        </button>
      </div>
    </div>
  )
}
