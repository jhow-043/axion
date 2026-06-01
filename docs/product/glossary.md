# Glossário — Linguagem Ubíqua

> Use sempre estes termos — no código, nas specs, nas mensagens de commit, nos comentários.
> Ambiguidade de linguagem gera bugs. Termos em inglês são usados apenas onde são nomes de
> conceitos técnicos consagrados (ex.: `status`, `token`, `payload`).

---

## Domínio principal

**Chamado**
Registro de uma solicitação de manutenção. Pode ser do tipo *industrial* (vinculado a um
equipamento) ou *predial* (vinculado a um local). Sinônimos proibidos: "ticket" no domínio
(use `ticket` apenas no código/banco, "chamado" nos textos).

**Chamado Industrial**
Chamado vinculado obrigatoriamente a um equipamento ativo. Representa falha ou manutenção
em máquina, motor, bomba, etc.

**Chamado Predial**
Chamado vinculado obrigatoriamente a um local (setor/sala/área). Representa problema em
instalação física: elétrica, hidráulica, estrutura, etc.

**Status do Chamado**
Estado atual no workflow. Os códigos (`status.code`) são invariantes de código:
`new` → `in_progress` → `pending` | `resolved` → `closed`.
O rótulo exibido ao usuário é configurável (P07), mas o código não.

**Transição**
Mudança de status do chamado seguindo a máquina de estados. Algumas exigem dados
adicionais (ex.: transição para `pending` exige motivo; para `resolved` exige solução).

**Assumir Chamado**
Ação do técnico que define o `assignee_id` e move o chamado de `new` para `in_progress`.
Inicia o SLA de Resolução e encerra o SLA de Atendimento.

**Pendência**
Estado `pending` onde o técnico aguarda informação ou condição externa.
O SLA de Resolução fica *pausado* enquanto o chamado está pendente.
Requer *Motivo de Pendência* (configurável em P07).

**Solução**
Descrição obrigatória informada pelo técnico ao marcar o chamado como `resolved`.
Registrada na entidade `solutions` e exibida ao solicitante para validação.

**Validação**
Processo em que o solicitante aprova ou rejeita a solução após o chamado ser marcado
como `resolved`. Aprovação → `closed`. Rejeição → volta para `in_progress`.

**Auto-fechamento**
Fechamento automático por decurso de prazo de validação sem resposta do solicitante.
Executado por job Celery (P13).

**SLA (Service Level Agreement)**
Acordo de nível de serviço. Neste sistema há dois SLAs por chamado:
- **SLA de Atendimento:** prazo para o técnico *assumir* o chamado.
- **SLA de Resolução:** prazo para *resolver* o chamado após assumi-lo.

**SLA Pausado**
Condição do SLA de Resolução enquanto o chamado está em `pending`.
O tempo de pausa é acumulado e descontado do prazo de resolução.

**SLA Vencido (breached)**
Status do SLA quando o prazo foi ultrapassado sem atingir o objetivo.

**Política de SLA**
Configuração que define os prazos de atendimento e resolução para uma combinação
de (tipo de chamado × prioridade × equipe). Gerenciada em P12 e configurável em P18.

**Timeline**
Histórico cronológico de eventos de um chamado. Registra todas as ações significativas:
abertura, transições, comentários, atribuições, eventos de SLA. Gerenciada em P10.

**Evento de Timeline**
Registro individual na timeline. Cada ação relevante gera um evento
(ex.: `ticket_assigned`, `status_changed`, `sla_breached`).

**Observador**
Usuário adicionado explicitamente a um chamado que pode comentar e recebe notificações,
mas não pode realizar transições de status.

**Participante**
Qualquer usuário com papel ativo no chamado: solicitante, responsável técnico ou observador.

**Responsável (Assignee)**
Técnico que assumiu o chamado. Definido pela ação de *Assumir*.

**Solicitante (Requester)**
Usuário que abriu o chamado.

---

## Estrutura organizacional

**Tenant**
Empresa/organização que usa a plataforma. Cada tenant tem seus dados completamente isolados.
Identificado por `tenant_id` em todas as entidades de domínio.

**Equipe**
Grupo de técnicos responsável por um tipo de manutenção (ex.: "Elétrica", "Mecânica").
Chamados são direcionados a equipes; técnicos assumem individualmente.

**Setor**
Área organizacional (ex.: "Produção", "Administrativo"). Agrupamento de locais prediais.

**Local**
Espaço físico dentro de um setor (ex.: "Sala 101", "Linha de Produção A").
Usado em chamados prediais.

**Equipamento**
Ativo industrial registrado na plataforma (ex.: "Bomba B-01", "Motor M-12").
Vinculado a um local e a uma equipe. Usado em chamados industriais.

---

## Catálogos configuráveis (P07)

**Prioridade**
Nível de urgência do chamado (ex.: "Crítica", "Alta", "Normal", "Baixa").
Usada como parâmetro nas políticas de SLA.

**Categoria**
Classificação do tipo de problema (ex.: "Elétrica", "Mecânica", "Hidráulica").

**Motivo de Pendência**
Razão para colocar o chamado em pendente (ex.: "Aguardando peça", "Aguardando informação").
Obrigatório ao realizar a transição para `pending`.

---

## Papéis (RBAC)

**Admin**
Acesso total. Gerencia usuários, configurações e todas as funcionalidades.

**Supervisor**
Gerencia equipes, vê todos os chamados do tenant, acessa dashboards gerenciais.

**Técnico**
Assume e executa chamados. Vê chamados da sua equipe.

**Solicitante**
Abre chamados, valida soluções. Vê apenas seus próprios chamados.

---

## Termos técnicos preservados no código

| Termo no código | Significado |
|-----------------|-------------|
| `ticket` | "Chamado" no banco e API |
| `tenant_id` | Identificador do tenant em cada entidade |
| `BaseRepository` | Repositório base com filtro automático de tenant |
| `TenantMixin` | Mixin SQLAlchemy que adiciona `tenant_id` ao modelo |
| `status.code` | Código invariante do status (âncora da state machine) |
| `assignee_id` | ID do técnico responsável pelo chamado |
| `requester_id` | ID do solicitante do chamado |
