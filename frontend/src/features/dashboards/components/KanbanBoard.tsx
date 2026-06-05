import { useState } from "react";
import {
  DndContext,
  DragOverlay,
  useDraggable,
  useDroppable,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { useQueryClient } from "@tanstack/react-query";
import { AlertCircle } from "lucide-react";
import { Badge } from "@/shared/components/ui/badge";
import { cn } from "@/utils/cn";
import { dashboardKeys, transitionTicket, useBoardData } from "../api";
import type { BoardColumn, BoardTicketItem } from "../types";

// ── Ticket card ───────────────────────────────────────────────────────────────

interface CardProps {
  ticket: BoardTicketItem;
  isDragging?: boolean;
}

function TicketCard({ ticket, isDragging }: CardProps) {
  const slaColor =
    ticket.sla_status === "breached"
      ? "border-destructive"
      : ticket.sla_status === "running"
        ? "border-yellow-400"
        : "";

  return (
    <div
      className={cn(
        "rounded-md border bg-card p-3 shadow-sm",
        isDragging ? "opacity-50" : "cursor-grab hover:shadow-md",
        slaColor,
      )}
    >
      <p className="line-clamp-2 text-sm font-medium">{ticket.title}</p>
      <div className="mt-2 flex items-center justify-between gap-2">
        <Badge variant={ticket.priority === "critical" ? "destructive" : "outline"} className="text-xs">
          {ticket.priority}
        </Badge>
        {ticket.assignee && (
          <span className="truncate text-xs text-muted-foreground">
            {ticket.assignee}
          </span>
        )}
      </div>
    </div>
  );
}

// ── Draggable wrapper ─────────────────────────────────────────────────────────

function DraggableCard({ ticket }: { ticket: BoardTicketItem }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } =
    useDraggable({ id: ticket.id, data: { ticket } });

  const style = transform
    ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)` }
    : undefined;

  return (
    <div ref={setNodeRef} style={style} {...listeners} {...attributes}>
      <TicketCard ticket={ticket} isDragging={isDragging} />
    </div>
  );
}

// ── Droppable column ──────────────────────────────────────────────────────────

function KanbanColumn({ column }: { column: BoardColumn }) {
  const { setNodeRef, isOver } = useDroppable({ id: column.status_code });

  return (
    <div className="flex w-72 shrink-0 flex-col">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold">{column.status_name}</h3>
        <Badge variant="secondary" className="text-xs">
          {column.tickets.length}
        </Badge>
      </div>
      <div
        ref={setNodeRef}
        className={cn(
          "min-h-24 flex-1 rounded-lg border-2 border-dashed p-2 transition-colors",
          isOver ? "border-primary bg-primary/5" : "border-border",
        )}
      >
        <div className="space-y-2">
          {column.tickets.map((ticket) => (
            <DraggableCard key={ticket.id} ticket={ticket} />
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Board container ───────────────────────────────────────────────────────────

export function KanbanBoard() {
  const { data, isLoading, error } = useBoardData();
  const queryClient = useQueryClient();
  const [activeTicket, setActiveTicket] = useState<BoardTicketItem | null>(
    null,
  );
  const [transitionError, setTransitionError] = useState<string | null>(null);

  if (isLoading)
    return (
      <div className="p-6 text-muted-foreground">Carregando Kanban...</div>
    );
  if (error || !data)
    return (
      <div className="p-6 text-destructive">
        Erro ao carregar o Kanban. Tente novamente.
      </div>
    );

  function handleDragStart(event: DragStartEvent) {
    const ticket = event.active.data.current?.ticket as BoardTicketItem;
    setActiveTicket(ticket ?? null);
    setTransitionError(null);
  }

  async function handleDragEnd(event: DragEndEvent) {
    setActiveTicket(null);
    const { active, over } = event;
    if (!over) return;

    const ticketId = active.id as string;
    const targetStatusCode = over.id as string;

    const sourceColumn = data.columns.find((c) =>
      c.tickets.some((t) => t.id === ticketId),
    );
    if (!sourceColumn || sourceColumn.status_code === targetStatusCode) return;

    try {
      await transitionTicket(ticketId, targetStatusCode);
      await queryClient.invalidateQueries({
        queryKey: dashboardKeys.board({}),
      });
    } catch {
      setTransitionError(
        `Transição de "${sourceColumn.status_name}" para "${targetStatusCode}" inválida.`,
      );
    }
  }

  return (
    <div className="p-6">
      <h1 className="mb-4 text-2xl font-bold">Kanban Operacional</h1>

      {transitionError && (
        <div className="mb-4 flex items-center gap-2 rounded-md border border-destructive bg-destructive/10 p-3 text-sm text-destructive">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {transitionError}
        </div>
      )}

      <DndContext onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
        <div className="flex gap-4 overflow-x-auto pb-4">
          {data.columns.map((column) => (
            <KanbanColumn key={column.status_code} column={column} />
          ))}
        </div>

        <DragOverlay>
          {activeTicket && (
            <div className="w-72 rotate-1 shadow-lg">
              <TicketCard ticket={activeTicket} />
            </div>
          )}
        </DragOverlay>
      </DndContext>
    </div>
  );
}
