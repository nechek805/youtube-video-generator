import { ErrorMessage } from '../ErrorMessage'
import { useRegeneratePrompt } from '../../hooks/useRegeneratePrompt'
import type { Project } from '../../types/project'

export function FailureView({ project }: { project: Project }) {
  const regeneratePrompt = useRegeneratePrompt(project.id)

  return (
    <div className="space-y-4">
      <ErrorMessage
        message={project.error_message ?? 'The workflow failed. Please try again.'}
      />
      <p className="text-sm text-gray-500">
        You can try regenerating the prompt to restart the workflow.
      </p>
      <button
        onClick={() => regeneratePrompt.mutate()}
        disabled={regeneratePrompt.isPending}
        className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
      >
        {regeneratePrompt.isPending ? 'Restarting…' : 'Restart from prompt'}
      </button>
    </div>
  )
}
