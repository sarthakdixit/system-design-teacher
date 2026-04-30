import clsx from "clsx";

type Props = {
  className?: string;
};

export function Skeleton({ className }: Props) {
  return (
    <div
      className={clsx("animate-pulse rounded bg-slate-200", className)}
      aria-hidden="true"
    />
  );
}
