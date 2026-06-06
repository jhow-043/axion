import { RedirectSection } from "./RedirectSection";

export function SlaSection() {
  return (
    <RedirectSection
      title="Políticas de SLA"
      description="Configure as políticas de SLA por tipo de chamado e prioridade."
      links={[{ label: "Políticas de SLA", to: "/sla" }]}
    />
  );
}
