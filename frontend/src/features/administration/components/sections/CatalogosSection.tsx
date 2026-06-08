import { useState } from "react";

import {
  useCategories,
  useCreateCategory,
  useDeactivateCategory,
  useUpdateCategory,
  usePriorities,
  useCreatePriority,
  useDeactivatePriority,
  useUpdatePriority,
  useStatuses,
  useUpdateStatus,
  usePendingReasons,
  useCreatePendingReason,
  useDeactivatePendingReason,
  useUpdatePendingReason,
  type Category,
  type Priority,
  type Status,
  type PendingReason,
} from "@/features/catalog/api";

type Tab = "categorias" | "prioridades" | "status" | "motivos";

export function CatalogosSection() {
  const [tab, setTab] = useState<Tab>("categorias");

  return (
    <div className="p-6 space-y-4">
      <h2 className="text-xl font-semibold">Catálogos</h2>
      <p className="text-sm text-gray-600">
        Configure prioridades, status, categorias e motivos de pendência.
      </p>

      <div className="flex gap-0 border-b">
        {(
          [
            { key: "categorias", label: "Categorias" },
            { key: "prioridades", label: "Prioridades" },
            { key: "status", label: "Status" },
            { key: "motivos", label: "Motivos de Pendência" },
          ] as const
        ).map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === key
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <div>
        {tab === "categorias" && <CategoriasTab />}
        {tab === "prioridades" && <PrioridadesTab />}
        {tab === "status" && <StatusTab />}
        {tab === "motivos" && <MotivosTab />}
      </div>
    </div>
  );
}

// ── Categorias ─────────────────────────────────────────────────────────────────

function CategoriasTab() {
  const { data, isLoading } = useCategories(false);
  const create = useCreateCategory();
  const deactivate = useDeactivateCategory();
  const [editing, setEditing] = useState<Category | null>(null);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const update = useUpdateCategory(editing?.id ?? "");

  function startCreate() {
    setEditing(null);
    setName("");
    setDescription("");
    setCreating(true);
  }

  function startEdit(cat: Category) {
    setCreating(false);
    setEditing(cat);
    setName(cat.name);
    setDescription(cat.description ?? "");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (editing) {
      await update.mutateAsync({ name, description: description || null });
      setEditing(null);
    } else {
      await create.mutateAsync({ name, description: description || null });
      setCreating(false);
    }
    setName("");
    setDescription("");
  }

  if (isLoading) return <div className="text-gray-500 text-sm">Carregando...</div>;

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button
          onClick={startCreate}
          className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 transition"
        >
          Nova categoria
        </button>
      </div>

      {(creating || editing) && (
        <form onSubmit={(e) => void handleSubmit(e)} className="border rounded p-4 space-y-3 bg-gray-50 max-w-md">
          <h3 className="text-sm font-medium">{editing ? "Editar categoria" : "Nova categoria"}</h3>
          <div>
            <label className="block text-xs font-medium mb-1">Nome *</label>
            <input
              required
              minLength={2}
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full border rounded px-3 py-1.5 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">Descrição</label>
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full border rounded px-3 py-1.5 text-sm"
            />
          </div>
          <div className="flex gap-2">
            <button type="submit" className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
              Salvar
            </button>
            <button
              type="button"
              onClick={() => { setCreating(false); setEditing(null); }}
              className="px-3 py-1.5 border rounded text-sm hover:bg-gray-100"
            >
              Cancelar
            </button>
          </div>
        </form>
      )}

      <SimpleTable
        items={data?.items ?? []}
        columns={[
          { label: "Nome", render: (c: Category) => c.name },
          { label: "Descrição", render: (c: Category) => c.description ?? "—" },
          { label: "Status", render: (c: Category) => <StatusBadge active={c.is_active} /> },
        ]}
        actions={(c: Category) => (
          <>
            <button onClick={() => startEdit(c)} className="text-blue-600 hover:underline text-xs">Editar</button>
            {c.is_active && (
              <button onClick={() => void deactivate.mutate(c.id)} className="text-red-500 hover:underline text-xs ml-3">
                Desativar
              </button>
            )}
          </>
        )}
      />
    </div>
  );
}

// ── Prioridades ────────────────────────────────────────────────────────────────

