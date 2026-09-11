// Обработка на бэкенде асинхронная: статус меняется через секунды после загрузки.
// Пока есть файлы «в работе», списки опрашиваются с этим интервалом (Г3).
export const POLL_INTERVAL_MS = 3000;

export const PAGE_SIZES = [10, 20, 50, 100] as const;
export const DEFAULT_PAGE_SIZE: (typeof PAGE_SIZES)[number] = 20;
