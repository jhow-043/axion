import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/shared/api/client";
import type {
  PermissionResponse,
  RoleAssignRequest,
  RoleResponse,
  UserCreate,
  UserFilters,
  UserListResponse,
  UserResponse,
  UserUpdate,
} from "./types";

const userKeys = {
  all: ["users"] as const,
  list: (filters: UserFilters) => [...userKeys.all, "list", filters] as const,
  detail: (id: string) => [...userKeys.all, "detail", id] as const,
  roles: (id: string) => [...userKeys.all, "roles", id] as const,
};

const roleKeys = {
  all: ["roles"] as const,
};

const permissionKeys = {
  all: ["permissions"] as const,
};

export function useUsers(filters: UserFilters = {}) {
  return useQuery({
    queryKey: userKeys.list(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.page) params.set("page", String(filters.page));
      if (filters.page_size) params.set("page_size", String(filters.page_size));
      if (filters.name) params.set("name", filters.name);
      if (filters.email) params.set("email", filters.email);
      if (filters.is_active !== undefined) params.set("is_active", String(filters.is_active));
      if (filters.role_code) params.set("role_code", filters.role_code);
      const { data } = await apiClient.get<UserListResponse>(`/users?${params.toString()}`);
      return data;
    },
  });
}

export function useUser(id: string) {
  return useQuery({
    queryKey: userKeys.detail(id),
    queryFn: async () => {
      const { data } = await apiClient.get<UserResponse>(`/users/${id}`);
      return data;
    },
    enabled: Boolean(id),
  });
}

export function useCreateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: UserCreate) => {
      const { data } = await apiClient.post<UserResponse>("/users", payload);
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: userKeys.all });
    },
  });
}

export function useUpdateUser(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: UserUpdate) => {
      const { data } = await apiClient.patch<UserResponse>(`/users/${id}`, payload);
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: userKeys.detail(id) });
      void qc.invalidateQueries({ queryKey: userKeys.all });
    },
  });
}

export function useActivateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post<UserResponse>(`/users/${id}/activate`);
      return data;
    },
    onSuccess: (_data, id) => {
      void qc.invalidateQueries({ queryKey: userKeys.detail(id) });
      void qc.invalidateQueries({ queryKey: userKeys.all });
    },
  });
}

export function useDeactivateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post<UserResponse>(`/users/${id}/deactivate`);
      return data;
    },
    onSuccess: (_data, id) => {
      void qc.invalidateQueries({ queryKey: userKeys.detail(id) });
      void qc.invalidateQueries({ queryKey: userKeys.all });
    },
  });
}

export function useUserRoles(userId: string) {
  return useQuery({
    queryKey: userKeys.roles(userId),
    queryFn: async () => {
      const { data } = await apiClient.get<RoleResponse[]>(`/users/${userId}/roles`);
      return data;
    },
    enabled: Boolean(userId),
  });
}

export function useAssignRole(userId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: RoleAssignRequest) => {
      const { data } = await apiClient.post<RoleResponse[]>(`/users/${userId}/roles`, payload);
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: userKeys.roles(userId) });
      void qc.invalidateQueries({ queryKey: userKeys.detail(userId) });
    },
  });
}

export function useRemoveRole(userId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (roleId: string) => {
      await apiClient.delete(`/users/${userId}/roles/${roleId}`);
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: userKeys.roles(userId) });
      void qc.invalidateQueries({ queryKey: userKeys.detail(userId) });
    },
  });
}

export function useRoles() {
  return useQuery({
    queryKey: roleKeys.all,
    queryFn: async () => {
      const { data } = await apiClient.get<RoleResponse[]>("/roles");
      return data;
    },
  });
}

export function usePermissions() {
  return useQuery({
    queryKey: permissionKeys.all,
    queryFn: async () => {
      const { data } = await apiClient.get<PermissionResponse[]>("/permissions");
      return data;
    },
  });
}
