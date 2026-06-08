import { useState } from "react";
import { Building2, Users, Ticket, CheckCircle2, PauseCircle } from "lucide-react";
import {
  useGlobalDashboard,
  useActivateCompany,
  useSuspendCompany,
  useDeleteCompany,
} from "../api";
import { CompanyProvisionModal } from "./CompanyProvisionModal";

function StatCard({
  label,
  value,
  icon: Icon,
  accent,
}: {
  label: string;
  value: number;
  icon: React.ElementType;
  accent?: string;
}) {
  return (
    <div className="rounded-lg border bg-card p-5 flex items-start gap-4">
      <div className={`rounded-md p-2 ${accent ?? "bg-muted"}`}>
        <Icon className="h-5 w-5 text-muted-foreground" />
      </div>
      <div>
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="text-2xl font-semibold">{value}</p>
      </div>
    </div>
  );
}

export function GlobalDashboard() {
  const [page, setPage] = useState(1);
  const [showProvision, setShowProvision] = useState(false);
  const { data, isLoading, error } = useGlobalDashboard(page, 20);
  const activate = useActivateCompany();
  const suspend = useSuspendCompany();
  const deleteCompany = useDeleteCompany();

  const [confirmDelete, setConfirmDelete] = useState<{ id: string; name: string } | null>(null);

  async function handleDelete(id: string) {
    await deleteCompany.mutateAsync(id);
    setConfirmDelete(null);
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Dashboard da Plataforma</h1>
        <button
          onClick={() => setShowProvision(true)}
          className="px-3 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition"
        >
          + Nova empresa
        </button>
      </div>

      {/* KPI cards */}
      {isLoading && (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-24 rounded-lg border bg-muted animate-pulse" />
          ))}
        </div>
      )}

      {data && (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          <StatCard label="Total de empresas" value={data.total_companies} icon={Building2} />
          <StatCard
            label="Empresas ativas"
            value={data.active_companies}
            icon={CheckCircle2}
            accent="bg-green-100"
          />
          <StatCard
            label="Suspensas"
            value={data.suspended_companies}
            icon={PauseCircle}
            accent="bg-yellow-100"
          />
          <StatCard label="Total de usuários" value={data.total_users} icon={Users} />
          <StatCard label="Total de chamados" value={data.total_tickets} icon={Ticket} />
        </div>
      )}

      {/* Companies table */}
      <div className="space-y-2">
        <h2 className="text-base font-medium">Empresas</h2>

        {error && <p className="text-red-600 text-sm">Erro ao carregar empresas.</p>}

        {data && (
          <>
            <div className="overflow-x-auto rounded border text-sm">
              <table className="w-full">
                <thead className="bg-muted/50 text-left">
                  <tr>
                    <th className="px-4 py-3 font-medium">Nome</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                    <th className="px-4 py-3 font-medium text-right">Usuários</th>
                    <th className="px-4 py-3 font-medium text-right">Chamados</th>
                    <th className="px-4 py-3 font-medium">Plano</th>
                    <th className="px-4 py-3 font-medium">Criada em</th>
                    <th className="px-4 py-3 font-medium">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {data.companies.length === 0 && (
                    <tr>
                      <td colSpan={7} className="px-4 py-6 text-center text-muted-foreground">
                        Nenhuma empresa cadastrada.
                      </td>
                    </tr>
                  )}
                  {data.companies.map((company) => (
                    <tr key={company.id} className="hover:bg-muted/30">
                      <td className="px-4 py-3 font-medium">{company.name}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                            company.is_active
                              ? "bg-green-100 text-green-700"
                              : "bg-red-100 text-red-700"
                          }`}
                        >
                          {company.is_active ? "Ativa" : "Suspensa"}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">{company.user_count}</td>
                      <td className="px-4 py-3 text-right">{company.ticket_count}</td>
                      <td className="px-4 py-3 text-muted-foreground text-xs">
                        {company.plan ?? "—"}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {new Date(company.created_at).toLocaleDateString("pt-BR")}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3 text-xs">
                          {company.is_active ? (
                            <button
                              disabled={suspend.isPending}
                              onClick={() => void suspend.mutate(company.id)}
                              className="text-yellow-600 hover:underline disabled:opacity-50"
                            >
                              Suspender
                            </button>
                          ) : (
                            <button
                              disabled={activate.isPending}
                              onClick={() => void activate.mutate(company.id)}
                              className="text-green-600 hover:underline disabled:opacity-50"
                            >
                              Reativar
                            </button>
                          )}
                          <button
                            onClick={() => setConfirmDelete({ id: company.id, name: company.name })}
                            className="text-red-600 hover:underline"
                          >
                            Excluir
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {data.total_company_pages > 1 && (
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span>
                  {data.total_companies} empresas — página {page} de{" "}
                  {data.total_company_pages}
                </span>
                <div className="flex gap-2">
                  <button
                    disabled={page <= 1}
                    onClick={() => setPage((p) => p - 1)}
                    className="px-3 py-1 border rounded disabled:opacity-40"
                  >
                    Anterior
                  </button>
                  <button
                    disabled={page >= data.total_company_pages}
                    onClick={() => setPage((p) => p + 1)}
                    className="px-3 py-1 border rounded disabled:opacity-40"
                  >
                    Próxima
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Provision modal */}
      {showProvision && <CompanyProvisionModal onClose={() => setShowProvision(false)} />}

      {/* Delete confirmation */}
      {confirmDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-sm space-y-4">
            <h3 className="text-base font-semibold">Excluir empresa</h3>
            <p className="text-sm text-muted-foreground">
              Tem certeza que deseja excluir{" "}
              <span className="font-medium text-foreground">{confirmDelete.name}</span>? Esta ação
              não pode ser desfeita.
            </p>
            <div className="flex gap-2 pt-2">
              <button
                onClick={() => void handleDelete(confirmDelete.id)}
                disabled={deleteCompany.isPending}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded text-sm hover:bg-red-700 disabled:opacity-50"
              >
                {deleteCompany.isPending ? "Excluindo..." : "Excluir"}
              </button>
              <button
                onClick={() => setConfirmDelete(null)}
                className="px-4 py-2 border rounded text-sm hover:bg-muted"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
