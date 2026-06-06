import { useState } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/shared/components/ui/card";
import { Badge } from "@/shared/components/ui/badge";
import { useManagementDashboard } from "../api";
import type { ManagementFilters } from "../types";

const PRIORITY_LABELS: Record<string, string> = {
  critical: "Crítica",
  high: "Alta",
  medium: "Média",
  low: "Baixa",
};

const TYPE_LABELS: Record<string, string> = {
  industrial: "Industrial",
  predial: "Predial",
};

function ComplianceBar({ pct, label }: { pct: number; label: string }) {
  const color =
    pct >= 90 ? "bg-green-500" : pct >= 70 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium">{pct}%</span>
      </div>
      <div className="h-2 w-full rounded-full bg-muted">
        <div
          className={`h-2 rounded-full ${color} transition-all`}
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
    </div>
  );
}

export function ManagementDashboard() {
  const now = new Date();
  const defaultFrom = `${now.getFullYear()}-01-01`;
  const defaultTo = now.toISOString().slice(0, 10);

  const [filters, setFilters] = useState<ManagementFilters>({
    date_from: defaultFrom,
    date_to: defaultTo,
  });

  const { data, isLoading, error } = useManagementDashboard(filters);

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
        <h1 className="text-xl font-semibold">Dashboard Gerencial</h1>
        <div className="flex gap-2 sm:ml-auto">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted-foreground">De</label>
            <input
              type="date"
              className="rounded border bg-background px-2 py-1 text-sm"
              value={filters.date_from ?? ""}
              onChange={(e) =>
                setFilters((f) => ({ ...f, date_from: e.target.value }))
              }
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted-foreground">Até</label>
            <input
              type="date"
              className="rounded border bg-background px-2 py-1 text-sm"
              value={filters.date_to ?? ""}
              onChange={(e) =>
                setFilters((f) => ({ ...f, date_to: e.target.value }))
              }
            />
          </div>
        </div>
      </div>

      {isLoading && (
        <p className="text-muted-foreground">Carregando indicadores...</p>
      )}
      {error && (
        <p className="text-destructive">Erro ao carregar dados. Tente novamente.</p>
      )}

      {data && (
        <>
          {/* KPI Cards */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="pb-1">
                <CardTitle className="text-sm text-muted-foreground">
                  Total de Chamados
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{data.summary.total_tickets}</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {data.summary.open} abertos · {data.summary.closed} fechados
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-1">
                <CardTitle className="text-sm text-muted-foreground">
                  Tempo Médio de Resolução
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">
                  {data.summary.avg_resolution_hours.toFixed(1)}
                  <span className="ml-1 text-base font-normal text-muted-foreground">h</span>
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-1">
                <CardTitle className="text-sm text-muted-foreground">
                  SLA Rompidos
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold text-destructive">
                  {data.sla.breached_count}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-1">
                <CardTitle className="text-sm text-muted-foreground">
                  Por Tipo
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-1">
                {Object.entries(data.summary.by_type).map(([type, count]) => (
                  <div key={type} className="flex justify-between text-sm">
                    <span>{TYPE_LABELS[type] ?? type}</span>
                    <span className="font-medium">{count}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Distribution + SLA */}
          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Por Prioridade</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {Object.entries(data.summary.by_priority)
                  .sort((a, b) => b[1] - a[1])
                  .map(([p, count]) => {
                    const pct = data.summary.total_tickets
                      ? Math.round((count / data.summary.total_tickets) * 100)
                      : 0;
                    return (
                      <div key={p} className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span>{PRIORITY_LABELS[p] ?? p}</span>
                          <span className="font-medium">
                            {count} ({pct}%)
                          </span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-muted">
                          <div
                            className="h-2 rounded-full bg-primary transition-all"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Cumprimento de SLA</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <ComplianceBar
                  pct={data.sla.attendance_compliance_pct}
                  label="Atendimento"
                />
                <ComplianceBar
                  pct={data.sla.resolution_compliance_pct}
                  label="Resolução"
                />
              </CardContent>
            </Card>
          </div>

          {/* Top Equipment */}
          {data.top_problematic_equipments.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">
                  Equipamentos mais Problemáticos
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-muted-foreground">
                        <th className="py-2 text-left font-medium">Equipamento</th>
                        <th className="py-2 text-right font-medium">Chamados</th>
                        <th className="py-2 text-right font-medium">Críticos</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.top_problematic_equipments.map((eq) => (
                        <tr key={eq.equipment_id} className="border-b last:border-0">
                          <td className="py-2">{eq.name}</td>
                          <td className="py-2 text-right font-medium">
                            {eq.ticket_count}
                          </td>
                          <td className="py-2 text-right">
                            {eq.critical_count > 0 ? (
                              <Badge variant="destructive">{eq.critical_count}</Badge>
                            ) : (
                              <span className="text-muted-foreground">0</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Team Performance */}
          {data.team_performance.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Desempenho por Equipe</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-muted-foreground">
                        <th className="py-2 text-left font-medium">Equipe</th>
                        <th className="py-2 text-right font-medium">Fechados</th>
                        <th className="py-2 text-right font-medium">SLA %</th>
                        <th className="py-2 text-right font-medium">Tempo Médio</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.team_performance.map((team) => (
                        <tr key={team.team_id} className="border-b last:border-0">
                          <td className="py-2">{team.name}</td>
                          <td className="py-2 text-right">{team.total}</td>
                          <td className="py-2 text-right">
                            <Badge
                              variant={
                                team.sla_compliance_pct >= 90
                                  ? "default"
                                  : team.sla_compliance_pct >= 70
                                    ? "secondary"
                                    : "destructive"
                              }
                            >
                              {team.sla_compliance_pct}%
                            </Badge>
                          </td>
                          <td className="py-2 text-right text-muted-foreground">
                            {team.avg_resolution_hours.toFixed(1)}h
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
