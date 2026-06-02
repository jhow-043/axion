import { useEffect, useState } from "react";

import { useCreateSector, useSector, useUpdateSector } from "../api";
import type { SectorCreate, SectorUpdate } from "../types";

interface SectorFormProps {
  sectorId?: string;
  onSuccess: () => void;
  onCancel: () => void;
}

export function SectorForm({ sectorId, onSuccess, onCancel }: SectorFormProps) {
  const isEditing = Boolean(sectorId);
  const { data: existing } = useSector(sectorId ?? "");
  const createSector = useCreateSector();
  const updateSector = useUpdateSector(sectorId ?? "");

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (existing) {
      setName(existing.name);
      setDescription(existing.description ?? "");
    }
  }, [existing]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    try {
      if (isEditing) {
        const payload: SectorUpdate = {};
        if (name !== existing?.name) payload.name = name;
        if (description !== (existing?.description ?? "")) payload.description = description || null;
        await updateSector.mutateAsync(payload);
      } else {
        const payload: SectorCreate = { name, description: description || null };
        await createSector.mutateAsync(payload);
      }
      onSuccess();
    } catch {
      setError("Erro ao salvar. Verifique os dados e tente novamente.");
    }
  }

  const isPending = createSector.isPending || updateSector.isPending;

  return (
    <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
      <div>
        <label className="block text-sm font-medium mb-1">Nome *</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          minLength={2}
          maxLength={255}
          required
          className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Descrição</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          maxLength={1000}
          rows={3}
          className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="flex justify-end gap-3">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border rounded text-sm hover:bg-gray-50"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={isPending}
          className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50"
        >
          {isPending ? "Salvando…" : isEditing ? "Salvar alterações" : "Criar setor"}
        </button>
      </div>
    </form>
  );
}
