import type {
  MetadataStatus,
  Project,
  PromptStatus,
  VideoStatus,
  WorkflowStatus,
} from '../types/project'

export function workflowStatusLabel(s: WorkflowStatus): string {
  switch (s) {
    case 'PROMPT': return 'Reviewing prompt'
    case 'VIDEO': return 'Working on video'
    case 'METADATA': return 'Reviewing metadata'
    case 'COMPLETED': return 'Completed'
    case 'FAILED': return 'Failed'
  }
}

export function workflowStatusColor(s: WorkflowStatus): string {
  switch (s) {
    case 'PROMPT': return 'bg-blue-100 text-blue-700'
    case 'VIDEO': return 'bg-yellow-100 text-yellow-700'
    case 'METADATA': return 'bg-purple-100 text-purple-700'
    case 'COMPLETED': return 'bg-green-100 text-green-700'
    case 'FAILED': return 'bg-red-100 text-red-700'
  }
}

export function workflowStepNumber(workflow: WorkflowStatus): number {
  switch (workflow) {
    case 'PROMPT': return 1
    case 'VIDEO': return 2
    case 'METADATA': return 3
    case 'COMPLETED': return 4
    case 'FAILED': return 0
  }
}

type PhaseStatusProject = Pick<
  Project,
  'prompt_status' | 'video_status' | 'metadata_status'
>

export function isBusy(p: PhaseStatusProject): boolean {
  return (
    p.prompt_status === 'PENDING' ||
    p.video_status === 'GENERATING' ||
    p.metadata_status === 'PENDING'
  )
}

export function hasPhaseFailure(
  ps: PromptStatus,
  vs: VideoStatus,
  ms: MetadataStatus,
): boolean {
  return ps === 'FAILED' || vs === 'FAILED' || ms === 'FAILED'
}
