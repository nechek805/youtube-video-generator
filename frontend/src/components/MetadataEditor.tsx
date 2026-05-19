import { useState } from 'react'

interface Props {
  defaultTitle: string
  defaultDescription: string
  onChangeTitle: (v: string) => void
  onChangeDescription: (v: string) => void
  disabled?: boolean
}

export function MetadataEditor({
  defaultTitle,
  defaultDescription,
  onChangeTitle,
  onChangeDescription,
  disabled,
}: Props) {
  const [title, setTitle] = useState(defaultTitle)
  const [desc, setDesc] = useState(defaultDescription)

  return (
    <div className="space-y-4">
      <div>
        <label className="mb-1 block text-sm font-medium text-gray-700">YouTube Title</label>
        <input
          type="text"
          className="w-full rounded-lg border border-gray-300 p-3 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:bg-gray-50"
          value={title}
          maxLength={100}
          onChange={(e) => { setTitle(e.target.value); onChangeTitle(e.target.value) }}
          disabled={disabled}
        />
        <p className="text-right text-xs text-gray-400">{title.length}/100</p>
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium text-gray-700">YouTube Description</label>
        <textarea
          className="w-full rounded-lg border border-gray-300 p-3 text-sm leading-relaxed focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:bg-gray-50"
          rows={8}
          value={desc}
          onChange={(e) => { setDesc(e.target.value); onChangeDescription(e.target.value) }}
          disabled={disabled}
        />
        <p className="text-right text-xs text-gray-400">{desc.length} chars</p>
      </div>
    </div>
  )
}
