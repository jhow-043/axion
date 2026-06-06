import { RedirectSection } from "./RedirectSection";

export function TeamsSection() {
  return (
    <RedirectSection
      title="Equipes"
      description="Gerencie as equipes de manutenção e seus membros."
      links={[
        { label: "Listar equipes", to: "/teams" },
        { label: "Nova equipe", to: "/teams/new" },
      ]}
    />
  );
}
