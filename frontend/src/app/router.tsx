import { lazy, Suspense } from "react";
import {
  createBrowserRouter,
  Navigate,
  RouterProvider,
} from "react-router-dom";
import { RequireAuth } from "@/shared/components/RequireAuth";
import { HomePage } from "@/features/home/HomePage";
import { Skeleton } from "@/shared/components/Skeleton";

const SituationPracticePage = lazy(() =>
  import("@/features/situation-practice/SituationPracticePage").then((m) => ({
    default: m.SituationPracticePage,
  })),
);

const DesignCanvasPage = lazy(
  () => import("@/features/design-canvas/DesignCanvasPage"),
);

const router = createBrowserRouter([
  {
    path: "/",
    element: (
      <RequireAuth>
        <HomePage />
      </RequireAuth>
    ),
  },
  {
    path: "/practice/situation",
    element: (
      <RequireAuth>
        <Suspense fallback={<Skeleton className="m-6 h-[400px]" />}>
          <SituationPracticePage />
        </Suspense>
      </RequireAuth>
    ),
  },
  {
    path: "/practice/design",
    element: (
      <RequireAuth>
        <Suspense fallback={<Skeleton className="m-6 h-[400px]" />}>
          <DesignCanvasPage />
        </Suspense>
      </RequireAuth>
    ),
  },
  {
    path: "*",
    element: <Navigate to="/" replace />,
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
