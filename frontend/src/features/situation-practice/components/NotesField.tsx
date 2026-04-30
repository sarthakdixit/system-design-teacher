import { ChangeEvent } from "react";
import clsx from "clsx";

type Props = {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
};

const MAX_LENGTH = 5000;

export function NotesField({ value, onChange, disabled }: Props) {
  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    const next = e.target.value.slice(0, MAX_LENGTH);
    onChange(next);
  };

  const remaining = MAX_LENGTH - value.length;

  return (
    <div>
      <label htmlFor="user-notes" className="block text-sm font-medium text-slate-700">
        Your notes <span className="text-slate-500">(optional)</span>
      </label>
      <textarea
        id="user-notes"
        rows={6}
        value={value}
        onChange={handleChange}
        disabled={disabled}
        placeholder="Jot down your approach before revealing the reference answer…"
        maxLength={MAX_LENGTH}
        className={clsx(
          "mt-1 block w-full rounded-md border border-slate-300 bg-white p-3 text-sm shadow-sm",
          "focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500",
          "disabled:cursor-not-allowed disabled:bg-slate-100",
        )}
      />
      <p className="mt-1 text-right text-xs text-slate-500">{remaining} characters remaining</p>
    </div>
  );
}
