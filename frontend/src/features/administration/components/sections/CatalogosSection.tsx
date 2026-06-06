import { RedirectSection } from "./RedirectSection";

export function CatalogosSection() {
  return (
    <RedirectSection
      title="Catálogos"
      description="Configure prioridades, status, categorias e motivos de pendência."
      links={[{ label: "Catálogos", to: "/catalogos" }]}
    />
  );
}
