import { useState, useRef, useEffect } from "react";
import { Bell } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { useNotifications, useMarkAllRead } from "../api";
import { useNotificationSocket } from "../hooks/useNotificationSocket";
import { NotificationList } from "./NotificationList";

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const { data } = useNotifications(null, 1);
  const markAllRead = useMarkAllRead();
  const unreadCount = data?.unread_count ?? 0;

  useNotificationSocket();

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <Button
        variant="ghost"
        size="icon"
        aria-label={`Notificações${unreadCount > 0 ? ` (${unreadCount} não lidas)` : ""}`}
        onClick={() => setOpen((v) => !v)}
        className="relative"
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </Button>

      {open && (
        <div className="absolute right-0 top-full z-50 mt-1 w-80 rounded-lg border bg-background shadow-lg">
          <div className="flex items-center justify-between border-b px-4 py-2">
            <span className="text-sm font-semibold">Notificações</span>
            {unreadCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="h-auto py-0 text-xs text-muted-foreground hover:text-foreground"
                onClick={() => void markAllRead.mutateAsync()}
                disabled={markAllRead.isPending}
              >
                Marcar todas como lidas
              </Button>
            )}
          </div>
          <NotificationList onClose={() => setOpen(false)} />
        </div>
      )}
    </div>
  );
}
