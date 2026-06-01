import { createBrowserRouter } from "react-router";
import { RequireAuth } from "@/shared/components/RequireAuth";
import { AppShell } from "@/shared/components/layout/AppShell";
import { LoginPage } from "@/features/auth/components/LoginPage";
import { NotFoundPage } from "@/shared/components/pages/NotFoundPage";
import { ErrorPage } from "@/shared/components/pages/ErrorPage";
import { UnauthorizedPage } from "@/shared/components/pages/UnauthorizedPage";

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/sem-permissao",
    element: <UnauthorizedPage />,
  },
  {
    path: "/",
    element: <RequireAuth />,
    errorElement: <ErrorPage />,
    children: [
      {
        element: <AppShell />,
        children: [
          {
            index: true,
            lazy: () =>
              import("@/shared/components/pages/DashboardRedirect").then((m) => ({
                Component: m.DashboardRedirect,
              })),
          },
        ],
      },
    ],
  },
  {
    path: "*",
    element: <NotFoundPage />,
  },
]);
