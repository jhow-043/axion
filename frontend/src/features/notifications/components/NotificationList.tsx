import { useNotifications, useMarkRead } from "../api";
import type { Notification } from "../types";

interface NotificationListProps {
  onClose?: () => void;
}

export function NotificationList({ onClose }: NotificationListProps) {
  const { data, isLoading } = useNotifications(null, 1);
  const markRead = useMarkRead();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
        Carregando…
      </div>
    );
  }

  const items = data?.items ?? [];

  if (items.length === 0) {
    return (
      <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
        Nenhuma notificação.
      </div>
    );
  }

  return (
    <ul className="max-h-96 overflow-y-auto divide-y">
      {items.map((n) => (
        <NotificationItem
          key={n.id}
          notification={n}
          onRead={() => {
            if (!n.is_read) void markRead.mutateAsync(n.id);
            onClose?.();
          }}
        />
      ))}
    </ul>
  );
}

function NotificationItem({
  notification: n,
  onRead,
}: {
  notification: Notification;
  onRead: () => void;
}) {
  return (
    <li>
      <button
        onClick={onRead}
        className={`w-full px-4 py-3 text-left transition-colors hover:bg-muted/50 ${
          n.is_read ? "opacity-60" : ""
        }`}
      >
        <div className="flex items-start gap-2">
          {!n.is_read && (
            <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-blue-500" />
          )}
          <div className={!n.is_read ? "" : "pl-4"}>
            <p className="text-sm font-medium leading-tight">{n.title}</p>
            <p className="mt-0.5 text-xs text-muted-foreground leading-snug">
              {n.body}
            </p>
            <p className="mt-1 text-[10px] text-muted-foreground">
              {new Date(n.created_at).toLocaleString("pt-BR")}
            </p>
          </div>
        </div>
      </button>
    </li>
  );
}
