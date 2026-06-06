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
          {
            path: "dashboard/technician",
            lazy: () =>
              import(
                "@/features/dashboards/components/TechnicianDashboard"
              ).then((m) => ({ Component: m.TechnicianDashboard })),
          },
          {
            path: "dashboard/supervisor",
            lazy: () =>
              import(
                "@/features/dashboards/components/SupervisorDashboard"
              ).then((m) => ({ Component: m.SupervisorDashboard })),
          },
          {
            path: "dashboard/board",
            lazy: () =>
              import("@/features/dashboards/components/KanbanBoard").then(
                (m) => ({ Component: m.KanbanBoard }),
              ),
          },
          {
            path: "dashboard/management",
            lazy: () =>
              import(
                "@/features/dashboards/components/ManagementDashboard"
              ).then((m) => ({ Component: m.ManagementDashboard })),
          },
          {
            path: "relatorios",
            lazy: () =>
              import("@/features/dashboards/components/Reports").then(
                (m) => ({ Component: m.Reports }),
              ),
          },
          {
            path: "administracao",
            lazy: () =>
              import("@/features/administration/components/AdminConsole").then((m) => ({
                Component: m.AdminConsole,
              })),
            children: [
              {
                path: "empresa",
                lazy: () =>
                  import(
                    "@/features/administration/components/sections/CompanySection"
                  ).then((m) => ({ Component: m.CompanySection })),
              },
              {
                path: "usuarios",
                lazy: () =>
                  import(
                    "@/features/administration/components/sections/UsersSection"
                  ).then((m) => ({ Component: m.UsersSection })),
              },
              {
                path: "equipes",
                lazy: () =>
                  import(
                    "@/features/administration/components/sections/TeamsSection"
                  ).then((m) => ({ Component: m.TeamsSection })),
              },
              {
                path: "setores",
                lazy: () =>
                  import(
                    "@/features/administration/components/sections/SetoresSection"
                  ).then((m) => ({ Component: m.SetoresSection })),
              },
              {
                path: "catalogos",
                lazy: () =>
                  import(
                    "@/features/administration/components/sections/CatalogosSection"
                  ).then((m) => ({ Component: m.CatalogosSection })),
              },
              {
                path: "sla",
                lazy: () =>
                  import(
                    "@/features/administration/components/sections/SlaSection"
                  ).then((m) => ({ Component: m.SlaSection })),
              },
              {
                path: "notificacoes",
                lazy: () =>
                  import(
                    "@/features/administration/components/sections/NotificacoesSection"
                  ).then((m) => ({ Component: m.NotificacoesSection })),
              },
              {
                path: "auditoria",
                lazy: () =>
                  import(
                    "@/features/administration/components/sections/AuditSection"
                  ).then((m) => ({ Component: m.AuditSection })),
              },
              {
                path: "tenants",
                lazy: () =>
                  import(
                    "@/features/administration/components/sections/TenantsSection"
                  ).then((m) => ({ Component: m.TenantsSection })),
              },
            ],
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
