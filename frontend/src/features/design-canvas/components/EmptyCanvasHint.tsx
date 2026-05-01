export function EmptyCanvasHint() {
  return (
    <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
      <div className="rounded-lg border-2 border-dashed border-slate-300 bg-white/80 px-8 py-6 text-center shadow-sm backdrop-blur-sm">
        <p className="text-sm font-medium text-slate-700">Drag a component from the palette to start</p>
        <p className="mt-1 text-xs text-slate-500">
          Connect components by dragging from the right edge of one to the left edge of another
        </p>
      </div>
    </div>
  );
}
