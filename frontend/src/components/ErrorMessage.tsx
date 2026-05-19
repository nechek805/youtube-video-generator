export function ErrorMessage({ message }: { message: string }) {
  return (
    <div className="rounded-md bg-red-50 border border-red-200 p-4 text-sm text-red-700">
      {message}
    </div>
  )
}
