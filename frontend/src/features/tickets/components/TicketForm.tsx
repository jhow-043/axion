import { useMemo, useState } from "react";
import { useNavigate } from "react-router";

import { useCategories, usePriorities } from "@/features/catalog/api";
import { useEquipments } from "@/features/equipments/api";
import { useLocations, useSectors } from "@/features/locations/api";
import { useTeams } from "@/features/teams/api";
import { useCreateTicket } from "../api";
import type { TicketCreate } from "../types";

export function TicketForm() {
  const navigate = useNavigate();
  const createTicket = useCreateTicket();

  const { data: prioritiesData } = usePriorities();
  const { data: categoriesData } = useCategories();
  const { data: sectorsData } = useSectors({ is_active: true, page_size: 100 });
  const { data: locationsData } = useLocations({ is_active: true, page_size: 100 });
  const { data: teamsData } = useTeams({ is_active: true, page_size: 100 });

  const [type, setType] = useState<"industrial" | "predial">("industrial");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priorityId, setPriorityId] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [sectorFilter, setSectorFilter] = useState("");
  const [equipmentId, setEquipmentId] = useState("");
  const [locationId, setLocationId] = useState("");
  const [teamId, setTeamId] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Load equipments filtered by selected sector
  const { data: equipmentsData } = useEquipments({
    is_active: true,
    page_size: 100,
    sector_id: sectorFilter || undefined,
  });

  const priorities = prioritiesData?.items ?? [];
  const categories = categoriesData?.items ?? [];
  const sectors = sectorsData?.items ?? [];
  const equipments = equipmentsData?.items ?? [];
  const locations = locationsData?.items ?? [];
  const teams = teamsData?.items ?? [];

  const sectorMap = useMemo(() => {
    const m: Record<string, string> = {};
    for (const s of sectors) m[s.id] = s.name;
    return m;
  }, [sectors]);

  const selectedEquipment = useMemo(
    () => equipments.find((eq) => eq.id === equipmentId) ?? null,
    [equipments, equipmentId],
  );

  function handleTypeChange(newType: "industrial" | "predial") {
    setType(newType);
    // Reset the field not relevant for the new type
    if (newType === "predial") {
      setEquipmentId("");
      setSectorFilter("");
    } else {
      setLocationId("");
    }
  }

  function handleSectorFilterChange(sid: string) {
    setSectorFilter(sid);
    setEquipmentId(""); // reset equipment when sector changes
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (type === "industrial" && !equipmentId) {
      setError("Chamado industrial exige um equipamento.");
      return;
    }
    if (type === "predial" && !locationId) {
      setError("Chamado predial exige um local.");
      return;
    }

    const payload: TicketCreate = {
      type,
      title,
      description,
      priority_id: priorityId,
      category_id: categoryId || undefined,
      equipment_id: equipmentId || undefined,
      location_id: locationId || undefined,
      team_id: teamId || undefined,
    };

    try {
      const ticket = await createTicket.mutateAsync(payload);
      void navigate(`/tickets/${ticket.id}`);
    } catch {
      setError("Erro ao criar chamado. Verifique os dados e tente novamente.");
    }
  }

  return (
    <div className="p-6 max-w-2xl">
      <h1 className="text-2xl font-semibold mb-6">Novo chamado</h1>

      {error && (
        <div className="mb-4 px-4 py-3 bg-red-50 text-red-700 rounded border border-red-200 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Tipo *</label>
            <select
              required
              value={type}
              onChange={(e) => handleTypeChange(e.target.value as "industrial" | "predial")}
              className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="industrial">Industrial</option>
              <option value="predial">Predial</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Prioridade *</label>
            <select
              required
              value={priorityId}
              onChange={(e) => setPriorityId(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Selecione a prioridade...</option>
              {priorities.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Título *</label>
          <input
            type="text"
            required
            minLength={5}
            maxLength={255}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Descreva brevemente o problema..."
            className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Descrição *</label>
          <textarea
            required
            minLength={10}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Descreva o problema em detalhes..."
            rows={4}
            className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Industrial: setor + equipamento */}
        {type === "industrial" && (
          <div className="space-y-3 p-4 bg-blue-50 rounded border border-blue-100">
            <p className="text-xs font-medium text-blue-700 uppercase tracking-wide">
              Equipamento *
            </p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-600 mb-1">Filtrar por setor</label>
                <select
                  value={sectorFilter}
                  onChange={(e) => handleSectorFilterChange(e.target.value)}
                  className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Todos os setores</option>
                  {sectors.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Equipamento *</label>
                <select
                  required={type === "industrial"}
                  value={equipmentId}
                  onChange={(e) => setEquipmentId(e.target.value)}
                  className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Selecione o equipamento...</option>
                  {equipments.map((eq) => (
                    <option key={eq.id} value={eq.id}>
                      {eq.code} — {eq.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {selectedEquipment && (
              <div className="flex gap-4 text-xs text-gray-600 bg-white rounded px-3 py-2 border">
                <span>
                  <span className="font-medium">Código:</span> {selectedEquipment.code}
                </span>
                <span>
                  <span className="font-medium">Setor:</span>{" "}
                  {sectorMap[selectedEquipment.sector_id] ?? "—"}
                </span>
                {selectedEquipment.manufacturer && (
                  <span>
                    <span className="font-medium">Fabricante:</span> {selectedEquipment.manufacturer}
                  </span>
                )}
              </div>
            )}
          </div>
        )}

        {/* Predial: local */}
        {type === "predial" && (
          <div className="p-4 bg-green-50 rounded border border-green-100">
            <label className="block text-sm font-medium mb-1 text-green-700">Local *</label>
            <select
              required={type === "predial"}
              value={locationId}
              onChange={(e) => setLocationId(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Selecione o local...</option>
              {locations.map((loc) => (
                <option key={loc.id} value={loc.id}>
                  {loc.name}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Categoria</label>
            <select
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Sem categoria</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Equipe</label>
            <select
              value={teamId}
              onChange={(e) => setTeamId(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Sem equipe</option>
              {teams.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={createTicket.isPending}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 transition"
          >
            {createTicket.isPending ? "Criando…" : "Criar chamado"}
          </button>
          <button
            type="button"
            onClick={() => void navigate("/tickets")}
            className="px-4 py-2 border rounded hover:bg-gray-50 transition"
          >
            Cancelar
          </button>
        </div>
      </form>
    </div>
  );
}
