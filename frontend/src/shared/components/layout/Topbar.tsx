import { Menu, LogOut, User } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { useAuth } from "@/shared/hooks/useAuth";
import { NotificationBell } from "@/features/notifications/components/NotificationBell";

interface TopbarProps {
  onMenuClick: () => void;
}

export function Topbar({ onMenuClick }: TopbarProps) {
  const { session, logout } = useAuth();

  return (
    <header className="flex h-14 items-center justify-between border-b bg-background px-4">
      <Button variant="ghost" size="icon" onClick={onMenuClick} aria-label="Alternar menu">
        <Menu className="h-5 w-5" />
      </Button>

      <div className="flex items-center gap-3">
        <NotificationBell />
        <div className="flex items-center gap-2 text-sm">
          <User className="h-4 w-4 text-muted-foreground" />
          <span>{session?.name ?? "—"}</span>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => void logout()}
          aria-label="Sair"
          title="Sair"
        >
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
}
