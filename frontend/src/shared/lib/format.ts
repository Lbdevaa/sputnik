// Один форматтер на модуль, а не на ячейку таблицы (Г7): создание Intl.DateTimeFormat —
// самая дорогая операция в рендере строки.
const dateFormatter = new Intl.DateTimeFormat("ru-RU", {
  dateStyle: "short",
  timeStyle: "short",
});

export function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : dateFormatter.format(date);
}

const UNITS = ["B", "KB", "MB", "GB"] as const;

export function formatSize(size: number): string {
  if (!Number.isFinite(size) || size < 0) {
    return "—";
  }
  let value = size;
  let unit = 0;
  while (value >= 1024 && unit < UNITS.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return unit === 0 ? `${value} ${UNITS[unit]}` : `${value.toFixed(1)} ${UNITS[unit]}`;
}
