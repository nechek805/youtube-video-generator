import { useEffect, useState } from 'react'
import { ErrorMessage } from '../ErrorMessage'
import { Spinner } from '../Spinner'
import { useApprovePrompt } from '../../hooks/useApprovePrompt'
import { useRegeneratePrompt } from '../../hooks/useRegeneratePrompt'
import { useSavePrompt } from '../../hooks/useSavePrompt'
import type { Project } from '../../types/project'

const MAX_REGENERATIONS = 3

interface EditModalProps {
  videoPrompt: string
  regenCount: number
  onApprove: (text: string) => void
  onRegenerate: (instruction: string) => void
  onClose: () => void
  busy: boolean
  error: Error | null
}

function EditModal({
  videoPrompt,
  regenCount,
  onApprove,
  onRegenerate,
  onClose,
  busy,
  error,
}: EditModalProps) {
  const [instruction, setInstruction] = useState('')
  const [editedPrompt, setEditedPrompt] = useState(videoPrompt)
  const regenLeft = MAX_REGENERATIONS - regenCount

  // Keep the textarea in sync when a regeneration returns a new prompt
  useEffect(() => {
    setEditedPrompt(videoPrompt)
  }, [videoPrompt])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-2xl rounded-xl bg-white shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-800">Edit Prompt</h2>
          <button
            onClick={onClose}
            disabled={busy}
            className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="space-y-5 px-6 py-5">
          {error && <ErrorMessage message={error.message} />}

          {/* Top section — instructions for the LLM */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Instructions for the AI
            </label>
            <p className="text-xs text-gray-400">
              Describe how the prompt should be improved — the AI will see the current
              video prompt and apply your instructions to it.
            </p>
            <textarea
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
              disabled={busy || regenLeft <= 0}
              rows={4}
              className="w-full rounded-lg border border-indigo-300 p-3 text-sm text-gray-800 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:bg-gray-50 disabled:opacity-70 resize-y"
              placeholder="e.g. Make it faster-paced, add a dramatic opening shot…"
            />
            {regenLeft <= 0 ? (
              <p className="text-sm font-medium text-amber-600">
                You have used all {MAX_REGENERATIONS} generation attempts.
              </p>
            ) : (
              <button
                type="button"
                onClick={() => onRegenerate(instruction)}
                disabled={busy}
                className="rounded-lg border border-indigo-600 px-4 py-2 text-sm font-medium text-indigo-600 hover:bg-indigo-50 disabled:opacity-60"
              >
                {busy ? 'Generating…' : `Generate (${regenLeft} left)`}
              </button>
            )}
          </div>

          <hr className="border-gray-200" />

          {/* Bottom section — the current video prompt (editable) */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Video Prompt
            </label>
            <textarea
              value={editedPrompt}
              onChange={(e) => setEditedPrompt(e.target.value)}
              disabled={busy}
              rows={7}
              className="w-full rounded-lg border border-gray-300 p-3 text-sm text-gray-800 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:bg-gray-50 disabled:opacity-70 resize-y"
              placeholder="No prompt generated yet."
            />
            <button
              type="button"
              onClick={() => onApprove(editedPrompt)}
              disabled={busy || !editedPrompt.trim()}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
            >
              Approve
            </button>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end border-t px-6 py-4">
          <button
            type="button"
            onClick={onClose}
            disabled={busy}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-60"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}

export function PromptStep({ project }: { project: Project }) {
  const approvePrompt = useApprovePrompt(project.id)
  const regeneratePrompt = useRegeneratePrompt(project.id)
  const savePrompt = useSavePrompt(project.id)
  const [modalOpen, setModalOpen] = useState(false)
  const [regenCount, setRegenCount] = useState(0)

  const currentPromptText = project.edited_prompt ?? project.generated_prompt ?? ''

  const busy = approvePrompt.isPending || regeneratePrompt.isPending || savePrompt.isPending
  const mutError = (approvePrompt.error || regeneratePrompt.error || savePrompt.error) as Error | null
  const ps = project.prompt_status

  const handleRegenerate = (instruction: string) => {
    if (regenCount >= MAX_REGENERATIONS) return
    regeneratePrompt.mutate(instruction, {
      onSuccess: () => setRegenCount((c) => c + 1),
    })
  }

  // Save prompt only — does NOT start video generation
  const handleSavePrompt = (text: string) => {
    savePrompt.mutate(text, {
      onSuccess: () => setModalOpen(false),
    })
  }

  if (ps === 'PENDING') {
    return <Spinner label="Generating your video prompt…" />
  }

  if (ps === 'FAILED') {
    return (
      <div className="space-y-4">
        <ErrorMessage message={project.error_message ?? 'Prompt generation failed.'} />
        <button
          onClick={() => regeneratePrompt.mutate(null)}
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
    <>
      {modalOpen && (
        <EditModal
          videoPrompt={currentPromptText}
          regenCount={regenCount}
          onApprove={handleSavePrompt}
          onRegenerate={handleRegenerate}
          onClose={() => !busy && setModalOpen(false)}
          busy={busy}
          error={mutError}
        />
      )}

      <div className="space-y-4">
        <h2 className="font-medium text-gray-800">Review Your Video Prompt</h2>
        <p className="text-sm text-gray-500">
          Approve the generated prompt to start video generation, or click{' '}
          <strong>Edit &amp; Approve</strong> to refine it with AI first.
        </p>
        {mutError && !modalOpen && <ErrorMessage message={mutError.message} />}

        <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-700 whitespace-pre-wrap">
          {currentPromptText || <span className="italic text-gray-400">No prompt yet.</span>}
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => approvePrompt.mutate(null)}
            disabled={busy}
            className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
          >
            {approvePrompt.isPending ? 'Starting…' : 'Approve & Continue'}
          </button>
          <button
            onClick={() => setModalOpen(true)}
            disabled={busy}
            className="rounded-lg border border-indigo-600 px-5 py-2.5 text-sm font-medium text-indigo-600 hover:bg-indigo-50 disabled:opacity-60"
          >
            Edit &amp; Approve
          </button>
        </div>
      </div>
    </>
  )
}