function PrioridadesTab() {
  const { data, isLoading } = usePriorities(false);
  const create = useCreatePriority();
  const deactivate = useDeactivatePriority();
  const [editing, setEditing] = useState<Priority | null>(null);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [color, setColor] = useState("");
  const [order, setOrder] = useState("1");
  const update = useUpdatePriority(editing?.id ?? "");

  function startCreate() {
    setEditing(null);
    setName(""); setCode(""); setColor(""); setOrder("1");
    setCreating(true);
  }

  function startEdit(p: Priority) {
    setCreating(false);
    setEditing(p);
    setName(p.name);
    setCode(p.code);
    setColor(p.color ?? "");
    setOrder(String(p.order));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (editing) {
      await update.mutateAsync({ name, color: color || null, order: Number(order) });
      setEditing(null);
    } else {
      await create.mutateAsync({ name, code, color: color || null, order: Number(order) });
      setCreating(false);
    }
  }

  if (isLoading) return <div className="text-gray-500 text-sm">Carregando...</div>;

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button onClick={startCreate} className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 transition">
          Nova prioridade
        </button>
      </div>

      {(creating || editing) && (
        <form onSubmit={(e) => void handleSubmit(e)} className="border rounded p-4 space-y-3 bg-gray-50 max-w-md">
          <h3 className="text-sm font-medium">{editing ? "Editar prioridade" : "Nova prioridade"}</h3>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium mb-1">Nome *</label>
              <input required minLength={1} value={name} onChange={(e) => setName(e.target.value)} className="w-full border rounded px-3 py-1.5 text-sm" />
            </div>
            {!editing && (
              <div>
                <label className="block text-xs font-medium mb-1">Código * (ex: high)</label>
                <input required value={code} onChange={(e) => setCode(e.target.value)} pattern="^[a-z][a-z0-9_]*$" className="w-full border rounded px-3 py-1.5 text-sm" />
              </div>
            )}
            <div>
              <label className="block text-xs font-medium mb-1">Cor (hex)</label>
              <input value={color} onChange={(e) => setColor(e.target.value)} placeholder="#ef4444" className="w-full border rounded px-3 py-1.5 text-sm" />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Ordem *</label>
              <input required type="number" min={1} value={order} onChange={(e) => setOrder(e.target.value)} className="w-full border rounded px-3 py-1.5 text-sm" />
            </div>
          </div>
          <div className="flex gap-2">
            <button type="submit" className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">Salvar</button>
            <button type="button" onClick={() => { setCreating(false); setEditing(null); }} className="px-3 py-1.5 border rounded text-sm hover:bg-gray-100">Cancelar</button>
          </div>
        </form>
      )}

      <SimpleTable
        items={data?.items ?? []}
        columns={[
          { label: "Nome", render: (p: Priority) => (
            <span className="flex items-center gap-2">
              {p.color && <span className="w-3 h-3 rounded-full inline-block" style={{ background: p.color }} />}
              {p.name}
            </span>
          )},
          { label: "Código", render: (p: Priority) => <code className="text-xs bg-gray-100 px-1 rounded">{p.code}</code> },
          { label: "Ordem", render: (p: Priority) => p.order },
          { label: "Status", render: (p: Priority) => <StatusBadge active={p.is_active} /> },
        ]}
        actions={(p: Priority) => (
          <>
            <button onClick={() => startEdit(p)} className="text-blue-600 hover:underline text-xs">Editar</button>
            {p.is_active && !p.is_default && (
              <button onClick={() => void deactivate.mutate(p.id)} className="text-red-500 hover:underline text-xs ml-3">Desativar</button>
            )}
          </>
        )}
      />
    </div>
  );
}

// ── Status ─────────────────────────────────────────────────────────────────────

function StatusTab() {
  const { data, isLoading } = useStatuses(false);
  const [editing, setEditing] = useState<Status | null>(null);
  const [name, setName] = useState("");
  const [order, setOrder] = useState("1");
  const update = useUpdateStatus(editing?.id ?? "");

  function startEdit(s: Status) {
    setEditing(s);
    setName(s.name);
    setOrder(String(s.order));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await update.mutateAsync({ name, order: Number(order) });
    setEditing(null);
  }

  if (isLoading) return <div className="text-gray-500 text-sm">Carregando...</div>;

  return (
    <div className="space-y-4">
      <p className="text-xs text-gray-500">
        Status são gerenciados pela máquina de estados do sistema. Você pode editar o nome e a ordem de exibição.
      </p>

      {editing && (
        <form onSubmit={(e) => void handleSubmit(e)} className="border rounded p-4 space-y-3 bg-gray-50 max-w-md">
          <h3 className="text-sm font-medium">Editar status</h3>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium mb-1">Nome *</label>
              <input required value={name} onChange={(e) => setName(e.target.value)} className="w-full border rounded px-3 py-1.5 text-sm" />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Ordem</label>
              <input type="number" min={1} value={order} onChange={(e) => setOrder(e.target.value)} className="w-full border rounded px-3 py-1.5 text-sm" />
            </div>
          </div>
          <div className="flex gap-2">
            <button type="submit" className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">Salvar</button>
            <button type="button" onClick={() => setEditing(null)} className="px-3 py-1.5 border rounded text-sm hover:bg-gray-100">Cancelar</button>
          </div>
        </form>
      )}

      <SimpleTable
        items={data?.items ?? []}
        columns={[
          { label: "Nome", render: (s: Status) => s.name },
          { label: "Código", render: (s: Status) => <code className="text-xs bg-gray-100 px-1 rounded">{s.code}</code> },
          { label: "Ordem", render: (s: Status) => s.order },
          { label: "Requer motivo", render: (s: Status) => s.requires_reason ? "Sim" : "—" },
          { label: "Requer solução", render: (s: Status) => s.requires_solution ? "Sim" : "—" },
          { label: "Terminal", render: (s: Status) => s.is_terminal ? "Sim" : "—" },
        ]}
        actions={(s: Status) => (
          <button onClick={() => startEdit(s)} className="text-blue-600 hover:underline text-xs">Editar</button>
        )}
      />
    </div>
  );
}

