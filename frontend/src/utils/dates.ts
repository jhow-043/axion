const DATE_FORMAT = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  timeZone: "America/Sao_Paulo",
});

const DATETIME_FORMAT = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  timeZone: "America/Sao_Paulo",
});

const RELATIVE_FORMAT = new Intl.RelativeTimeFormat("pt-BR", {
  numeric: "always",
});

export function formatDate(isoUtc: string): string {
  return DATE_FORMAT.format(new Date(isoUtc));
}

export function formatDateTime(isoUtc: string): string {
  return DATETIME_FORMAT.format(new Date(isoUtc));
}

export function formatDistanceToNow(date: Date, now = new Date()): string {
  const diffMs = date.getTime() - now.getTime();
  const absMs = Math.abs(diffMs);
  const minuteMs = 60 * 1000;
  const hourMs = 60 * minuteMs;
  const dayMs = 24 * hourMs;

  if (absMs < hourMs) {
    return RELATIVE_FORMAT.format(Math.round(diffMs / minuteMs), "minute");
  }

  if (absMs < dayMs) {
    return RELATIVE_FORMAT.format(Math.round(diffMs / hourMs), "hour");
  }

  return RELATIVE_FORMAT.format(Math.round(diffMs / dayMs), "day");
}
