import { Link, NavLink } from "react-router-dom";
import clsx from "clsx";
import { useAuthStore } from "@/features/auth/store";
import { Button } from "./Button";

type Props = {
  title?: string;
  children: React.ReactNode;
  variant?: "default" | "fullWidth";
};

export function PageLayout({ title, children, variant = "default" }: Props) {
  const user = useAuthStore((s) => s.user);
  const clearSession = useAuthStore((s) => s.clearSession);

  const isFullWidth = variant === "fullWidth";

  return (
    <div className={clsx("bg-slate-50", isFullWidth ? "h-screen overflow-hidden" : "min-h-screen")}>
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <div className="flex items-center gap-6">
            <Link to="/" className="text-base font-bold text-slate-900">
              System Design Teacher
            </Link>
            <nav className="flex items-center gap-4 text-sm">
              <NavLink
                to="/practice/situation"
                className={({ isActive }) =>
                  isActive ? "font-medium text-brand-600" : "text-slate-600 hover:text-slate-900"
                }
              >
                Situation practice
              </NavLink>
              <NavLink
                to="/practice/design"
                className={({ isActive }) =>
                  isActive ? "font-medium text-brand-600" : "text-slate-600 hover:text-slate-900"
                }
              >
                Design canvas
              </NavLink>
            </nav>
          </div>
          <div className="flex items-center gap-3">
            {user ? (
              <span className="text-sm text-slate-600">{user.displayName}</span>
            ) : null}
            <Button variant="ghost" size="sm" onClick={clearSession}>
              Sign out
            </Button>
          </div>
        </div>
      </header>
      {isFullWidth ? (
        <main className="h-[calc(100vh-3.5rem)] overflow-hidden">{children}</main>
      ) : (
        <main className="mx-auto max-w-6xl px-4 py-6">
          {title && <h1 className="mb-4 text-2xl font-bold text-slate-900">{title}</h1>}
          {children}
        </main>
      )}
    </div>
  );
}
