import { createBrowserRouter, Navigate } from "react-router";
import { RequireAuth } from "@/shared/components/RequireAuth";
import { RequireModule } from "@/shared/components/RequireModule";
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
              import("@/features/hub/components/HubHome").then((m) => ({
                Component: m.HubHome,
              })),
          },

          // ── Rotas de plataforma (sem guard de módulo) ──────────────────
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
            ],
          },
          {
            path: "plataforma",
            lazy: () =>
              import("@/features/platform/components/PlatformArea").then((m) => ({
                Component: m.PlatformArea,
              })),
            children: [
              {
                index: true,
                lazy: () =>
                  import("@/features/platform/components/GlobalDashboard").then((m) => ({
                    Component: m.GlobalDashboard,
                  })),
              },
              {
                path: "empresas",
                lazy: () =>
                  import("@/features/platform/components/CompanyList").then((m) => ({
                    Component: m.CompanyList,
                  })),
              },
            ],
          },

          // ── Rotas do módulo manutencao (guardadas por RequireModule) ───
          {
            element: <RequireModule code="manutencao" />,
            children: [
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
                path: "tickets",
                lazy: () =>
                  import("@/features/tickets/components/TicketList").then((m) => ({
                    Component: m.TicketList,
                  })),
              },
              {
                path: "tickets/new",
                lazy: () =>
                  import("@/features/tickets/components/TicketForm").then((m) => ({
                    Component: m.TicketForm,
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
                path: "setores",
                lazy: () =>
                  import("@/features/locations/components/SetoresLocaisPage").then((m) => ({
                    Component: m.SetoresLocaisPage,
                  })),
              },
              {
                path: "locais",
                lazy: () =>
                  import("@/features/locations/components/LocationList").then((m) => ({
                    Component: m.LocationList,
                  })),
              },
              {
                path: "sla",
                lazy: () =>
                  import("@/features/sla/components/SlaPolicyList").then((m) => ({
                    Component: m.SlaPolicyList,
                  })),
              },
              {
                path: "catalogos",
                element: <Navigate to="/administracao/catalogos" replace />,
              },
              {
                path: "dashboard",
                children: [
                  {
                    index: true,
                    lazy: () =>
                      import("@/shared/components/pages/DashboardRedirect").then((m) => ({
                        Component: m.DashboardRedirect,
                      })),
                  },
                  {
                    path: "technician",
                    lazy: () =>
                      import(
                        "@/features/dashboards/components/TechnicianDashboard"
                      ).then((m) => ({ Component: m.TechnicianDashboard })),
                  },
                  {
                    path: "supervisor",
                    lazy: () =>
                      import(
                        "@/features/dashboards/components/SupervisorDashboard"
                      ).then((m) => ({ Component: m.SupervisorDashboard })),
                  },
                  {
                    path: "board",
                    lazy: () =>
                      import("@/features/dashboards/components/KanbanBoard").then(
                        (m) => ({ Component: m.KanbanBoard }),
                      ),
                  },
                  {
                    path: "management",
                    lazy: () =>
                      import(
                        "@/features/dashboards/components/ManagementDashboard"
                      ).then((m) => ({ Component: m.ManagementDashboard })),
                  },
                ],
              },
              {
                path: "relatorios",
                lazy: () =>
                  import("@/features/dashboards/components/Reports").then(
                    (m) => ({ Component: m.Reports }),
                  ),
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
