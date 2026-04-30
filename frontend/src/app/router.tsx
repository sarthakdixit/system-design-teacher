import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { HomePage } from "@/features/home/HomePage";
import { SituationPracticePage } from "@/features/situation-practice/SituationPracticePage";

const router = createBrowserRouter([
  {
    path: "/",
    element: <HomePage />,
  },
  {
    path: "/practice/situation",
    element: <SituationPracticePage />,
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
