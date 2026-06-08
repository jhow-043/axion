# Subplano 10 — Menus e Navegação

**Specs:** P02 (Fundação do Frontend)
**Prioridade:** Médio
**Status diagnóstico:** ⏳ Pendente

---

## Escopo da spec

- Layout shell: sidebar, topbar, área de conteúdo
- React Router com RequireAuth guard
- Guardas de permissão por componente (`hasPermission`)
- Página de Login, 404, erro genérico
- Redirecionamento por papel ao acessar `/dashboard`
- Menu lateral com itens por permissão

---

## Arquivos relevantes

- `frontend/src/app/router.tsx`
- `frontend/src/app/providers/AuthProvider.tsx`
- `frontend/src/shared/components/layout/Sidebar.tsx`
- `frontend/src/shared/components/layout/AppShell.tsx`
- `frontend/src/shared/components/layout/Topbar.tsx` (se existir)
- `frontend/src/pages/` (Login, 404, Error, etc.)

---

## Fluxos a validar

- [ ] Usuário não autenticado → redirecionado para /login
- [ ] Login bem-sucedido → redirecionado para dashboard correto por papel
- [ ] Sidebar exibe apenas itens com permissão do usuário logado
- [ ] Técnico: não vê item "Administração" nem "Plataforma"
- [ ] Admin: vê "Administração"; não vê "Plataforma"
- [ ] SaaS Admin: vê "Plataforma"
- [ ] Acesso direto a rota sem permissão → comportamento adequado (não 500, não tela em branco)
- [ ] Rota inexistente → página 404
- [ ] Logout → redirecionado para /login; sessão limpa
- [ ] Refresh da página: sessão restaurada automaticamente (AuthProvider)
- [ ] Token expirado durante uso: refresh transparente, usuário não percebe

---

## Problemas catalogados (Fase A)

| EST-ID | Classificação | Descrição | Arquivo:Linha | Reprodução |
|--------|--------------|-----------|---------------|------------|
| EST-FE-003 | Alto | Lint frontend nao executa: ESLint 9 exige `eslint.config.*`, mas o projeto nao possui flat config | `frontend/package.json` | `cd frontend && npm run lint` |
| — | — | *A preencher* | — | — |

---

## Notas de risco

- **Guardas de rota ausentes em nível de router**: todas as proteções são por componente. Se a API retornar 403, a tela pode ficar em branco ou exibir erro não tratado.
- Verificar comportamento de `DashboardRedirect` para cada papel.
- `/catalogos` tem redirect para `/administracao/catalogos` — verificar se funciona.
