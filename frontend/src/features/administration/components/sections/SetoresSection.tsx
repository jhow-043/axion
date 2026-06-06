import { RedirectSection } from "./RedirectSection";

export function SetoresSection() {
  return (
    <RedirectSection
      title="Setores e Locais"
      description="Gerencie setores e locais prediais."
      links={[{ label: "Setores e Locais", to: "/setores" }]}
    />
  );
}
