import { CATEGORIES, DIFFICULTIES, type CategoryValue, type DifficultyValue } from "@/features/situation-practice/constants";

type Props = {
  category: CategoryValue | "";
  difficulty: DifficultyValue | "";
  onCategoryChange: (value: CategoryValue | "") => void;
  onDifficultyChange: (value: DifficultyValue | "") => void;
  disabled?: boolean;
};

const SELECT_CLASSES =
  "block w-full rounded-md border-slate-300 shadow-sm text-sm py-2 px-3 border bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 disabled:cursor-not-allowed disabled:bg-slate-100";

export function FilterBar({
  category,
  difficulty,
  onCategoryChange,
  onDifficultyChange,
  disabled,
}: Props) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <div>
        <label htmlFor="category" className="block text-sm font-medium text-slate-700">
          Category
        </label>
        <select
          id="category"
          value={category}
          onChange={(e) => onCategoryChange(e.target.value as CategoryValue | "")}
          disabled={disabled}
          className={SELECT_CLASSES}
        >
          <option value="">Any category</option>
          {CATEGORIES.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="difficulty" className="block text-sm font-medium text-slate-700">
          Difficulty
        </label>
        <select
          id="difficulty"
          value={difficulty}
          onChange={(e) => onDifficultyChange(e.target.value as DifficultyValue | "")}
          disabled={disabled}
          className={SELECT_CLASSES}
        >
          <option value="">Any difficulty</option>
          {DIFFICULTIES.map((d) => (
            <option key={d.value} value={d.value}>
              {d.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
