import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router";

import { useSectors } from "@/features/locations/api";
import { useCreateEquipment, useEquipment, useUpdateEquipment } from "../api";

export function EquipmentForm() {
  const { id } = useParams<{ id?: string }>();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const { data: existing, isLoading } = useEquipment(id ?? "");
  const { data: sectorsData } = useSectors({ is_active: true, page_size: 100 });
  const createEquipment = useCreateEquipment();
  const updateEquipment = useUpdateEquipment(id ?? "");

  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [sectorId, setSectorId] = useState("");
  const [manufacturer, setManufacturer] = useState("");
  const [model, setModel] = useState("");
  const [serialNumber, setSerialNumber] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (existing) {
      setCode(existing.code);
      setName(existing.name);
      setSectorId(existing.sector_id);
      setManufacturer(existing.manufacturer ?? "");
      setModel(existing.model ?? "");
      setSerialNumber(existing.serial_number ?? "");
      setNotes(existing.notes ?? "");
    }
  }, [existing]);

  if (isEdit && isLoading) {
    return <div className="p-6 text-gray-500">Carregando...</div>;
  }

  const sectors = sectorsData?.items ?? [];

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    try {
      if (isEdit && id) {
        await updateEquipment.mutateAsync({
          code: code || undefined,
          name: name || undefined,
          sector_id: sectorId || undefined,
          manufacturer: manufacturer || null,
          model: model || null,
          serial_number: serialNumber || null,
          notes: notes || null,
        });
      } else {
        await createEquipment.mutateAsync({
          code,
          name,
          sector_id: sectorId,
          manufacturer: manufacturer || null,
          model: model || null,
          serial_number: serialNumber || null,
          notes: notes || null,
        });
      }
      void navigate("/equipments");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message ??
        "Erro ao salvar equipamento.";
      setError(msg);
    }
  }

  const isPending = createEquipment.isPending || updateEquipment.isPending;

  return (
    <div className="p-6 max-w-2xl">
      <h1 className="text-2xl font-semibold mb-6">
        {isEdit ? "Editar equipamento" : "Novo equipamento"}
      </h1>

      {error && (
        <div className="mb-4 px-4 py-3 bg-red-50 text-red-700 rounded border border-red-200 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Código *</label>
            <input
              type="text"
              required
              minLength={1}
              maxLength={100}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="Ex.: EQ-001"
              className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Nome *</label>
            <input
              type="text"
              required
              minLength={2}
              maxLength={255}
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ex.: Motor Elétrico 10cv"
              className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Setor *</label>
          <select
            required
            value={sectorId}
            onChange={(e) => setSectorId(e.target.value)}
            className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Selecione um setor...</option>
            {sectors.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Fabricante</label>
            <input
              type="text"
              maxLength={255}
              value={manufacturer}
              onChange={(e) => setManufacturer(e.target.value)}
              placeholder="Ex.: WEG"
              className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Modelo</label>
            <input
              type="text"
              maxLength={255}
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder="Ex.: W22"
              className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Número de série</label>
          <input
            type="text"
            maxLength={100}
            value={serialNumber}
            onChange={(e) => setSerialNumber(e.target.value)}
            placeholder="Ex.: SN-12345"
            className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Observações</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Informações adicionais sobre o equipamento..."
            rows={3}
            className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={isPending}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 transition"
          >
            {isEdit ? "Salvar" : "Criar"}
          </button>
          <button
            type="button"
            onClick={() => void navigate("/equipments")}
            className="px-4 py-2 border rounded hover:bg-gray-50 transition"
          >
            Cancelar
          </button>
        </div>
      </form>
    </div>
  );
}
