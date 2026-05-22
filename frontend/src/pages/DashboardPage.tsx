import { Link } from 'react-router-dom'
import { ErrorMessage } from '../components/ErrorMessage'
import { Layout } from '../components/Layout'
import { Spinner } from '../components/Spinner'
import { useProjects } from '../hooks/useProjects'
import {
  hasPhaseFailure,
  workflowStatusColor,
  workflowStatusLabel,
} from '../lib/projectStatus'

export function DashboardPage() {
  const { data: projects, isLoading, error } = useProjects()

  return (
    <Layout>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">My Projects</h1>
        <Link
          to="/projects/new"
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          + New Project
        </Link>
      </div>

      {isLoading && <Spinner label="Loading projects…" />}
      {error && <ErrorMessage message={(error as Error).message} />}

      {projects && projects.length === 0 && (
        <div className="rounded-xl border border-dashed border-gray-300 py-16 text-center text-gray-400">
          <p className="mb-4 text-lg">No projects yet</p>
          <Link
            to="/projects/new"
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Create your first video
          </Link>
        </div>
      )}

      {projects && projects.length > 0 && (
        <ul className="space-y-3">
          {projects.map((p) => {
            const failed = p.workflow_status === 'FAILED'
            const needsAttention =
              !failed &&
              hasPhaseFailure(p.prompt_status, p.video_status, p.metadata_status)
            return (
              <li key={p.id}>
                <Link
                  to={`/projects/${p.id}`}
                  className="flex items-center justify-between rounded-xl border border-gray-200 bg-white p-4 hover:border-indigo-300 hover:shadow-sm transition-all"
                >
                  <div>
                    <p className="font-medium text-gray-900">{p.topic}</p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      {new Date(p.updated_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {needsAttention && (
                      <span className="rounded-full px-2 py-0.5 text-xs font-medium bg-red-100 text-red-700">
                        needs attention
                      </span>
                    )}
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-medium ${workflowStatusColor(p.workflow_status)}`}
                    >
                      {workflowStatusLabel(p.workflow_status)}
                    </span>
                  </div>
                </Link>
              </li>
            )
          })}
        </ul>
      )}
    </Layout>
  )
}
