import type { ProjectStatus } from '../types/project'

const STEPS: { label: string; statuses: ProjectStatus[] }[] = [
  { label: 'Topic', statuses: ['PROMPT_PENDING', 'PROMPT_READY'] },
  { label: 'Prompt', statuses: ['PROMPT_READY'] },
  { label: 'Video', statuses: ['VIDEO_GENERATING', 'VIDEO_READY'] },
  { label: 'Review', statuses: ['VIDEO_READY'] },
  { label: 'Metadata', statuses: ['METADATA_PENDING', 'METADATA_READY'] },
  { label: 'Done', statuses: ['COMPLETED'] },
]

const STATUS_TO_STEP: Record<ProjectStatus, number> = {
  PROMPT_PENDING: 1,
  PROMPT_READY: 2,
  VIDEO_GENERATING: 3,
  VIDEO_READY: 4,
  METADATA_PENDING: 5,
  METADATA_READY: 5,
  COMPLETED: 6,
}

export function StepIndicator({ status }: { status: ProjectStatus }) {
  const current = STATUS_TO_STEP[status] ?? 1
  return (
    <div className="flex items-center gap-2 mb-6">
      {STEPS.map((step, i) => {
        const stepNum = i + 1
        const done = stepNum < current
        const active = stepNum === current
        return (
          <div key={step.label} className="flex items-center gap-2">
            <div
              className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold
                ${done ? 'bg-indigo-600 text-white' : active ? 'bg-indigo-100 text-indigo-700 ring-2 ring-indigo-600' : 'bg-gray-100 text-gray-400'}`}
            >
              {done ? '✓' : stepNum}
            </div>
            <span className={`text-sm ${active ? 'font-medium text-indigo-700' : 'text-gray-400'}`}>
              {step.label}
            </span>
            {i < STEPS.length - 1 && <div className="h-px w-6 bg-gray-200" />}
          </div>
        )
      })}
    </div>
  )
}
