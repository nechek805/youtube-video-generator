import { apiFetch } from './client'
import type { GenerationStatus, Project, ProjectListItem } from '../types/project'

export const listProjects = () =>
  apiFetch<ProjectListItem[]>('/video/projects')

export const getProject = (id: number) =>
  apiFetch<Project>(`/video/projects/${id}`)

export const createProject = (topic: string) =>
  apiFetch<Project>('/video/projects', {
    method: 'POST',
    body: JSON.stringify({ topic }),
  })

export const approvePrompt = (id: number, editedPrompt?: string | null) =>
  apiFetch<Project>(`/video/projects/${id}/approve-prompt`, {
    method: 'POST',
    body: JSON.stringify({ edited_prompt: editedPrompt ?? null }),
  })

export const regeneratePrompt = (id: number) =>
  apiFetch<Project>(`/video/projects/${id}/regenerate-prompt`, {
    method: 'POST',
  })

export const getGenerationStatus = (id: number) =>
  apiFetch<GenerationStatus>(`/video/projects/${id}/generation-status`)

export const approveVideo = (id: number, approved: boolean) =>
  apiFetch<Project>(`/video/projects/${id}/approve-video`, {
    method: 'POST',
    body: JSON.stringify({ approved }),
  })

export const approveMetadata = (
  id: number,
  editedTitle?: string | null,
  editedDescription?: string | null,
) =>
  apiFetch<Project>(`/video/projects/${id}/approve-metadata`, {
    method: 'POST',
    body: JSON.stringify({
      edited_title: editedTitle ?? null,
      edited_description: editedDescription ?? null,
    }),
  })

export const getDownload = (id: number) =>
  apiFetch<{ video_url: string }>(`/video/projects/${id}/download`)

export const publishYouTubeStub = (id: number) =>
  apiFetch<{ message: string; youtube_url: string | null }>(
    `/video/projects/${id}/publish-youtube`,
    { method: 'POST' },
  )
