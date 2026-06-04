import type { WorkflowStatus } from '../types/project'
import { workflowStepNumber } from '../lib/projectStatus'

const STEPS = [
  { num: 1, label: 'Prompt' },
  { num: 2, label: 'Video' },
  { num: 3, label: 'Metadata' },
  { num: 4, label: 'Done' },
]

export function StepIndicator({ status }: { status: WorkflowStatus }) {
  const current = workflowStepNumber(status)
  const failed = status === 'FAILED'

  return (
    <div className="flex items-center gap-2 mb-6">
      {STEPS.map((step, i) => {
        const done = step.num < current
        const active = step.num === current
        return (
          <div key={step.label} className="flex items-center gap-2">
            <div
              className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold
                ${failed ? 'bg-red-100 text-red-700' :
                  done ? 'bg-indigo-600 text-white' :
                  active ? 'bg-indigo-100 text-indigo-700 ring-2 ring-indigo-600' :
                  'bg-gray-100 text-gray-400'}`}
            >
              {done ? '✓' : step.num}
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