// ── Motivos de Pendência ───────────────────────────────────────────────────────

function MotivosTab() {
  const { data, isLoading } = usePendingReasons(false);
  const create = useCreatePendingReason();
  const deactivate = useDeactivatePendingReason();
  const [editing, setEditing] = useState<PendingReason | null>(null);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const update = useUpdatePendingReason(editing?.id ?? "");

  function startCreate() {
    setEditing(null);
    setName(""); setDescription("");
    setCreating(true);
  }

  function startEdit(r: PendingReason) {
    setCreating(false);
    setEditing(r);
    setName(r.name);
    setDescription(r.description ?? "");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (editing) {
      await update.mutateAsync({ name, description: description || null });
      setEditing(null);
    } else {
      await create.mutateAsync({ name, description: description || null });
      setCreating(false);
    }
    setName(""); setDescription("");
  }

  if (isLoading) return <div className="text-gray-500 text-sm">Carregando...</div>;

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button onClick={startCreate} className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 transition">
          Novo motivo
        </button>
      </div>

      {(creating || editing) && (
        <form onSubmit={(e) => void handleSubmit(e)} className="border rounded p-4 space-y-3 bg-gray-50 max-w-md">
          <h3 className="text-sm font-medium">{editing ? "Editar motivo" : "Novo motivo de pendência"}</h3>
          <div>
            <label className="block text-xs font-medium mb-1">Nome *</label>
            <input required minLength={2} value={name} onChange={(e) => setName(e.target.value)} className="w-full border rounded px-3 py-1.5 text-sm" />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">Descrição</label>
            <input value={description} onChange={(e) => setDescription(e.target.value)} className="w-full border rounded px-3 py-1.5 text-sm" />
          </div>
          <div className="flex gap-2">
            <button type="submit" className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">Salvar</button>
            <button type="button" onClick={() => { setCreating(false); setEditing(null); }} className="px-3 py-1.5 border rounded text-sm hover:bg-gray-100">Cancelar</button>
          </div>
        </form>
      )}

      <SimpleTable
        items={data?.items ?? []}
        columns={[
          { label: "Nome", render: (r: PendingReason) => r.name },
          { label: "Descrição", render: (r: PendingReason) => r.description ?? "—" },
          { label: "Status", render: (r: PendingReason) => <StatusBadge active={r.is_active} /> },
        ]}
        actions={(r: PendingReason) => (
          <>
            <button onClick={() => startEdit(r)} className="text-blue-600 hover:underline text-xs">Editar</button>
            {r.is_active && (
              <button onClick={() => void deactivate.mutate(r.id)} className="text-red-500 hover:underline text-xs ml-3">Desativar</button>
            )}
          </>
        )}
      />
    </div>
  );
}

// ── Shared helpers ─────────────────────────────────────────────────────────────

function StatusBadge({ active }: { active: boolean }) {
  return (
    <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
      {active ? "Ativo" : "Inativo"}
    </span>
  );
}

interface Column<T> {
  label: string;
  render: (item: T) => React.ReactNode;
}

function SimpleTable<T extends { id: string }>({
  items,
  columns,
  actions,
}: {
  items: T[];
  columns: Column<T>[];
  actions?: (item: T) => React.ReactNode;
}) {
  if (items.length === 0) {
    return <div className="text-center text-gray-500 py-6 text-sm">Nenhum item cadastrado.</div>;
  }
  return (
    <div className="overflow-x-auto rounded border">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-left">
          <tr>
            {columns.map((c) => (
              <th key={c.label} className="px-4 py-2.5 font-medium text-gray-700">{c.label}</th>
            ))}
            {actions && <th className="px-4 py-2.5 font-medium text-gray-700">Ações</th>}
          </tr>
        </thead>
        <tbody className="divide-y">
          {items.map((item) => (
            <tr key={item.id} className="hover:bg-gray-50">
              {columns.map((c) => (
                <td key={c.label} className="px-4 py-2.5 text-gray-700">{c.render(item)}</td>
              ))}
              {actions && <td className="px-4 py-2.5">{actions(item)}</td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
