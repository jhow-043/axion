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
          {
            path: "users",
            lazy: () =>
              import("@/features/users/components/UserList").then((m) => ({
                Component: m.UserList,
              })),
          },
          {
            path: "users/new",
            lazy: () =>
              import("@/features/users/components/UserForm").then((m) => ({
                Component: m.UserForm,
              })),
          },
          {
            path: "users/:id",
            lazy: () =>
              import("@/features/users/components/UserDetail").then((m) => ({
                Component: m.UserDetail,
              })),
          },
          {
            path: "teams",
            lazy: () =>
              import("@/features/teams/components/TeamList").then((m) => ({
                Component: m.TeamList,
              })),
          },
          {
            path: "teams/new",
            lazy: () =>
              import("@/features/teams/components/TeamForm").then((m) => ({
                Component: m.TeamForm,
              })),
          },
          {
            path: "teams/:id",
            lazy: () =>
              import("@/features/teams/components/TeamMembers").then((m) => ({
                Component: m.TeamMembers,
              })),
          },
          {
            path: "teams/:id/edit",
            lazy: () =>
              import("@/features/teams/components/TeamForm").then((m) => ({
                Component: m.TeamForm,
              })),
          },
          {
            path: "equipments",
            lazy: () =>
              import("@/features/equipments/components/EquipmentList").then((m) => ({
                Component: m.EquipmentList,
              })),
          },
          {
            path: "equipments/new",
            lazy: () =>
              import("@/features/equipments/components/EquipmentForm").then((m) => ({
                Component: m.EquipmentForm,
              })),
          },
          {
            path: "equipments/:id",
            lazy: () =>
              import("@/features/equipments/components/EquipmentDetail").then((m) => ({
                Component: m.EquipmentDetail,
              })),
          },
          {
            path: "equipments/:id/edit",
            lazy: () =>
              import("@/features/equipments/components/EquipmentForm").then((m) => ({
                Component: m.EquipmentForm,
              })),
          },
          {
            path: "tickets/:id",
            lazy: () =>
              import("@/features/tickets/components/TicketDetail").then((m) => ({
                Component: m.TicketDetail,
              })),
          },
          {
            path: "notifications",
            lazy: () =>
              import("@/features/notifications/components/NotificationList").then((m) => ({
                Component: m.NotificationList,
              })),
          },
          {
            path: "notifications/preferences",
            lazy: () =>
              import(
                "@/features/notifications/components/NotificationPreferences"
              ).then((m) => ({ Component: m.NotificationPreferences })),
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
