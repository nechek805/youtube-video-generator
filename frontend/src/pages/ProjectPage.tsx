import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { publishYouTubeStub } from '../api/projects'
import { ErrorMessage } from '../components/ErrorMessage'
import { Layout } from '../components/Layout'
import { MetadataEditor } from '../components/MetadataEditor'
import { Spinner } from '../components/Spinner'
import { StepIndicator } from '../components/StepIndicator'
import { VideoPlayer } from '../components/VideoPlayer'
import { PromptStep } from '../components/steps/PromptStep'
import { VideoStep } from '../components/steps/VideoStep'
import { useApproveMetadata } from '../hooks/useApproveMetadata'
import { useApproveVideo } from '../hooks/useApproveVideo'
import { useProject } from '../hooks/useProject'
import { useRegeneratePrompt } from '../hooks/useRegeneratePrompt'
import {
  workflowStatusColor,
  workflowStatusLabel,
} from '../lib/projectStatus'
import type { Project } from '../types/project'

function ProjectView({ project }: { project: Project }) {
  const approveVideo = useApproveVideo(project.id)
  const approveMetadata = useApproveMetadata(project.id)
  const regeneratePrompt = useRegeneratePrompt(project.id)

  const [editedTitle, setEditedTitle] = useState(project.title ?? '')
  const [editedDesc, setEditedDesc] = useState(project.description ?? '')
  const [publishMsg, setPublishMsg] = useState<string | null>(null)

  const ws = project.workflow_status
  const ms = project.metadata_status

  const metadataBusy = approveVideo.isPending || approveMetadata.isPending
  const metadataErr = (approveVideo.error || approveMetadata.error) as Error | null

  const handlePublish = async () => {
    const res = await publishYouTubeStub(project.id)
    setPublishMsg(res.message)
  }

  return (
    <Layout>
      <div className="max-w-2xl">
        <div className="mb-4 flex items-start justify-between gap-3">
          <h1 className="text-xl font-semibold text-gray-900 truncate">{project.topic}</h1>
          <span
            className={`shrink-0 rounded-full px-3 py-1 text-xs font-medium ${workflowStatusColor(ws)}`}
          >
            {workflowStatusLabel(ws)}
          </span>
        </div>

        <StepIndicator status={ws} />

        {/* Workflow-level failure */}
        {ws === 'FAILED' && (
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
        )}

        {ws === 'PROMPT' && <PromptStep project={project} />}
        {ws === 'VIDEO' && <VideoStep project={project} />}

        {/* Phase 3: METADATA */}
        {ws === 'METADATA' && ms === 'PENDING' && (
          <Spinner label="Writing YouTube title and description…" />
        )}

        {ws === 'METADATA' && ms === 'FAILED' && (
          <div className="space-y-4">
            <ErrorMessage
              message={project.error_message ?? 'Metadata generation failed.'}
            />
            <button
              onClick={() => approveVideo.mutate(true)}
              disabled={metadataBusy}
              className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
            >
              Try again
            </button>
          </div>
        )}

        {ws === 'METADATA' && ms === 'READY' && (
          <div className="space-y-4">
            <h2 className="font-medium text-gray-800">Review YouTube Metadata</h2>
            <p className="text-sm text-gray-500">Edit the title and description if needed.</p>
            {metadataErr && <ErrorMessage message={metadataErr.message} />}
            <MetadataEditor
              defaultTitle={project.title ?? ''}
              defaultDescription={project.description ?? ''}
              onChangeTitle={setEditedTitle}
              onChangeDescription={setEditedDesc}
              disabled={metadataBusy}
            />
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => approveMetadata.mutate({ title: null, description: null })}
                disabled={metadataBusy}
                className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
              >
                {approveMetadata.isPending ? 'Finalizing…' : 'Finalize'}
              </button>
              <button
                onClick={() =>
                  approveMetadata.mutate({ title: editedTitle, description: editedDesc })
                }
                disabled={metadataBusy}
                className="rounded-lg border border-indigo-600 px-5 py-2.5 text-sm font-medium text-indigo-600 hover:bg-indigo-50 disabled:opacity-60"
              >
                Edit &amp; Finalize
              </button>
            </div>
          </div>
        )}

        {/* Final */}
        {ws === 'COMPLETED' && (
          <div className="space-y-6">
            <div className="rounded-xl border border-green-200 bg-green-50 p-4">
              <p className="font-medium text-green-800">Your video project is complete!</p>
            </div>

            <div>
              <h2 className="mb-2 font-medium text-gray-800">Final Video</h2>
              <VideoPlayer url={project.video_url} />
              {project.video_url && (
                <a
                  href={project.video_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-2 inline-block text-sm text-indigo-600 hover:underline"
                >
                  Download video ↗
                </a>
              )}
            </div>

            <div className="space-y-2">
              <h2 className="font-medium text-gray-800">YouTube Title</h2>
              <p className="rounded-lg border border-gray-200 bg-white p-3 text-sm">
                {project.title}
              </p>
            </div>

            <div className="space-y-2">
              <h2 className="font-medium text-gray-800">YouTube Description</h2>
              <pre className="whitespace-pre-wrap rounded-lg border border-gray-200 bg-white p-3 text-sm font-sans">
                {project.description}
              </pre>
            </div>

            <div className="space-y-2">
              <h2 className="font-medium text-gray-800">Video Prompt Used</h2>
              <pre className="whitespace-pre-wrap rounded-lg border border-gray-200 bg-gray-50 p-3 text-xs font-mono text-gray-600">
                {project.edited_prompt ?? project.generated_prompt}
              </pre>
            </div>

            <div>
              <button
                onClick={handlePublish}
                className="rounded-lg border border-red-500 px-5 py-2.5 text-sm font-medium text-red-600 hover:bg-red-50"
              >
                Publish to YouTube (stub)
              </button>
              {publishMsg && <p className="mt-2 text-sm text-gray-500">{publishMsg}</p>}
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}

export function ProjectPage() {
  const { id } = useParams<{ id: string }>()
  const projectId = Number(id)
  const { data: project, isLoading, error } = useProject(projectId)

  if (isLoading)
    return (
      <Layout>
        <Spinner label="Loading project…" />
      </Layout>
    )
  if (error)
    return (
      <Layout>
        <div className="space-y-4">
          <ErrorMessage message={(error as Error).message} />
          <Link
            to="/"
            className="inline-block text-sm text-indigo-600 hover:underline"
          >
            ← Back to projects
          </Link>
        </div>
      </Layout>
    )
  if (!project) return null

  return <ProjectView project={project} />
}
