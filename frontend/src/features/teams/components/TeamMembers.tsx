import { useState } from "react";
import { useParams } from "react-router";

import { useAuth } from "@/shared/hooks/useAuth";
import { hasPermission, Permissions } from "@/utils/permissions";
import { useAddMember, useRemoveMember, useTeam, useTeamMembers } from "../api";

export function TeamMembers() {
  const { id } = useParams<{ id: string }>();
  const { session } = useAuth();
  const canManage = hasPermission(session, Permissions.TEAM_MANAGE);

  const { data: team, isLoading: teamLoading } = useTeam(id ?? "");
  const { data: members, isLoading: membersLoading } = useTeamMembers(id ?? "");
  const addMember = useAddMember(id ?? "");
  const removeMember = useRemoveMember(id ?? "");

  const [newUserId, setNewUserId] = useState("");
  const [addError, setAddError] = useState<string | null>(null);

  if (teamLoading || membersLoading) {
    return <div className="p-6 text-gray-500">Carregando membros...</div>;
  }

  if (!team) {
    return <div className="p-6 text-red-600">Equipe não encontrada.</div>;
  }

  async function handleAddMember(e: React.FormEvent) {
    e.preventDefault();
    setAddError(null);
    try {
      await addMember.mutateAsync({ user_id: newUserId.trim() });
      setNewUserId("");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message ??
        "Erro ao adicionar membro.";
      setAddError(msg);
    }
  }

  return (
    <div className="p-6 space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-semibold">{team.name}</h1>
        {team.description && <p className="text-gray-600 mt-1 text-sm">{team.description}</p>}
        <span
          className={`inline-block mt-2 px-2 py-0.5 text-xs rounded-full font-medium ${
            team.is_active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
          }`}
        >
          {team.is_active ? "Ativa" : "Inativa"}
        </span>
      </div>

      {canManage && team.is_active && (
        <div>
          <h2 className="text-lg font-medium mb-3">Adicionar membro</h2>
          {addError && (
            <p className="mb-2 text-sm text-red-600">{addError}</p>
          )}
          <form
            onSubmit={(e) => void handleAddMember(e)}
            className="flex gap-2"
          >
            <input
              type="text"
              required
              value={newUserId}
              onChange={(e) => setNewUserId(e.target.value)}
              placeholder="UUID do usuário"
              className="flex-1 border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              disabled={addMember.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 transition text-sm"
            >
              Adicionar
            </button>
          </form>
        </div>
      )}

      <div>
        <h2 className="text-lg font-medium mb-3">
          Membros ({members?.length ?? 0})
        </h2>

        {!members || members.length === 0 ? (
          <p className="text-gray-500 text-sm">Nenhum membro nesta equipe.</p>
        ) : (
          <ul className="divide-y rounded border">
            {members.map((member) => (
              <li key={member.user_id} className="flex items-center justify-between px-4 py-3">
                <span className="text-sm font-mono text-gray-700">{member.user_id}</span>
                {canManage && (
                  <button
                    onClick={() => {
                      if (confirm("Remover membro da equipe?")) {
                        removeMember.mutate(member.user_id);
                      }
                    }}
                    className="text-red-500 hover:underline text-xs"
                  >
                    Remover
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
