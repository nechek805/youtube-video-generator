interface Props {
  url: string | null
}

export function VideoPlayer({ url }: Props) {
  if (!url) {
    return (
      <div className="flex h-48 items-center justify-center rounded-lg bg-gray-100 text-gray-400 text-sm">
        Video is processing…
      </div>
    )
  }
  return (
    <video
      className="w-full rounded-lg border border-gray-200 bg-black"
      controls
      src={url}
    >
      Your browser does not support the video tag.
    </video>
  )
}
