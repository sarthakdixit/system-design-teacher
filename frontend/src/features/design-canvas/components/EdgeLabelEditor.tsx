import { useEffect, useRef, useState } from "react";

const MAX_LABEL_LENGTH = 80;

type Props = {
  edgeId: string;
  initialLabel: string;
  onSave: (edgeId: string, label: string) => void;
  onCancel: () => void;
};

export function EdgeLabelEditor({ edgeId, initialLabel, onSave, onCancel }: Props) {
  const [value, setValue] = useState(initialLabel);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
    inputRef.current?.select();
  }, []);

  const handleSave = () => {
    const trimmed = value.trim();
    onSave(edgeId, trimmed);
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      event.preventDefault();
      handleSave();
    } else if (event.key === "Escape") {
      event.preventDefault();
      onCancel();
    }
  };

  return (
    <div className="flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 shadow-md">
      <label htmlFor={`edge-label-${edgeId}`} className="text-xs font-medium text-slate-600">
        Edge label:
      </label>
      <input
        ref={inputRef}
        id={`edge-label-${edgeId}`}
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        maxLength={MAX_LABEL_LENGTH}
        placeholder="e.g. redirect path"
        className="w-64 rounded border border-slate-300 px-2 py-1 text-xs text-slate-800 outline-none focus:border-slate-500"
      />
      <button
        type="button"
        onClick={handleSave}
        className="rounded bg-slate-800 px-3 py-1 text-xs font-medium text-white hover:bg-slate-700"
      >
        Save
      </button>
      <button
        type="button"
        onClick={onCancel}
        className="rounded border border-slate-300 px-3 py-1 text-xs font-medium text-slate-600 hover:bg-slate-50"
      >
        Cancel
      </button>
      <span className="text-[10px] text-slate-400">
        {value.length}/{MAX_LABEL_LENGTH}
      </span>
    </div>
  );
}
