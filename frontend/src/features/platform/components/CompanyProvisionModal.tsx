import { useState } from "react";
import { X } from "lucide-react";
import { useProvisionCompany } from "../api";
import type { TenantCreate } from "../types";

const EMPTY: TenantCreate = {
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

interface Props {
  onClose: () => void;
}

export function CompanyProvisionModal({ onClose }: Props) {
  const [form, setForm] = useState<TenantCreate>(EMPTY);
  const [error, setError] = useState<string | null>(null);
  const provision = useProvisionCompany();

  function handleNameChange(name: string) {
    setForm((f) => ({ ...f, name, slug: slugify(name) }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await provision.mutateAsync(form);
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao provisionar empresa.");
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Nova empresa</h3>
          <button onClick={onClose}>
            <X className="h-4 w-4 text-muted-foreground" />
          </button>
        </div>

        <form onSubmit={(e) => void handleSubmit(e)} className="space-y-3">
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
          <p className="text-xs text-muted-foreground">Usuário administrador inicial</p>
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

          {error && <p className="text-sm text-red-600">{error}</p>}

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
              onClick={onClose}
              className="px-4 py-2 border rounded text-sm hover:bg-muted"
            >
              Cancelar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
