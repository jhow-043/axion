import { useRouteError, isRouteErrorResponse, Link } from "react-router";
import { Button } from "@/shared/components/ui/button";

export function ErrorPage() {
  const error = useRouteError();

  const message = isRouteErrorResponse(error)
    ? error.data?.message ?? error.statusText
    : error instanceof Error
      ? error.message
      : "Ocorreu um erro inesperado.";

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 text-center">
      <h1 className="text-4xl font-bold text-destructive">Algo deu errado</h1>
      <p className="max-w-md text-muted-foreground">{message}</p>
      <Button asChild variant="outline">
        <Link to="/">Voltar ao início</Link>
      </Button>
    </div>
  );
}
