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

export function formatDate(isoUtc: string): string {
  return DATE_FORMAT.format(new Date(isoUtc));
}

export function formatDateTime(isoUtc: string): string {
  return DATETIME_FORMAT.format(new Date(isoUtc));
}
