import { useState } from "react";
import { Plus } from "lucide-react";
import {
  usePlatformTenants,
  useActivateCompany,
  useSuspendCompany,
  useDeleteCompany,
  useUpdateCompany,
} from "../api";
import { CompanyProvisionModal } from "./CompanyProvisionModal";
import { CompanyModulesModal } from "./CompanyModulesModal";

export function CompanyList() {
  const [page, setPage] = useState(1);
  const [showProvision, setShowProvision] = useState(false);
  const [modulesFor, setModulesFor] = useState<{ id: string; name: string } | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<{ id: string; name: string } | null>(null);
  const [editing, setEditing] = useState<{ id: string; name: string } | null>(null);

  const { data, isLoading, error } = usePlatformTenants(page, 20);
  const activate = useActivateCompany();
  const suspend = useSuspendCompany();
  const deleteCompany = useDeleteCompany();

  const totalPages = data ? Math.ceil(data.total / 20) : 1;

  async function handleDelete(id: string) {
    await deleteCompany.mutateAsync(id);
    setConfirmDelete(null);
  }

  function EditRow({ id, initialName }: { id: string; initialName: string }) {
    const [name, setName] = useState(initialName);
    const update = useUpdateCompany(id);

    async function save() {
      if (name.trim() && name !== initialName) {
        await update.mutateAsync({ name: name.trim() });
      }
      setEditing(null);
    }

    return (
      <div className="flex items-center gap-2">
        <input
          autoFocus
          type="text"
          className="border rounded px-2 py-1 text-sm w-48"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") void save();
            if (e.key === "Escape") setEditing(null);
          }}
        />
        <button
          onClick={() => void save()}
          disabled={update.isPending}
          className="text-xs text-blue-600 hover:underline disabled:opacity-50"
        >
          Salvar
        </button>
        <button onClick={() => setEditing(null)} className="text-xs text-muted-foreground hover:underline">
          Cancelar
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Gestão de Empresas</h2>
        <button
          onClick={() => setShowProvision(true)}
          className="flex items-center gap-1.5 px-3 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 transition"
        >
          <Plus className="h-4 w-4" />
          Nova empresa
        </button>
      </div>

      {isLoading && (
        <div className="space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-12 bg-muted rounded animate-pulse" />
          ))}
        </div>
      )}

      {error && <p className="text-red-600 text-sm">Erro ao carregar empresas.</p>}

      {data && (
        <>
          <div className="overflow-x-auto rounded border text-sm">
            <table className="w-full">
              <thead className="bg-muted/50 text-left">
                <tr>
                  <th className="px-4 py-3 font-medium">Nome</th>
                  <th className="px-4 py-3 font-medium">Slug</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Criada em</th>
                  <th className="px-4 py-3 font-medium">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data.items.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-6 text-center text-muted-foreground">
                      Nenhuma empresa encontrada.
                    </td>
                  </tr>
                )}
                {data.items.map((tenant) => (
                  <tr key={tenant.id} className="hover:bg-muted/30">
                    <td className="px-4 py-3 font-medium">
                      {editing?.id === tenant.id ? (
                        <EditRow id={tenant.id} initialName={tenant.name} />
                      ) : (
                        <button
                          className="hover:underline text-left"
                          onClick={() => setEditing({ id: tenant.id, name: tenant.name })}
                        >
                          {tenant.name}
                        </button>
                      )}
                    </td>
                    <td className="px-4 py-3 font-mono text-muted-foreground">{tenant.slug}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                          tenant.is_active
                            ? "bg-green-100 text-green-700"
                            : "bg-red-100 text-red-700"
                        }`}
                      >
                        {tenant.is_active ? "Ativa" : "Suspensa"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {new Date(tenant.created_at).toLocaleDateString("pt-BR")}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3 text-xs">
                        <button
                          onClick={() => setModulesFor({ id: tenant.id, name: tenant.name })}
                          className="text-blue-600 hover:underline"
                        >
                          Módulos
                        </button>
                        {tenant.is_active ? (
                          <button
                            disabled={suspend.isPending}
                            onClick={() => void suspend.mutate(tenant.id)}
                            className="text-yellow-600 hover:underline disabled:opacity-50"
                          >
                            Suspender
                          </button>
                        ) : (
                          <button
                            disabled={activate.isPending}
                            onClick={() => void activate.mutate(tenant.id)}
                            className="text-green-600 hover:underline disabled:opacity-50"
                          >
                            Reativar
                          </button>
                        )}
                        <button
                          onClick={() =>
                            setConfirmDelete({ id: tenant.id, name: tenant.name })
                          }
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

          {totalPages > 1 && (
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>
                {data.total} empresas — página {page} de {totalPages}
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
                  disabled={page >= totalPages}
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

      {showProvision && <CompanyProvisionModal onClose={() => setShowProvision(false)} />}

      {modulesFor && (
        <CompanyModulesModal
          tenantId={modulesFor.id}
          tenantName={modulesFor.name}
          onClose={() => setModulesFor(null)}
        />
      )}

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
