import { useState } from "react";
import { useNavigate, useParams } from "react-router";

import { useCreateTeam, useTeam, useUpdateTeam } from "../api";

export function TeamForm() {
  const { id } = useParams<{ id?: string }>();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const { data: existing, isLoading } = useTeam(id ?? "");
  const createTeam = useCreateTeam();
  const updateTeam = useUpdateTeam(id ?? "");

  const [name, setName] = useState(existing?.name ?? "");
  const [description, setDescription] = useState(existing?.description ?? "");
  const [error, setError] = useState<string | null>(null);

  if (isEdit && isLoading) {
    return <div className="p-6 text-gray-500">Carregando...</div>;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    try {
      if (isEdit && id) {
        await updateTeam.mutateAsync({
          name: name || undefined,
          description: description || undefined,
        });
      } else {
        await createTeam.mutateAsync({ name, description: description || undefined });
      }
      void navigate("/teams");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message ??
        "Erro ao salvar equipe.";
      setError(msg);
    }
  }

  return (
    <div className="p-6 max-w-lg">
      <h1 className="text-2xl font-semibold mb-6">
        {isEdit ? "Editar equipe" : "Nova equipe"}
      </h1>

      {error && (
        <div className="mb-4 px-4 py-3 bg-red-50 text-red-700 rounded border border-red-200 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Nome *</label>
          <input
            type="text"
            required
            minLength={2}
            maxLength={255}
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Ex.: Elétrica"
            className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Descrição</label>
          <textarea
            maxLength={1000}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Descrição opcional da equipe"
            rows={3}
            className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={createTeam.isPending || updateTeam.isPending}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 transition"
          >
            {isEdit ? "Salvar" : "Criar"}
          </button>
          <button
            type="button"
            onClick={() => void navigate("/teams")}
            className="px-4 py-2 border rounded hover:bg-gray-50 transition"
          >
            Cancelar
          </button>
        </div>
      </form>
    </div>
  );
}
