# Subplano 04 — Usuários

**Specs:** P04 (Usuários e RBAC — parte CRUD)
**Prioridade:** Alto
**Status diagnóstico:** ⏳ Pendente

---

## Escopo da spec

- CRUD usuários por tenant: criar, listar, detalhar, editar, ativar/desativar
- Email único por tenant
- 4 papéis default seeded por tenant: Admin, Supervisor, Técnico, Solicitante
- Atribuição/remoção de papéis (UserRole)
- Proteção: admin não pode remover próprio papel de admin se for o único

---

## Arquivos relevantes

### Backend
- `backend/app/modules/users/router.py`
- `backend/app/modules/users/service.py`
- `backend/app/modules/users/repository.py`
- `backend/app/modules/users/schemas.py`
- `backend/app/modules/users/models.py` (User, Role, Permission, UserRole, RolePermission)
- `backend/app/modules/users/seed.py`

### Frontend
- `frontend/src/features/users/components/UserList.tsx`
- `frontend/src/features/users/components/UserForm.tsx`
- `frontend/src/features/users/components/UserDetail.tsx`
- `frontend/src/features/users/components/RoleAssignment.tsx`
- `frontend/src/features/users/api.ts`

---

## Fluxos a validar

- [ ] Listar usuários: paginação, filtros por nome/email/status/papel funcionam
- [ ] Criar usuário: formulário completo → usuário aparece na lista com papel correto
- [ ] Visualizar detalhe do usuário: dados + papéis atribuídos
- [ ] Editar usuário: alterar nome/email → persistido corretamente
- [ ] Desativar usuário: usuário não consegue mais autenticar
- [ ] Reativar usuário: consegue autenticar novamente
- [ ] Atribuir papel: usuário herda as permissões do papel
- [ ] Remover papel: permissões revogadas
- [ ] Email duplicado no mesmo tenant → erro adequado (não 500)
- [ ] Usuário de outro tenant não aparece na listagem

---

## Problemas catalogados (Fase A)

| EST-ID | Classificação | Descrição | Arquivo:Linha | Reprodução |
|--------|--------------|-----------|---------------|------------|
| — | — | *A preencher* | — | — |

---

## Notas de risco

- Seed de papéis ocorre em dois momentos: no `seed_dev.py` e no provisioning de tenant (P19). Verificar idempotência.
- `require_permission("USER_MANAGE")` deve ser verificado em criar/editar/desativar.
