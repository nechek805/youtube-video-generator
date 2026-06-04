import { ErrorMessage } from '../ErrorMessage'
import { Spinner } from '../Spinner'
import { VideoPlayer } from '../VideoPlayer'
import { useApprovePrompt } from '../../hooks/useApprovePrompt'
import { useApproveVideo } from '../../hooks/useApproveVideo'
import { useGenerationStatus } from '../../hooks/useGenerationStatus'
import { useAddPart, useFinalizeParts } from '../../hooks/useAddPart'
import type { Project, VideoPart } from '../../types/project'

const MAX_PARTS = 3

/** Shows the list of already-approved clips above the current action area. */
function ApprovedPartsList({ parts }: { parts: VideoPart[] }) {
  if (parts.length === 0) return null
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-gray-700">
        Approved clips ({parts.length}/{MAX_PARTS})
      </h3>
      {parts.map((p) => (
        <div
          key={p.id}
          className="rounded-lg border border-green-200 bg-green-50 p-3 flex items-center gap-3"
        >
          <span className="shrink-0 rounded-full bg-green-600 text-white text-xs font-bold w-6 h-6 flex items-center justify-center">
            {p.part_number}
          </span>
          <div className="min-w-0">
            <video
              src={p.video_url}
              controls
              className="w-full max-h-32 rounded object-cover"
            />
            <p className="mt-1 text-xs text-gray-500 truncate">{p.prompt}</p>
          </div>
        </div>
      ))}
    </div>
  )
}

export function VideoStep({ project }: { project: Project }) {
  const approveVideo = useApproveVideo(project.id)
  const retryPrompt = useApprovePrompt(project.id)
  const addPart = useAddPart(project.id)
  const finalize = useFinalizeParts(project.id)

  useGenerationStatus(project.id, project.video_status === 'GENERATING')

  const busy =
    approveVideo.isPending ||
    retryPrompt.isPending ||
    addPart.isPending ||
    finalize.isPending

  const mutError = (
    approveVideo.error ||
    retryPrompt.error ||
    addPart.error ||
    finalize.error
  ) as Error | null

  const vs = project.video_status

  // -----------------------------------------------------------------------
  // "Choose next step" mode: current part was approved and saved.
  // Detected by: parts.length === parts_count && video_status === 'READY'
  // -----------------------------------------------------------------------
  const allPartsSaved = project.parts.length === project.parts_count
  if (vs === 'READY' && allPartsSaved) {
    const canAddMore = project.parts_count < MAX_PARTS
    return (
      <div className="space-y-5">
        <ApprovedPartsList parts={project.parts} />

        {mutError && <ErrorMessage message={mutError.message} />}

        <div className="rounded-xl border border-indigo-100 bg-indigo-50 p-4 space-y-3">
          <p className="text-sm font-medium text-indigo-900">
            {canAddMore
              ? `Part ${project.parts_count} approved! Add another clip or finish.`
              : `All ${MAX_PARTS} parts approved. Ready to generate metadata.`}
          </p>

          <div className="flex flex-wrap gap-3">
            {canAddMore && (
              <button
                onClick={() => addPart.mutate()}
                disabled={busy}
                className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
              >
                {addPart.isPending
                  ? 'Preparing…'
                  : `+ Add Part ${project.parts_count + 1}`}
              </button>
            )}
            <button
              onClick={() => finalize.mutate()}
              disabled={busy}
              className="rounded-lg bg-green-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-60"
            >
              {finalize.isPending
                ? 'Processing…'
                : '✓ Finalize & Generate Metadata'}
            </button>
          </div>
        </div>
      </div>
    )
  }

  // -----------------------------------------------------------------------
  // Standard states: PENDING / GENERATING / FAILED / READY (not yet approved)
  // -----------------------------------------------------------------------

  if (vs === 'PENDING') {
    return <Spinner label="Preparing video generation…" />
  }

  if (vs === 'GENERATING') {
    return <Spinner label={`Generating part ${project.parts_count}…`} />
  }

  if (vs === 'FAILED') {
    return (
      <div className="space-y-4">
        <ApprovedPartsList parts={project.parts} />
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

  // vs === 'READY' and current part not yet approved
  return (
    <div className="space-y-4">
      <ApprovedPartsList parts={project.parts} />

      <h2 className="font-medium text-gray-800">
        Review Part {project.parts_count}
      </h2>
      {mutError && <ErrorMessage message={mutError.message} />}
      <VideoPlayer url={project.video_url} />

      <div className="flex flex-wrap gap-3">
        <button
          onClick={() => approveVideo.mutate(true)}
          disabled={busy}
          className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
        >
          {approveVideo.isPending ? 'Saving…' : `✓ Approve Part ${project.parts_count}`}
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
