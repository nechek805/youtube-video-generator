import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { publishYouTubeStub } from '../api/projects'
import { ErrorMessage } from '../components/ErrorMessage'
import { Layout } from '../components/Layout'
import { MetadataEditor } from '../components/MetadataEditor'
import { PromptEditor } from '../components/PromptEditor'
import { Spinner } from '../components/Spinner'
import { StepIndicator } from '../components/StepIndicator'
import { VideoPlayer } from '../components/VideoPlayer'
import { useApproveMetadata } from '../hooks/useApproveMetadata'
import { useApprovePrompt } from '../hooks/useApprovePrompt'
import { useApproveVideo } from '../hooks/useApproveVideo'
import { useGenerationStatus } from '../hooks/useGenerationStatus'
import { useProject } from '../hooks/useProject'
import type { Project } from '../types/project'

function ProjectView({ project }: { project: Project }) {
  const approvePrompt = useApprovePrompt(project.id)
  const approveVideo = useApproveVideo(project.id)
  const approveMetadata = useApproveMetadata(project.id)

  const [editedPrompt, setEditedPrompt] = useState(project.generated_prompt ?? '')
  const [editedTitle, setEditedTitle] = useState(project.youtube_title ?? '')
  const [editedDesc, setEditedDesc] = useState(project.youtube_description ?? '')
  const [publishMsg, setPublishMsg] = useState<string | null>(null)

  const isGenerating = project.status === 'VIDEO_GENERATING'
  useGenerationStatus(project.id, isGenerating)

  const latestGeneration = project.generations[project.generations.length - 1] ?? null

  const mutError =
    (approvePrompt.error || approveVideo.error || approveMetadata.error) as Error | null

  return (
    <Layout>
      <div className="max-w-2xl">
        <div className="mb-4">
          <h1 className="text-xl font-semibold text-gray-900 truncate">{project.topic}</h1>
        </div>

        <StepIndicator status={project.status} />

        {mutError && <div className="mb-4"><ErrorMessage message={mutError.message} /></div>}

        {/* Step 1: PROMPT_PENDING */}
        {project.status === 'PROMPT_PENDING' && (
          <Spinner label="Generating your video prompt…" />
        )}

        {/* Step 2: PROMPT_READY */}
        {project.status === 'PROMPT_READY' && (
          <div className="space-y-4">
            <h2 className="font-medium text-gray-800">Review Your Video Prompt</h2>
            <p className="text-sm text-gray-500">
              Edit the prompt if needed, then approve to start video generation.
            </p>
            <PromptEditor
              defaultValue={project.generated_prompt ?? ''}
              onChange={setEditedPrompt}
              disabled={approvePrompt.isPending}
            />
            <div className="flex gap-3">
              <button
                onClick={() => approvePrompt.mutate(null)}
                disabled={approvePrompt.isPending}
                className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
              >
                {approvePrompt.isPending ? 'Starting…' : 'Approve & Generate Video'}
              </button>
              <button
                onClick={() => approvePrompt.mutate(editedPrompt)}
                disabled={approvePrompt.isPending}
                className="rounded-lg border border-indigo-600 px-5 py-2.5 text-sm font-medium text-indigo-600 hover:bg-indigo-50 disabled:opacity-60"
              >
                Use Edited Prompt
              </button>
            </div>
          </div>
        )}

        {/* Step 3: VIDEO_GENERATING */}
        {project.status === 'VIDEO_GENERATING' && (
          <Spinner label="Generating your video… this takes about 5 seconds." />
        )}

        {/* Step 4: VIDEO_READY */}
        {project.status === 'VIDEO_READY' && (
          <div className="space-y-4">
            <h2 className="font-medium text-gray-800">Review Your Video</h2>
            <VideoPlayer url={latestGeneration?.video_url ?? null} />
            <div className="flex gap-3">
              <button
                onClick={() => approveVideo.mutate(true)}
                disabled={approveVideo.isPending}
                className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
              >
                {approveVideo.isPending ? 'Processing…' : 'Approve Video'}
              </button>
              <button
                onClick={() => approveVideo.mutate(false)}
                disabled={approveVideo.isPending}
                className="rounded-lg border border-gray-300 px-5 py-2.5 text-sm font-medium text-gray-600 hover:bg-gray-100 disabled:opacity-60"
              >
                Reject & Edit Prompt
              </button>
            </div>
          </div>
        )}

        {/* Step 5: METADATA_PENDING */}
        {project.status === 'METADATA_PENDING' && (
          <Spinner label="Writing YouTube title and description…" />
        )}

        {/* Step 5: METADATA_READY */}
        {project.status === 'METADATA_READY' && (
          <div className="space-y-4">
            <h2 className="font-medium text-gray-800">Review YouTube Metadata</h2>
            <p className="text-sm text-gray-500">Edit the title and description if needed.</p>
            <MetadataEditor
              defaultTitle={project.youtube_title ?? ''}
              defaultDescription={project.youtube_description ?? ''}
              onChangeTitle={setEditedTitle}
              onChangeDescription={setEditedDesc}
              disabled={approveMetadata.isPending}
            />
            <div className="flex gap-3">
              <button
                onClick={() => approveMetadata.mutate({ title: null, description: null })}
                disabled={approveMetadata.isPending}
                className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
              >
                {approveMetadata.isPending ? 'Saving…' : 'Approve Metadata'}
              </button>
              <button
                onClick={() => approveMetadata.mutate({ title: editedTitle, description: editedDesc })}
                disabled={approveMetadata.isPending}
                className="rounded-lg border border-indigo-600 px-5 py-2.5 text-sm font-medium text-indigo-600 hover:bg-indigo-50 disabled:opacity-60"
              >
                Use Edited Metadata
              </button>
            </div>
          </div>
        )}

        {/* Step 6: COMPLETED */}
        {project.status === 'COMPLETED' && (
          <div className="space-y-6">
            <div className="rounded-xl border border-green-200 bg-green-50 p-4">
              <p className="font-medium text-green-800">Your video project is complete!</p>
            </div>

            <div>
              <h2 className="mb-2 font-medium text-gray-800">Final Video</h2>
              <VideoPlayer url={latestGeneration?.video_url ?? null} />
              {latestGeneration?.video_url && (
                <a
                  href={latestGeneration.video_url}
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
                {project.final_title}
              </p>
            </div>

            <div className="space-y-2">
              <h2 className="font-medium text-gray-800">YouTube Description</h2>
              <pre className="whitespace-pre-wrap rounded-lg border border-gray-200 bg-white p-3 text-sm font-sans">
                {project.final_description}
              </pre>
            </div>

            <div className="space-y-2">
              <h2 className="font-medium text-gray-800">Video Prompt Used</h2>
              <pre className="whitespace-pre-wrap rounded-lg border border-gray-200 bg-gray-50 p-3 text-xs font-mono text-gray-600">
                {project.final_prompt}
              </pre>
            </div>

            <div>
              <button
                onClick={async () => {
                  const res = await publishYouTubeStub(project.id)
                  setPublishMsg(res.message)
                }}
                className="rounded-lg border border-red-500 px-5 py-2.5 text-sm font-medium text-red-600 hover:bg-red-50"
              >
                Publish to YouTube (stub)
              </button>
              {publishMsg && (
                <p className="mt-2 text-sm text-gray-500">{publishMsg}</p>
              )}
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

  if (isLoading) return <Layout><Spinner label="Loading project…" /></Layout>
  if (error) return <Layout><ErrorMessage message={(error as Error).message} /></Layout>
  if (!project) return null

  return <ProjectView project={project} />
}
