import { RedirectSection } from "./RedirectSection";

export function UsersSection() {
  return (
    <RedirectSection
      title="Usuários"
      description="Gerencie os usuários do sistema, crie novos e atribua papéis."
      links={[
        { label: "Listar usuários", to: "/users" },
        { label: "Novo usuário", to: "/users/new" },
      ]}
    />
  );
}
