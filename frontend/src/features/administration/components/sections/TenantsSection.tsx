import { useState } from "react";
import { Plus, X } from "lucide-react";
import {
  useActivateTenant,
  useDeactivateTenant,
  useProvisionTenant,
  useTenants,
} from "../../api";
import type { TenantCreate } from "../../types";

const EMPTY_FORM: TenantCreate = {
  name: "",
  slug: "",
  admin_name: "",
  admin_email: "",
  admin_password: "",
};

function slugify(value: string) {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

export function TenantsSection() {
  const [page, setPage] = useState(1);
  const { data, isLoading, error } = useTenants(page, 20);
  const activate = useActivateTenant();
  const deactivate = useDeactivateTenant();
  const provision = useProvisionTenant();

  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<TenantCreate>(EMPTY_FORM);
  const [formError, setFormError] = useState<string | null>(null);

  const totalPages = data ? Math.ceil(data.total / 20) : 1;

  function handleNameChange(name: string) {
    setForm((f) => ({ ...f, name, slug: slugify(name) }));
  }

  async function handleProvision(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    try {
      await provision.mutateAsync(form);
      setForm(EMPTY_FORM);
      setShowForm(false);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Erro ao provisionar empresa. Tente novamente.";
      setFormError(message);
    }
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Gestão de Empresas</h2>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-1.5 px-3 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 transition"
        >
          <Plus className="h-4 w-4" />
          Nova empresa
        </button>
      </div>

      {/* Provision form modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Provisionar Nova Empresa</h3>
              <button onClick={() => setShowForm(false)}>
                <X className="h-4 w-4 text-gray-500" />
              </button>
            </div>

            <form onSubmit={(e) => void handleProvision(e)} className="space-y-3">
              <div>
                <label className="block text-sm font-medium mb-1">Nome da empresa *</label>
                <input
                  type="text"
                  required
                  className="border rounded px-3 py-2 w-full text-sm"
                  value={form.name}
                  onChange={(e) => handleNameChange(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Slug *</label>
                <input
                  type="text"
                  required
                  className="border rounded px-3 py-2 w-full text-sm font-mono"
                  value={form.slug}
                  onChange={(e) => setForm((f) => ({ ...f, slug: e.target.value }))}
                />
              </div>
              <hr />
              <p className="text-xs text-gray-500">Usuário administrador inicial</p>
              <div>
                <label className="block text-sm font-medium mb-1">Nome *</label>
                <input
                  type="text"
                  required
                  className="border rounded px-3 py-2 w-full text-sm"
                  value={form.admin_name}
                  onChange={(e) => setForm((f) => ({ ...f, admin_name: e.target.value }))}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Email *</label>
                <input
                  type="email"
                  required
                  className="border rounded px-3 py-2 w-full text-sm"
                  value={form.admin_email}
                  onChange={(e) => setForm((f) => ({ ...f, admin_email: e.target.value }))}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Senha *</label>
                <input
                  type="password"
                  required
                  minLength={8}
                  className="border rounded px-3 py-2 w-full text-sm"
                  value={form.admin_password}
                  onChange={(e) => setForm((f) => ({ ...f, admin_password: e.target.value }))}
                />
              </div>

              {formError && <p className="text-sm text-red-600">{formError}</p>}

              <div className="flex gap-2 pt-2">
                <button
                  type="submit"
                  disabled={provision.isPending}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50"
                >
                  {provision.isPending ? "Provisionando..." : "Provisionar"}
                </button>
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="px-4 py-2 border rounded text-sm hover:bg-gray-50"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {isLoading && (
        <div className="space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-12 bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      )}

      {error && <p className="text-red-600 text-sm">Erro ao carregar empresas.</p>}

      {data && (
        <>
          <div className="overflow-x-auto rounded border text-sm">
            <table className="w-full">
              <thead className="bg-gray-50 text-left">
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
                    <td colSpan={5} className="px-4 py-6 text-center text-gray-500">
                      Nenhuma empresa encontrada.
                    </td>
                  </tr>
                )}
                {data.items.map((tenant) => (
                  <tr key={tenant.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium">{tenant.name}</td>
                    <td className="px-4 py-3 font-mono text-gray-600">{tenant.slug}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                          tenant.is_active
                            ? "bg-green-100 text-green-700"
                            : "bg-red-100 text-red-700"
                        }`}
                      >
                        {tenant.is_active ? "Ativa" : "Inativa"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500">
                      {new Date(tenant.created_at).toLocaleDateString("pt-BR")}
                    </td>
                    <td className="px-4 py-3">
                      {tenant.is_active ? (
                        <button
                          disabled={deactivate.isPending}
                          onClick={() => void deactivate.mutate(tenant.id)}
                          className="text-red-600 hover:underline text-xs disabled:opacity-50"
                        >
                          Desativar
                        </button>
                      ) : (
                        <button
                          disabled={activate.isPending}
                          onClick={() => void activate.mutate(tenant.id)}
                          className="text-green-600 hover:underline text-xs disabled:opacity-50"
                        >
                          Ativar
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between text-sm text-gray-600">
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
    </div>
  );
}
