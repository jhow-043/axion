import { Link } from "react-router";
import { KanbanSquare } from "lucide-react";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/shared/components/ui/card";
import { useSupervisorDashboard } from "../api";

const PRIORITY_LABELS: Record<string, string> = {
  critical: "Crítica",
  high: "Alta",
  medium: "Média",
  low: "Baixa",
};

const PRIORITY_VARIANTS: Record<
  string,
  "destructive" | "warning" | "default" | "secondary"
> = {
  critical: "destructive",
  high: "warning",
  medium: "default",
  low: "secondary",
};

const STATUS_LABELS: Record<string, string> = {
  new: "Novo",
  in_progress: "Em Atendimento",
  pending: "Pendente",
  resolved: "Solucionado",
};

export function SupervisorDashboard() {
  const { data, isLoading, error } = useSupervisorDashboard();

  if (isLoading)
    return (
      <div className="p-6 text-muted-foreground">Carregando dashboard...</div>
    );
  if (error)
    return (
      <div className="p-6 text-destructive">
        Erro ao carregar dashboard. Tente novamente.
      </div>
    );
  if (!data) return null;

  const { summary, teams, sla_summary } = data;

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard Operacional</h1>
        <Button asChild variant="outline">
          <Link to="/dashboard/board">
            <KanbanSquare className="mr-2 h-4 w-4" />
            Abrir Kanban
          </Link>
        </Button>
      </div>

      {/* Summary cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total em aberto
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{summary.total_open}</p>
          </CardContent>
        </Card>

        {Object.entries(summary.by_status).map(([code, count]) => (
          <Card key={code}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {STATUS_LABELS[code] ?? code}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{count}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Priority breakdown */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Chamados por Prioridade</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            {Object.entries(summary.by_priority).map(([code, count]) => (
              <div key={code} className="flex items-center gap-2">
                <Badge
                  variant={PRIORITY_VARIANTS[code] ?? "default"}
                >
                  {PRIORITY_LABELS[code] ?? code}
                </Badge>
                <span className="font-semibold">{count}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* SLA compliance */}
      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Conformidade SLA — Atendimento
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {sla_summary.attendance_compliance_pct}%
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Conformidade SLA — Resolução
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {sla_summary.resolution_compliance_pct}%
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Teams table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Filas por Equipe</CardTitle>
        </CardHeader>
        <CardContent>
          {teams.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Nenhuma equipe com chamados em aberto.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="pb-2 pr-4 font-medium">Equipe</th>
                    <th className="pb-2 pr-4 font-medium text-right">
                      Em aberto
                    </th>
                    <th className="pb-2 pr-4 font-medium text-right">
                      SLA em risco
                    </th>
                    <th className="pb-2 font-medium text-right">
                      SLA vencido
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {teams.map((team) => (
                    <tr key={team.team_id} className="border-b last:border-0">
                      <td className="py-2 pr-4 font-medium">{team.team_name}</td>
                      <td className="py-2 pr-4 text-right">{team.total_open}</td>
                      <td className="py-2 pr-4 text-right">
                        {team.sla_at_risk > 0 ? (
                          <Badge variant="warning">{team.sla_at_risk}</Badge>
                        ) : (
                          <span className="text-muted-foreground">0</span>
                        )}
                      </td>
                      <td className="py-2 text-right">
                        {team.sla_breached > 0 ? (
                          <Badge variant="destructive">
                            {team.sla_breached}
                          </Badge>
                        ) : (
                          <span className="text-muted-foreground">0</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
