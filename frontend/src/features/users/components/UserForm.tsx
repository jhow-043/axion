import { useState } from "react";
import { useNavigate } from "react-router";

import { useCreateUser, useRoles, useUpdateUser } from "../api";
import type { UserResponse } from "../types";

interface UserFormProps {
  user?: UserResponse;
}

export function UserForm({ user }: UserFormProps) {
  const navigate = useNavigate();
  const isEdit = Boolean(user);

  const [name, setName] = useState(user?.name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [password, setPassword] = useState("");
  const [roleId, setRoleId] = useState(user?.roles[0]?.id ?? "");
  const [error, setError] = useState<string | null>(null);

  const { data: roles } = useRoles();
  const createUser = useCreateUser();
  const updateUser = useUpdateUser(user?.id ?? "");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    try {
      if (isEdit && user) {
        await updateUser.mutateAsync({ name, email });
      } else {
        const created = await createUser.mutateAsync({ name, email, password });
        void navigate(`/users/${created.id}`);
        return;
      }
      void navigate(`/users/${user!.id}`);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message ??
        "Erro ao salvar usuário.";
      setError(msg);
    }
  }

  const isPending = createUser.isPending || updateUser.isPending;

  return (
    <div className="p-6 max-w-lg">
      <h1 className="text-2xl font-semibold mb-6">
        {isEdit ? "Editar usuário" : "Novo usuário"}
      </h1>

      <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
            {error}
          </div>
        )}

        <div className="space-y-1">
          <label className="block text-sm font-medium">Nome</label>
          <input
            type="text"
            required
            minLength={2}
            maxLength={255}
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="space-y-1">
          <label className="block text-sm font-medium">Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {!isEdit && (
          <div className="space-y-1">
            <label className="block text-sm font-medium">Senha inicial</label>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        )}

        {!isEdit && roles && (
          <div className="space-y-1">
            <label className="block text-sm font-medium">Papel inicial</label>
            <select
              value={roleId}
              onChange={(e) => setRoleId(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm"
            >
              <option value="">Selecionar papel...</option>
              {roles.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={isPending}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 transition"
          >
            {isPending ? "Salvando..." : isEdit ? "Salvar alterações" : "Criar usuário"}
          </button>
          <button
            type="button"
            onClick={() => void navigate(isEdit ? `/users/${user!.id}` : "/users")}
            className="px-4 py-2 border rounded hover:bg-gray-50 transition"
          >
            Cancelar
          </button>
        </div>
      </form>
    </div>
  );
}
