export type WorkflowStatus =
  | 'PROMPT'
  | 'VIDEO'
  | 'METADATA'
  | 'COMPLETED'
  | 'FAILED'

export type PromptStatus = 'PENDING' | 'READY' | 'FAILED'

export type VideoStatus = 'PENDING' | 'GENERATING' | 'READY' | 'FAILED'

export type MetadataStatus = 'PENDING' | 'READY' | 'FAILED'

export interface GenerationStep {
  id: number
  prompt_used: string
  video_url: string | null
  celery_task_id: string | null
  is_approved: boolean
  created_at: string
}

export interface Project {
  id: number
  topic: string

  generated_prompt: string | null
  edited_prompt: string | null
  prompt_status: PromptStatus

  video_url: string | null
  video_status: VideoStatus

  title: string | null
  description: string | null
  metadata_status: MetadataStatus

  workflow_status: WorkflowStatus
  error_message: string | null

  created_at: string
  updated_at: string

  generation_steps: GenerationStep[]
}

export interface ProjectListItem {
  id: number
  topic: string
  workflow_status: WorkflowStatus
  prompt_status: PromptStatus
  video_status: VideoStatus
  metadata_status: MetadataStatus
  created_at: string
  updated_at: string
}

export interface GenerationStatus {
  workflow_status: WorkflowStatus
  video_status: VideoStatus
  video_url: string | null
  celery_task_id: string | null
  error_message: string | null
}
