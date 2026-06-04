import { useState } from 'react'
import { ErrorMessage } from '../ErrorMessage'
import { MetadataEditor } from '../MetadataEditor'
import { Spinner } from '../Spinner'
import { useApproveMetadata } from '../../hooks/useApproveMetadata'
import { useApproveVideo } from '../../hooks/useApproveVideo'
import type { Project } from '../../types/project'

export function MetadataStep({ project }: { project: Project }) {
  const approveMetadata = useApproveMetadata(project.id)
  const retryFromVideo = useApproveVideo(project.id)

  const [editedTitle, setEditedTitle] = useState(project.title ?? '')
  const [editedDesc, setEditedDesc] = useState(project.description ?? '')

  const busy = approveMetadata.isPending || retryFromVideo.isPending
  const mutError = (approveMetadata.error || retryFromVideo.error) as Error | null
  const ms = project.metadata_status

  if (ms === 'PENDING') {
    return <Spinner label="Writing YouTube title and description…" />
  }

  if (ms === 'FAILED') {
    return (
      <div className="space-y-4">
        <ErrorMessage message={project.error_message ?? 'Metadata generation failed.'} />
        <button
          onClick={() => retryFromVideo.mutate(true)}
          disabled={busy}
          className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
        >
          {retryFromVideo.isPending ? 'Retrying…' : 'Try again'}
        </button>
      </div>
    )
  }

  // ms === 'READY'
  return (
    <div className="space-y-4">
      <h2 className="font-medium text-gray-800">Review YouTube Metadata</h2>
      <p className="text-sm text-gray-500">Edit the title and description if needed.</p>
      {mutError && <ErrorMessage message={mutError.message} />}
      <MetadataEditor
        defaultTitle={project.title ?? ''}
        defaultDescription={project.description ?? ''}
        onChangeTitle={setEditedTitle}
        onChangeDescription={setEditedDesc}
        disabled={busy}
      />
      <div className="flex flex-wrap gap-3">
        <button
          onClick={() => approveMetadata.mutate({ title: null, description: null })}
          disabled={busy}
          className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
        >
          {approveMetadata.isPending ? 'Finalizing…' : 'Finalize'}
        </button>
        <button
          onClick={() => approveMetadata.mutate({ title: editedTitle, description: editedDesc })}
          disabled={busy}
          className="rounded-lg border border-indigo-600 px-5 py-2.5 text-sm font-medium text-indigo-600 hover:bg-indigo-50 disabled:opacity-60"
        >
          Edit & Finalize
        </button>
      </div>
    </div>
  )
}
