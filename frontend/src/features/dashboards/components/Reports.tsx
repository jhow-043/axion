import { useState } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/shared/components/ui/card";
import { Badge } from "@/shared/components/ui/badge";
import { buildReportUrl } from "../api";
import type { ReportFilters } from "../types";

type ReportType = "tickets" | "sla" | "equipments" | "teams";

const REPORT_LABELS: Record<ReportType, string> = {
  tickets: "Chamados",
  sla: "SLA",
  equipments: "Equipamentos",
  teams: "Equipes",
};

const REPORT_DESCRIPTIONS: Record<ReportType, string> = {
  tickets: "Todos os chamados do período com status, prioridade, tipo e responsável",
  sla: "Conformidade de SLA por chamado (atendimento e resolução)",
  equipments: "Ranking de equipamentos por volume de chamados",
  teams: "Desempenho de equipes: chamados fechados, SLA e tempo médio",
};

export function Reports() {
  const now = new Date();
  const defaultFrom = `${now.getFullYear()}-01-01T00:00:00`;
  const defaultTo = now.toISOString().slice(0, 19);

  const [reportType, setReportType] = useState<ReportType>("tickets");
  const [dateFrom, setDateFrom] = useState(defaultFrom.slice(0, 10));
  const [dateTo, setDateTo] = useState(defaultTo.slice(0, 10));

  function handleExportCsv() {
    const filters: ReportFilters = {
      date_from: `${dateFrom}T00:00:00`,
      date_to: `${dateTo}T23:59:59`,
      format: "csv",
    };
    const url = buildReportUrl(reportType, filters);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${reportType}_${dateFrom}_${dateTo}.csv`;
    anchor.click();
  }

  function handlePreviewJson() {
    const filters: ReportFilters = {
      date_from: `${dateFrom}T00:00:00`,
      date_to: `${dateTo}T23:59:59`,
      format: "json",
    };
    const url = buildReportUrl(reportType, filters);
    window.open(url, "_blank", "noopener,noreferrer");
  }

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-xl font-semibold">Relatórios</h1>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Configurar Relatório</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Report type selector */}
          <div className="space-y-2">
            <p className="text-sm font-medium">Tipo de relatório</p>
            <div className="flex flex-wrap gap-2">
              {(Object.keys(REPORT_LABELS) as ReportType[]).map((type) => (
                <button
                  key={type}
                  onClick={() => setReportType(type)}
                  className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                    reportType === type
                      ? "bg-primary text-primary-foreground"
                      : "border bg-background hover:bg-muted"
                  }`}
                >
                  {REPORT_LABELS[type]}
                </button>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">
              {REPORT_DESCRIPTIONS[reportType]}
            </p>
          </div>

          {/* Date range */}
          <div className="flex flex-wrap gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium">De</label>
              <input
                type="date"
                className="rounded border bg-background px-3 py-1.5 text-sm"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium">Até</label>
              <input
                type="date"
                className="rounded border bg-background px-3 py-1.5 text-sm"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
              />
            </div>
          </div>

          {/* Period validation hint */}
          {dateFrom && dateTo && (() => {
            const days =
              (new Date(dateTo).getTime() - new Date(dateFrom).getTime()) /
              86_400_000;
            return days > 366 ? (
              <p className="text-sm text-destructive">
                Período máximo: 12 meses (366 dias). Período selecionado: {Math.round(days)} dias.
              </p>
            ) : null;
          })()}

          {/* Actions */}
          <div className="flex gap-2 pt-2">
            <button
              onClick={handleExportCsv}
              className="inline-flex items-center gap-2 rounded bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" x2="12" y1="15" y2="3" />
              </svg>
              Exportar CSV
            </button>
            <button
              onClick={handlePreviewJson}
              className="inline-flex items-center gap-2 rounded border bg-background px-4 py-2 text-sm font-medium hover:bg-muted transition-colors"
            >
              Visualizar JSON
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Info card */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="12" cy="12" r="10" />
                <path d="M12 16v-4" />
                <path d="M12 8h.01" />
              </svg>
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium">Como usar</p>
              <ul className="space-y-1 text-sm text-muted-foreground">
                <li>• Selecione o tipo de relatório e o período desejado.</li>
                <li>
                  • <strong>Exportar CSV</strong>: faz download do arquivo para
                  análise em planilhas.
                </li>
                <li>
                  • <strong>Visualizar JSON</strong>: abre os dados brutos em
                  nova aba para integração com outras ferramentas.
                </li>
                <li>• Período máximo permitido: 12 meses (366 dias).</li>
              </ul>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {(Object.keys(REPORT_LABELS) as ReportType[]).map((type) => (
              <Badge key={type} variant="secondary">
                {REPORT_LABELS[type]}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
