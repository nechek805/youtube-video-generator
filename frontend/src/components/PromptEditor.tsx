import { useState } from 'react'

interface Props {
  defaultValue: string
  onChange: (value: string) => void
  disabled?: boolean
}

export function PromptEditor({ defaultValue, onChange, disabled }: Props) {
  const [value, setValue] = useState(defaultValue)

  const handleChange = (v: string) => {
    setValue(v)
    onChange(v)
  }

  return (
    <div className="space-y-1">
      <textarea
        className="w-full rounded-lg border border-gray-300 p-3 text-sm leading-relaxed focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:bg-gray-50"
        rows={10}
        value={value}
        onChange={(e) => handleChange(e.target.value)}
        disabled={disabled}
      />
      <p className="text-right text-xs text-gray-400">{value.length} chars</p>
    </div>
  )
}
