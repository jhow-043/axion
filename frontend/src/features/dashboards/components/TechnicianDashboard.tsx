import { Link } from "react-router";
import { AlertTriangle, CheckCircle, Clock } from "lucide-react";
import { Badge } from "@/shared/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/shared/components/ui/card";
import { formatDateTime } from "@/utils/dates";
import { useTechnicianDashboard } from "../api";

const STATUS_LABELS: Record<string, string> = {
  new: "Novo",
  in_progress: "Em Atendimento",
  pending: "Pendente",
  resolved: "Solucionado",
};

export function TechnicianDashboard() {
  const { data, isLoading, error } = useTechnicianDashboard();

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

  const { assigned_tickets, sla_at_risk, sla_breached } = data;

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold">Meus Chamados</h1>

      {/* Status summary cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total atribuídos
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{assigned_tickets.total}</p>
          </CardContent>
        </Card>

        {Object.entries(assigned_tickets.by_status).map(([code, count]) => (
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

      {/* SLA at risk */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Clock className="h-4 w-4 text-yellow-500" />
            SLA em Risco ({sla_at_risk.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {sla_at_risk.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Nenhum chamado em risco.
            </p>
          ) : (
            <ul className="space-y-2">
              {sla_at_risk.map((item) => (
                <li
                  key={`${item.ticket_id}-${item.sla_type}`}
                  className="flex items-center justify-between text-sm"
                >
                  <Link
                    to={`/tickets/${item.ticket_id}`}
                    className="font-medium hover:underline"
                  >
                    {item.title}
                  </Link>
                  <div className="flex items-center gap-2">
                    <Badge variant="warning">
                      {item.sla_type === "attendance"
                        ? "Atendimento"
                        : "Resolução"}
                    </Badge>
                    <span className="text-muted-foreground">
                      {formatDateTime(item.due_at)}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      {/* SLA breached */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <AlertTriangle className="h-4 w-4 text-destructive" />
            SLA Vencido ({sla_breached.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {sla_breached.length === 0 ? (
            <p className="flex items-center gap-2 text-sm text-green-600">
              <CheckCircle className="h-4 w-4" /> Sem SLA vencido.
            </p>
          ) : (
            <ul className="space-y-2">
              {sla_breached.map((item) => (
                <li
                  key={`${item.ticket_id}-${item.sla_type}`}
                  className="flex items-center justify-between text-sm"
                >
                  <Link
                    to={`/tickets/${item.ticket_id}`}
                    className="font-medium hover:underline"
                  >
                    {item.title}
                  </Link>
                  <div className="flex items-center gap-2">
                    <Badge variant="destructive">
                      {item.sla_type === "attendance"
                        ? "Atendimento"
                        : "Resolução"}
                    </Badge>
                    <span className="text-muted-foreground">
                      Venceu: {formatDateTime(item.breached_at)}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
