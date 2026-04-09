export default function LoadingSpinner({ message }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4">
      <div className="relative w-12 h-12">
        <div className="absolute inset-0 rounded-full border-2 border-ufc-border" />
        <div className="absolute inset-0 rounded-full border-2 border-t-ufc-red border-r-transparent border-b-transparent border-l-transparent animate-spin" />
      </div>
      {message && (
        <p className="text-ufc-muted text-sm animate-pulse">{message}</p>
      )}
    </div>
  );
}
