export default function LoadingIndicator() {
  return (
    <div className="flex items-start gap-3 animate-fade-in">
      <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-cortex-500 to-cortex-700 flex items-center justify-center flex-shrink-0 mt-0.5">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" className="text-white">
          <path
            d="M12 3C7.03 3 3 7.03 3 12s4.03 9 9 9 9-4.03 9-9-4.03-9-9-9zm0 3.5a5.5 5.5 0 110 11 5.5 5.5 0 010-11z"
            fill="currentColor"
            fillOpacity="0.9"
          />
        </svg>
      </div>
      <div className="bg-surface-100 border border-border rounded-2xl rounded-tl-md px-4 py-3 max-w-[75%]">
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 bg-cortex-400 rounded-full animate-typing" style={{ animationDelay: '0ms' }} />
          <span className="w-1.5 h-1.5 bg-cortex-400 rounded-full animate-typing" style={{ animationDelay: '200ms' }} />
          <span className="w-1.5 h-1.5 bg-cortex-400 rounded-full animate-typing" style={{ animationDelay: '400ms' }} />
        </div>
      </div>
    </div>
  );
}
