import { Link, useParams } from 'react-router-dom'
import { ErrorMessage } from '../components/ErrorMessage'
import { Layout } from '../components/Layout'
import { Spinner } from '../components/Spinner'
import { StepIndicator } from '../components/StepIndicator'
import { CompletedStep } from '../components/steps/CompletedStep'
import { FailureView } from '../components/steps/FailureView'
import { MetadataStep } from '../components/steps/MetadataStep'
import { PromptStep } from '../components/steps/PromptStep'
import { VideoStep } from '../components/steps/VideoStep'
import { useProject } from '../hooks/useProject'
import {
  workflowStatusColor,
  workflowStatusLabel,
  workflowStepNumber,
} from '../lib/projectStatus'
import type { Project } from '../types/project'

const TOTAL_STEPS = 4

function ProjectView({ project }: { project: Project }) {
  const ws = project.workflow_status
  const step = workflowStepNumber(ws)

  return (
    <Layout>
      <div className="max-w-2xl">
        <div className="mb-1 text-xs uppercase tracking-wide text-gray-400">
          {ws === 'FAILED'
            ? 'Workflow failed'
            : ws === 'COMPLETED'
              ? 'Step 4 of 4 — Complete'
              : `Step ${step} of ${TOTAL_STEPS}`}
        </div>

        <div className="mb-4 flex items-start justify-between gap-3">
          <h1 className="text-xl font-semibold text-gray-900 truncate">{project.topic}</h1>
          <span
            className={`shrink-0 rounded-full px-3 py-1 text-xs font-medium ${workflowStatusColor(ws)}`}
          >
            {workflowStatusLabel(ws)}
          </span>
        </div>

        <StepIndicator status={ws} />

        {ws === 'FAILED' && <FailureView project={project} />}
        {ws === 'PROMPT' && <PromptStep project={project} />}
        {ws === 'VIDEO' && <VideoStep project={project} />}
        {ws === 'METADATA' && <MetadataStep project={project} />}
        {ws === 'COMPLETED' && <CompletedStep project={project} />}
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
