import { useState } from "react";
import { useNavigate } from "react-router";

import { useAuth } from "@/shared/hooks/useAuth";
import { hasPermission, Permissions } from "@/utils/permissions";
import { useUsers } from "../api";
import type { UserFilters } from "../types";

export function UserList() {
  const { session } = useAuth();
  const navigate = useNavigate();
  const canManage = hasPermission(session, Permissions.USER_MANAGE);

  const [filters, setFilters] = useState<UserFilters>({ page: 1, page_size: 20 });
  const { data, isLoading, error } = useUsers(filters);

  if (isLoading) {
    return (
      <div className="p-6 space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-12 bg-gray-100 rounded animate-pulse" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-red-600">
        Erro ao carregar usuários. Tente novamente.
      </div>
    );
  }

  if (!data || data.items.length === 0) {
    return (
      <div className="p-6 text-center text-gray-500">
        Nenhum usuário encontrado.
        {canManage && (
          <button
            onClick={() => void navigate("/users/new")}
            className="ml-2 text-blue-600 underline"
          >
            Criar usuário
          </button>
        )}
      </div>
    );
  }

  const totalPages = Math.ceil(data.total / (filters.page_size ?? 20));

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Usuários</h1>
        {canManage && (
          <button
            onClick={() => void navigate("/users/new")}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            Novo usuário
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <input
          type="text"
          placeholder="Filtrar por nome"
          className="border rounded px-3 py-1.5 text-sm"
          value={filters.name ?? ""}
          onChange={(e) =>
            setFilters((f) => ({ ...f, name: e.target.value || undefined, page: 1 }))
          }
        />
        <input
          type="text"
          placeholder="Filtrar por email"
          className="border rounded px-3 py-1.5 text-sm"
          value={filters.email ?? ""}
          onChange={(e) =>
            setFilters((f) => ({ ...f, email: e.target.value || undefined, page: 1 }))
          }
        />
        <select
          className="border rounded px-3 py-1.5 text-sm"
          value={filters.is_active === undefined ? "" : String(filters.is_active)}
          onChange={(e) =>
            setFilters((f) => ({
              ...f,
              is_active: e.target.value === "" ? undefined : e.target.value === "true",
              page: 1,
            }))
          }
        >
          <option value="">Todos os status</option>
          <option value="true">Ativo</option>
          <option value="false">Inativo</option>
        </select>
        <select
          className="border rounded px-3 py-1.5 text-sm"
          value={filters.role_code ?? ""}
          onChange={(e) =>
            setFilters((f) => ({
              ...f,
              role_code: e.target.value || undefined,
              page: 1,
            }))
          }
        >
          <option value="">Todos os papéis</option>
          <option value="admin">Admin</option>
          <option value="supervisor">Supervisor</option>
          <option value="technician">Técnico</option>
          <option value="requester">Solicitante</option>
        </select>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded border">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left">
            <tr>
              <th className="px-4 py-3 font-medium">Nome</th>
              <th className="px-4 py-3 font-medium">Email</th>
              <th className="px-4 py-3 font-medium">Papéis</th>
              <th className="px-4 py-3 font-medium">Status</th>
              {canManage && <th className="px-4 py-3 font-medium">Ações</th>}
            </tr>
          </thead>
          <tbody className="divide-y">
            {data.items.map((user) => (
              <tr
                key={user.id}
                className="hover:bg-gray-50 cursor-pointer"
                onClick={() => void navigate(`/users/${user.id}`)}
              >
                <td className="px-4 py-3">{user.name}</td>
                <td className="px-4 py-3 text-gray-600">{user.email}</td>
                <td className="px-4 py-3">
                  <span className="flex flex-wrap gap-1">
                    {user.roles.map((r) => (
                      <span
                        key={r.id}
                        className="px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-700"
                      >
                        {r.name}
                      </span>
                    ))}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                      user.is_active
                        ? "bg-green-100 text-green-700"
                        : "bg-red-100 text-red-700"
                    }`}
                  >
                    {user.is_active ? "Ativo" : "Inativo"}
                  </span>
                </td>
                {canManage && (
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={() => void navigate(`/users/${user.id}`)}
                      className="text-blue-600 hover:underline text-xs"
                    >
                      Editar
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>
            {data.total} usuários — página {filters.page} de {totalPages}
          </span>
          <div className="flex gap-2">
            <button
              disabled={(filters.page ?? 1) <= 1}
              onClick={() => setFilters((f) => ({ ...f, page: (f.page ?? 1) - 1 }))}
              className="px-3 py-1 border rounded disabled:opacity-40"
            >
              Anterior
            </button>
            <button
              disabled={(filters.page ?? 1) >= totalPages}
              onClick={() => setFilters((f) => ({ ...f, page: (f.page ?? 1) + 1 }))}
              className="px-3 py-1 border rounded disabled:opacity-40"
            >
              Próxima
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
