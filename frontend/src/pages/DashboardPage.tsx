import { Link } from 'react-router-dom'
import { ErrorMessage } from '../components/ErrorMessage'
import { Layout } from '../components/Layout'
import { Spinner } from '../components/Spinner'
import { useProjects } from '../hooks/useProjects'
import type { ProjectStatus } from '../types/project'

const STATUS_LABEL: Record<ProjectStatus, string> = {
  PROMPT_PENDING: 'Generating prompt…',
  PROMPT_READY: 'Awaiting prompt approval',
  VIDEO_GENERATING: 'Generating video…',
  VIDEO_READY: 'Awaiting video approval',
  METADATA_PENDING: 'Generating metadata…',
  METADATA_READY: 'Awaiting metadata approval',
  COMPLETED: 'Completed',
}

const STATUS_COLOR: Record<ProjectStatus, string> = {
  PROMPT_PENDING: 'bg-yellow-100 text-yellow-700',
  PROMPT_READY: 'bg-blue-100 text-blue-700',
  VIDEO_GENERATING: 'bg-yellow-100 text-yellow-700',
  VIDEO_READY: 'bg-blue-100 text-blue-700',
  METADATA_PENDING: 'bg-yellow-100 text-yellow-700',
  METADATA_READY: 'bg-blue-100 text-blue-700',
  COMPLETED: 'bg-green-100 text-green-700',
}

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
          {projects.map((p) => (
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
                <span
                  className={`rounded-full px-3 py-1 text-xs font-medium ${STATUS_COLOR[p.status]}`}
                >
                  {STATUS_LABEL[p.status]}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Layout>
  )
}
