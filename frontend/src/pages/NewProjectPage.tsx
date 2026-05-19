import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ErrorMessage } from '../components/ErrorMessage'
import { Layout } from '../components/Layout'
import { Spinner } from '../components/Spinner'
import { useCreateProject } from '../hooks/useCreateProject'

export function NewProjectPage() {
  const navigate = useNavigate()
  const [topic, setTopic] = useState('')
  const mutation = useCreateProject()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (topic.trim().length < 3) return
    const project = await mutation.mutateAsync(topic.trim())
    navigate(`/projects/${project.id}`)
  }

  if (mutation.isPending) {
    return (
      <Layout>
        <Spinner label="Generating your video prompt… this may take a few seconds." />
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="max-w-xl">
        <h1 className="mb-2 text-2xl font-semibold text-gray-900">New Video Project</h1>
        <p className="mb-6 text-sm text-gray-500">
          Describe what your YouTube video should be about. Be as specific or as broad as you like.
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Video Topic</label>
            <textarea
              className="w-full rounded-lg border border-gray-300 p-3 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              rows={4}
              placeholder="e.g. A cinematic tour of Tokyo at night with lofi music"
              value={topic}
              maxLength={500}
              onChange={(e) => setTopic(e.target.value)}
              required
            />
            <p className="text-right text-xs text-gray-400">{topic.length}/500</p>
          </div>
          {mutation.error && <ErrorMessage message={(mutation.error as Error).message} />}
          <button
            type="submit"
            disabled={topic.trim().length < 3}
            className="rounded-lg bg-indigo-600 px-6 py-3 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            Generate Prompt
          </button>
        </form>
      </div>
    </Layout>
  )
}
