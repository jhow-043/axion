---
id: P02
slug: fundacao-frontend
status: done
version: 1.0.0
owner: jhowworks
depends_on: [P00]
satisfies: [RNF-A11Y-001, RNF-A11Y-002, RNF-I18N-001, RNF-I18N-003]
adrs: []
branch: feature/002-fundacao-frontend
last_updated: 2026-06-01
---

# P02 — Fundação do Frontend

## Objetivo

Estabelecer o esqueleto do SPA React com providers, roteamento, client de API tipado, design system base e cliente WebSocket, de forma que todas as features subsequentes possam ser desenvolvidas de forma consistente e independente.

## Escopo

- Projeto Vite + React + TypeScript configurado.
- React Router: configuração base com suporte a rotas públicas, privadas (autenticadas) e por papel (`role guard`).
- Provider de autenticação (`AuthProvider`): estado de sessão, funções de login/logout/refresh.
- TanStack Query: configuração global (`QueryClient`) com tratamento padrão de erros e retry.
- Client HTTP (`src/shared/api/client.ts`): instância Axios com interceptors de autenticação (Bearer token), refresh transparente em 401, e tratamento de erro centralizado (mapeia código HTTP para mensagem amigável).
- Design system base: Tailwind CSS configurado + shadcn/ui instalado com tema, tipografia e cores padrão.
- Layout shell: estrutura de página com sidebar (navegação principal), topbar (perfil/notificações), e área de conteúdo — responsivo.
- Cliente WebSocket base (`src/shared/ws/client.ts`): conexão, reconexão automática, subscrição a canais.
- Páginas base: Login (só estrutura, integração em P03), 404, erro genérico.
- Tipos compartilhados iniciais (`src/types/`): envelopes de resposta da API, paginação.
- Configuração de variáveis de ambiente (`.env.example`).
- Setup de testes: Vitest + Testing Library.

## Fora do Escopo

- Telas de domínio (cada feature traz as suas).
- Lógica de autenticação completa (integração real em P03).
- Componentes de domínio (equipamentos, chamados, etc.).
- WebSocket de notificações (integração real em P14).

## Dependências

- **P00** (Fundação Backend) — para ter um endpoint (`/api/v1/ping`) ao qual o client pode se conectar e validar a configuração.
- **P03** (Autenticação) — integração do fluxo de login real; a fundação cria a estrutura, P03 completa.

## Entidades Impactadas

Nenhuma entidade de banco. Frontend puro.

## APIs Necessárias

| Método | Rota | Uso |
|--------|------|-----|
| GET | `/api/v1/ping` | Verificar conexão com o backend (configuração do client) |
| POST | `/api/v1/auth/login` | (estrutura criada aqui; implementação completa em P03) |
| POST | `/api/v1/auth/refresh` | (idem) |

## Telas Necessárias

| Tela | Descrição |
|------|-----------|
| Layout Shell | Sidebar + Topbar + área de conteúdo responsiva |
| Página de Login | Formulário (email + senha); integração real em P03 |
| Página 404 | Rota não encontrada |
| Página de Erro | Erro genérico (ex.: servidor indisponível) |

## Regras de Negócio

- **Rotas privadas:** redirecionar para `/login` se não houver sessão válida. Após login bem-sucedido, redirecionar para a rota solicitada originalmente.
- **Refresh transparente:** interceptor do Axios detecta `401`, tenta o refresh silenciosamente, repete a requisição original. Se o refresh falhar, desloga o usuário.
- **Armazenamento do token:** `access_token` em memória (não em localStorage); `refresh_token` em cookie `httpOnly` (quando possível) ou localStorage com ciência do risco — decisão a documentar claramente.
- **Role guard:** componente `<RequireRole roles={["admin","supervisor"]}>` que redireciona ou exibe "sem permissão" se o papel do usuário não estiver na lista.
- **WebSocket:** reconexão com backoff exponencial; não bloqueia a UI se a conexão falhar.

## Critérios de Aceite

- [ ] `npm run dev` sobe o SPA sem erros.
- [ ] `npm run build` gera bundle sem erros de tipo.
- [ ] Navegar para rota privada sem sessão → redireciona para `/login`.
- [ ] Client Axios envia `Authorization: Bearer <token>` em requisições autenticadas.
- [ ] Interceptor de refresh: token expirado → tenta refresh → repete requisição → usuário não percebe interrupção.
- [ ] Refresh falho → logout automático → redirect para `/login`.
- [ ] Layout shell renderiza sidebar e topbar sem erros.
- [ ] Página 404 exibida para rota desconhecida.
- [ ] WebSocket client conecta, desconecta e reconecta sem erros de console.
- [ ] `npm run test` roda sem erros (pelo menos testes de setup).
- [ ] Componentes do design system (Button, Input, Card) renderizam com o tema correto.

## Estratégia de Testes

### Testes Unitários

- `AuthProvider`: estado de sessão (logado/deslogado), funções de login/logout chamam os endpoints corretos.
- Interceptor de refresh: sequência de chamadas (request 401 → refresh → retry original).
- `RequireRole`: redireciona quando papel insuficiente; renderiza filhos quando papel válido.
- Utilitários de tipo/paginação: serialização/deserialização de envelopes da API.

### Testes de Integração

- Client HTTP com servidor mock (MSW): login, refresh e logout completos.
- Rota privada sem token → redirect para `/login` → login → redirect para rota original.
- WebSocket: conexão, recebimento de mensagem, reconexão após queda.

### Testes E2E

- Usuário acessa rota privada → vê a tela de login → faz login → vê o layout shell.
- Usuário com papel insuficiente → vê a tela de "sem permissão".
- Sessão expirada durante o uso → refresh silencioso → continua navegando.

## Riscos Técnicos

- **Armazenamento seguro do refresh token:** `httpOnly` cookie ideal mas requer CORS configurado corretamente no backend (origin, credentials). Definir estratégia clara antes de implementar.
- **Reconexão do WebSocket:** gerenciar estado de conexão sem causar re-renders desnecessários.
- **Tipagem do client HTTP:** tipos da API devem estar alinhados com os schemas Pydantic do backend (API-first); divergência causa bugs silenciosos.
- **Tree shaking do shadcn/ui:** importações erradas podem inflar o bundle.

## Complexidade

**Média** — sem regra de negócio, mas a lógica de auth/refresh e o setup de WebSocket são críticos para o restante do sistema.

## Prioridade

**Crítica** — bloqueador de todas as features de frontend.

## Branch

`feature/002-fundacao-frontend`
