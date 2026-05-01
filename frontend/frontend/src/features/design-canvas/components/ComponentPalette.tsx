import { PALETTE, PALETTE_CATEGORIES, type PaletteItem } from "../palette";

type Props = {
  disabled?: boolean;
};

function PaletteRow({ item, disabled }: { item: PaletteItem; disabled?: boolean }) {
  const onDragStart = (event: React.DragEvent) => {
    if (disabled) {
      event.preventDefault();
      return;
    }
    event.dataTransfer.setData("application/sdt-component", item.type);
    event.dataTransfer.effectAllowed = "move";
  };

  return (
    <div
      draggable={!disabled}
      onDragStart={onDragStart}
      className={
        "group flex cursor-grab items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm transition-colors hover:border-brand-400 hover:bg-brand-50 active:cursor-grabbing " +
        (disabled ? "opacity-50 !cursor-not-allowed" : "")
      }
      role="button"
      tabIndex={0}
      aria-label={`Drag ${item.label} onto canvas`}
      title={item.description}
    >
      <span className="text-base leading-none" aria-hidden="true">
        {item.icon}
      </span>
      <span className="font-medium text-slate-700">{item.label}</span>
    </div>
  );
}

export function ComponentPalette({ disabled = false }: Props) {
  return (
    <aside className="flex h-full w-56 flex-shrink-0 flex-col gap-4 overflow-y-auto border-r border-slate-200 bg-slate-50 p-3">
      <div>
        <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Components
        </h2>
        <p className="mt-1 text-xs text-slate-500">Drag onto the canvas to build your design</p>
      </div>
      {PALETTE_CATEGORIES.map((category) => {
        const items = PALETTE.filter((p) => p.category === category.id);
        if (items.length === 0) return null;
        return (
          <div key={category.id}>
            <h3 className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              {category.label}
            </h3>
            <div className="flex flex-col gap-1.5">
              {items.map((item) => (
                <PaletteRow key={item.type} item={item} disabled={disabled} />
              ))}
            </div>
          </div>
        );
      })}
    </aside>
  );
}
