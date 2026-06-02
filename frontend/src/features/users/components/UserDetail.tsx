import { useNavigate, useParams } from "react-router";

import { useAuth } from "@/shared/hooks/useAuth";
import { hasPermission, Permissions } from "@/utils/permissions";
import { useActivateUser, useDeactivateUser, useUser } from "../api";
import { RoleAssignment } from "./RoleAssignment";
import { UserForm } from "./UserForm";

export function UserDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { session } = useAuth();
  const canManage = hasPermission(session, Permissions.USER_MANAGE);

  const { data: user, isLoading, error } = useUser(id ?? "");
  const activateUser = useActivateUser();
  const deactivateUser = useDeactivateUser();

  if (isLoading) {
    return (
      <div className="p-6 space-y-3">
        <div className="h-8 w-48 bg-gray-100 rounded animate-pulse" />
        <div className="h-24 bg-gray-100 rounded animate-pulse" />
      </div>
    );
  }

  if (error || !user) {
    return (
      <div className="p-6 text-red-600">
        Usuário não encontrado.{" "}
        <button onClick={() => void navigate("/users")} className="underline text-blue-600">
          Voltar
        </button>
      </div>
    );
  }

  async function toggleActive() {
    if (!user) return;
    if (user.is_active) {
      await deactivateUser.mutateAsync(user.id);
    } else {
      await activateUser.mutateAsync(user.id);
    }
  }

  return (
    <div className="p-6 max-w-2xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={() => void navigate("/users")}
            className="text-sm text-gray-500 hover:underline mb-1 flex items-center gap-1"
          >
            ← Usuários
          </button>
          <h1 className="text-2xl font-semibold">{user.name}</h1>
          <p className="text-gray-500 text-sm">{user.email}</p>
        </div>

        {canManage && (
          <div className="flex gap-2">
            <button
              onClick={() => void toggleActive()}
              disabled={activateUser.isPending || deactivateUser.isPending}
              className={`px-3 py-1.5 text-sm rounded transition ${
                user.is_active
                  ? "bg-red-50 text-red-700 border border-red-200 hover:bg-red-100"
                  : "bg-green-50 text-green-700 border border-green-200 hover:bg-green-100"
              }`}
            >
              {user.is_active ? "Desativar" : "Ativar"}
            </button>
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        <span className="text-sm font-medium">Status:</span>
        <span
          className={`px-2 py-0.5 text-xs rounded-full font-medium ${
            user.is_active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
          }`}
        >
          {user.is_active ? "Ativo" : "Inativo"}
        </span>
      </div>

      {canManage && (
        <section className="border rounded p-4 space-y-3">
          <h2 className="font-medium">Editar dados</h2>
          <UserForm user={user} />
        </section>
      )}

      {canManage && (
        <section className="border rounded p-4">
          <RoleAssignment userId={user.id} currentRoles={user.roles} />
        </section>
      )}

      {!canManage && (
        <section className="border rounded p-4">
          <h3 className="font-medium text-sm mb-2">Papéis</h3>
          <div className="flex flex-wrap gap-2">
            {user.roles.map((r) => (
              <span
                key={r.id}
                className="px-2.5 py-1 bg-blue-100 text-blue-700 rounded-full text-xs"
              >
                {r.name}
              </span>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
