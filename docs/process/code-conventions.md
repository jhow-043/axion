# Convenções de Código

Aplicam-se a todo código do projeto, gerado por humanos ou por IA.
Leia também `docs/constitution.md` para os invariantes invioláveis.

---

## Backend (Python/FastAPI)

### Estrutura de módulo

Ver `docs/architecture/folder-structure.md` para a estrutura completa.

Resumo das responsabilidades:

```
router.py    → validação de entrada (Pydantic), chama service, retorna schema
service.py   → regras de negócio, recebe repositório por DI
repository.py → queries, herda BaseRepository (tenant automático)
models.py    → ORM, herda TenantMixin, sem lógica
schemas.py   → Pydantic v2, request/response separados
```

**Proibições:**
- `router.py` não importa modelos ORM nem `AsyncSession`.
- `service.py` não importa `AsyncSession` diretamente.
- Queries SQLAlchemy diretas fora do `repository.py` (violação de INV-01).

### Pydantic v2

```python
# Schemas request/response separados — nunca o mesmo para os dois
class TicketCreate(BaseModel):
    model_config = ConfigDict(strict=True)
    title: str = Field(min_length=3, max_length=200)
    type: Literal["industrial", "predial"]

class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    status_code: str  # campo calculado, não ORM direto
```

### SQLAlchemy 2.0 async

```python
# Sempre async — sem operações síncronas de banco
async def get_tickets(self, filters: TicketFilters) -> list[Ticket]:
    stmt = (
        select(Ticket)
        .where(Ticket.status_id == filters.status_id)  # tenant_id já no BaseRepository
        .order_by(Ticket.created_at.desc())
    )
    result = await self.session.execute(stmt)
    return list(result.scalars().all())
```

### FastAPI

```python
# require_permission como dependência — não como lógica inline
@router.post("/tickets/{id}/transition")
async def transition_ticket(
    id: UUID,
    body: TicketTransitionRequest,
    service: TicketService = Depends(get_ticket_service),
    _: None = Depends(require_permission("ticket:transition")),
) -> TicketResponse:
    return await service.transition(id, body)
```

### Exceções

```python
# Hierarquia de exceções própria — nunca HTTPException diretamente no service
class TicketNotFoundError(NotFoundError): ...
class InvalidTransitionError(BusinessRuleError): ...

# O handler global em core/exceptions.py converte para o envelope padrão
```

### Comentários

- Apenas para o **porquê** — nunca para o que o código faz.
- Cite o ADR ou regra de negócio quando necessário.
- Errado: `# Verifica se o chamado existe`
- Certo: `# 404 em vez de 403 para não revelar existência cross-tenant (ADR-0002)`

---

## Frontend (React/TypeScript)

### Tipos

```typescript
// Espelham os contratos da API — sem any, sem cast forçado
interface Ticket {
  id: string;        // UUID como string no frontend
  title: string;
  status: TicketStatus;
  priority: Priority;
  requester: UserSummary;
  assignee: UserSummary | null;
  created_at: string; // ISO 8601 UTC — formatar na exibição
}

// Enums como const objects — melhor tree-shaking que TypeScript enums
export const TicketStatus = {
  NEW: "new",
  IN_PROGRESS: "in_progress",
  PENDING: "pending",
  RESOLVED: "resolved",
  CLOSED: "closed",
} as const;
export type TicketStatus = typeof TicketStatus[keyof typeof TicketStatus];
```

### TanStack Query

```typescript
// Chaves de query consistentes — array com hierarquia
const ticketKeys = {
  all: ["tickets"] as const,
  list: (filters: TicketFilters) => [...ticketKeys.all, "list", filters] as const,
  detail: (id: string) => [...ticketKeys.all, "detail", id] as const,
};

// Mutation com invalidação automática
const transitionMutation = useMutation({
  mutationFn: (data: TransitionRequest) => transitionTicket(id, data),
  onSuccess: () => queryClient.invalidateQueries({ queryKey: ticketKeys.detail(id) }),
});
```

### Componentes

```typescript
// Componentes menores com responsabilidade única
// Props tipadas, sem prop drilling excessivo
interface TicketStatusBadgeProps {
  status: TicketStatus;
  slaBreached?: boolean;
}

export function TicketStatusBadge({ status, slaBreached }: TicketStatusBadgeProps) {
  // ...
}
```

### Estados de UI obrigatórios

Toda listagem/detalhe deve tratar:
```typescript
if (isLoading) return <Skeleton />;
if (error) return <ErrorState message={error.message} />;
if (!data || data.items.length === 0) return <EmptyState />;
return <TicketList items={data.items} />;
```

### Datas

```typescript
// Sempre converter UTC → local na exibição, nunca armazenar local
import { formatDate, formatDateTime } from "@/utils/dates";

<span>{formatDate(ticket.created_at)}</span>  // "01/06/2026"
<span>{formatDateTime(ticket.assigned_at)}</span>  // "01/06/2026 14:30"
```

---

## Convenções gerais

### Nomenclatura

| Contexto | Convenção | Exemplo |
|----------|-----------|---------|
| Arquivos Python | `snake_case` | `ticket_service.py` |
| Classes Python | `PascalCase` | `TicketService` |
| Funções/variáveis Python | `snake_case` | `calculate_resolution_due_at` |
| Arquivos TypeScript | `PascalCase` componentes, `camelCase` utils | `TicketList.tsx`, `formatDate.ts` |
| Variáveis TypeScript | `camelCase` | `ticketId`, `isLoading` |
| Tipos/Interfaces TypeScript | `PascalCase` | `TicketResponse` |
| Tabelas SQL | `snake_case` plural | `ticket_observers` |
| Colunas SQL | `snake_case` | `assignee_id` |

### Tamanho de arquivo

- Funções Python: < 30 linhas por função (alerta acima de 50).
- Componentes React: < 150 linhas (alerta acima de 200 — extrair sub-componentes).
- Arquivos de módulo: < 300 linhas (alerta acima de 500 — extrair).

### Imports

Python: organize na ordem `stdlib → third-party → local`, separados por linha em branco.
TypeScript: `react → third-party → @/shared → features → local`, separados por linha.

---

## Geração de código por IA

Regras adicionais para código gerado por agentes:

1. **Consulte o Context7 MCP** antes de usar API de FastAPI, SQLAlchemy, Pydantic, TanStack ou shadcn. Elimina código obsoleto ou alucinado.
2. **Uma operação por função** — não gere funções com múltiplos `if/else` de responsabilidades diferentes.
3. **Sem comentários de tarefas** (`# TODO`, `# FIXME`) — resolva na hora ou crie uma issue.
4. **Sem código de debug** (`print()`, `console.log()`, `breakpoint()`).
5. **Sem imports não utilizados** — ruff remove automaticamente, mas não gere-os.
6. **Sem backwards-compat** — se algo foi removido, remova. Sem aliases ou re-exports de conveniência.
7. **Teste junto** — nunca gere código de implementação sem os testes correspondentes no mesmo PR.
