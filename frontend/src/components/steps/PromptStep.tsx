import { useState } from 'react'
import { ErrorMessage } from '../ErrorMessage'
import { PromptEditor } from '../PromptEditor'
import { Spinner } from '../Spinner'
import { useApprovePrompt } from '../../hooks/useApprovePrompt'
import { useRegeneratePrompt } from '../../hooks/useRegeneratePrompt'
import type { Project } from '../../types/project'

export function PromptStep({ project }: { project: Project }) {
  const approvePrompt = useApprovePrompt(project.id)
  const regeneratePrompt = useRegeneratePrompt(project.id)
  const [editedPrompt, setEditedPrompt] = useState(
    project.edited_prompt ?? project.generated_prompt ?? '',
  )

  const busy = approvePrompt.isPending || regeneratePrompt.isPending
  const mutError = (approvePrompt.error || regeneratePrompt.error) as Error | null
  const ps = project.prompt_status

  if (ps === 'PENDING') {
    return <Spinner label="Generating your video prompt…" />
  }

  if (ps === 'FAILED') {
    return (
      <div className="space-y-4">
        <ErrorMessage message={project.error_message ?? 'Prompt generation failed.'} />
        <button
          onClick={() => regeneratePrompt.mutate()}
          disabled={busy}
          className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
        >
          {regeneratePrompt.isPending ? 'Generating…' : 'Try again'}
        </button>
      </div>
    )
  }

  // ps === 'READY'
  return (
    <div className="space-y-4">
      <h2 className="font-medium text-gray-800">Review Your Video Prompt</h2>
      <p className="text-sm text-gray-500">
        Edit the prompt if needed, then approve to start video generation.
      </p>
      {mutError && <ErrorMessage message={mutError.message} />}
      <PromptEditor
        defaultValue={project.edited_prompt ?? project.generated_prompt ?? ''}
        onChange={setEditedPrompt}
        disabled={busy}
      />
      <div className="flex flex-wrap gap-3">
        <button
          onClick={() => approvePrompt.mutate(null)}
          disabled={busy}
          className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
        >
          {approvePrompt.isPending ? 'Starting…' : 'Approve & Continue'}
        </button>
        <button
          onClick={() => approvePrompt.mutate(editedPrompt)}
          disabled={busy}
          className="rounded-lg border border-indigo-600 px-5 py-2.5 text-sm font-medium text-indigo-600 hover:bg-indigo-50 disabled:opacity-60"
        >
          Edit & Approve
        </button>
        <button
          onClick={() => regeneratePrompt.mutate()}
          disabled={busy}
          className="rounded-lg border border-gray-300 px-5 py-2.5 text-sm font-medium text-gray-600 hover:bg-gray-100 disabled:opacity-60"
        >
          {regeneratePrompt.isPending ? 'Regenerating…' : 'Regenerate'}
        </button>
      </div>
    </div>
  )
}
