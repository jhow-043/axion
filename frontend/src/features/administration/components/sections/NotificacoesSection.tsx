import { RedirectSection } from "./RedirectSection";

export function NotificacoesSection() {
  return (
    <RedirectSection
      title="Notificações"
      description="Configure as preferências de notificação do seu usuário."
      links={[{ label: "Preferências de notificação", to: "/notifications/preferences" }]}
    />
  );
}
