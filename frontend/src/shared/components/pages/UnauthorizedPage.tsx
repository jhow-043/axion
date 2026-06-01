import { Link } from "react-router";
import { Button } from "@/shared/components/ui/button";

export function UnauthorizedPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 text-center">
      <h1 className="text-6xl font-bold text-muted-foreground">403</h1>
      <h2 className="text-xl font-semibold">Sem permissão</h2>
      <p className="text-muted-foreground">
        Você não tem permissão para acessar esta página.
      </p>
      <Button asChild variant="outline">
        <Link to="/">Voltar ao início</Link>
      </Button>
    </div>
  );
}
