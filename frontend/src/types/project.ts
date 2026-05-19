export type ProjectStatus =
  | 'PROMPT_PENDING'
  | 'PROMPT_READY'
  | 'VIDEO_GENERATING'
  | 'VIDEO_READY'
  | 'METADATA_PENDING'
  | 'METADATA_READY'
  | 'COMPLETED'

export interface Generation {
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
  final_prompt: string | null
  youtube_title: string | null
  youtube_description: string | null
  final_title: string | null
  final_description: string | null
  status: ProjectStatus
  created_at: string
  updated_at: string
  generations: Generation[]
}

export interface ProjectListItem {
  id: number
  topic: string
  status: ProjectStatus
  created_at: string
  updated_at: string
}

export interface GenerationStatus {
  status: string
  video_url: string | null
  celery_task_id: string | null
}
