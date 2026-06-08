# Subplano 06 — Equipamentos

**Specs:** P08 (Equipamentos)
**Prioridade:** Alto — pré-requisito para chamados industriais
**Status diagnóstico:** ⏳ Pendente

---

## Escopo da spec

- CRUD equipamentos: criar, listar, detalhar, editar, ativar/desativar
- Campos obrigatórios: nome, código (único por tenant), setor, status
- Campos opcionais: fabricante, modelo, número de série, observações
- Página de detalhe com histórico paginado de chamados
- Equipamento inativo não pode ser alvo de novos chamados

---

## Arquivos relevantes

### Backend
- `backend/app/modules/equipments/router.py`
- `backend/app/modules/equipments/service.py`
- `backend/app/modules/equipments/repository.py`
- `backend/app/modules/equipments/models.py`
- `backend/app/modules/equipments/schemas.py`

### Frontend
- `frontend/src/features/equipments/components/EquipmentList.tsx`
- `frontend/src/features/equipments/components/EquipmentForm.tsx`
- `frontend/src/features/equipments/components/EquipmentDetail.tsx`
- `frontend/src/features/equipments/api.ts`
- Rotas: `/equipments`, `/equipments/new`, `/equipments/:id`, `/equipments/:id/edit`

---

## Fluxos a validar

- [ ] Listar equipamentos: busca, filtro por setor, filtro por status, paginação
- [ ] Criar equipamento: todos os campos obrigatórios + opcionais → aparece na lista
- [ ] Visualizar detalhe: dados completos + histórico de chamados do equipamento
- [ ] Editar equipamento: formulário pré-preenchido → alteração persistida
- [ ] Desativar equipamento: não aparece no dropdown de criação de chamado industrial
- [ ] Ativar equipamento: volta a aparecer no dropdown
- [ ] Código duplicado no tenant → erro adequado
- [ ] Setor selecionado pertence ao mesmo tenant (sem vazar opções cross-tenant)
- [ ] Histórico de chamados: paginado, mais recente primeiro
- [ ] Equipamento de outro tenant não visível

---

## Problemas catalogados (Fase A)

| EST-ID | Classificação | Descrição | Arquivo:Linha | Reprodução |
|--------|--------------|-----------|---------------|------------|
| — | — | *A preencher* | — | — |

---

## Notas de risco

- EquipmentDetail precisa carregar tanto o equipamento quanto seu histórico; verificar se as duas queries são eficientes (N+1).
- Botão "Editar" em EquipmentDetail foi sinalizado como potencialmente ausente na exploração estática — confirmar.
