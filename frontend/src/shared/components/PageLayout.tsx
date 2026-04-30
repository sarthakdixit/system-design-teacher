import { ReactNode } from "react";
import { Link, NavLink } from "react-router-dom";
import clsx from "clsx";
import { useAuthStore } from "@/features/auth/store";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { Button } from "@/shared/components/Button";

type Props = {
  children: ReactNode;
};

const NAV_LINK_CLASSES =
  "px-3 py-2 text-sm font-medium rounded-md transition";
const NAV_LINK_INACTIVE = "text-slate-600 hover:text-slate-900 hover:bg-slate-100";
const NAV_LINK_ACTIVE = "text-brand-700 bg-brand-50";

export function PageLayout({ children }: Props) {
  const isAuthenticated = useAuthStore((s) => s.accessToken !== null);
  const user = useAuthStore((s) => s.user);
  const { logout } = useAuth();

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-3">
          <Link to="/" className="text-lg font-semibold text-slate-900">
            System Design Teacher
          </Link>

          {isAuthenticated && (
            <nav className="flex items-center gap-1" aria-label="Main">
              <NavLink
                to="/"
                end
                className={({ isActive }) =>
                  clsx(NAV_LINK_CLASSES, isActive ? NAV_LINK_ACTIVE : NAV_LINK_INACTIVE)
                }
              >
                Home
              </NavLink>
              <NavLink
                to="/practice/situation"
                className={({ isActive }) =>
                  clsx(NAV_LINK_CLASSES, isActive ? NAV_LINK_ACTIVE : NAV_LINK_INACTIVE)
                }
              >
                Situation Practice
              </NavLink>
            </nav>
          )}

          {isAuthenticated && user && (
            <div className="flex items-center gap-3">
              <span className="hidden text-sm text-slate-600 sm:inline">{user.displayName}</span>
              <Button variant="secondary" size="sm" onClick={logout}>
                Sign out
              </Button>
            </div>
          )}
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-8">{children}</main>
    </div>
  );
}
