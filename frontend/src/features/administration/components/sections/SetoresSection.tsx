import { RedirectSection } from "./RedirectSection";

export function SetoresSection() {
  return (
    <RedirectSection
      title="Setores e Locais"
      description="Gerencie setores e locais prediais da empresa."
      links={[
        { label: "Setores", to: "/setores" },
        { label: "Locais", to: "/locais" },
      ]}
    />
  );
}
