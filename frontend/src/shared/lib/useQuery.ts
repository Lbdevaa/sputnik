"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { isAbortError } from "@/shared/api/client";

export type QueryState<T> = {
  data: T | null;
  error: string | null;
  /** Первая загрузка: данных ещё нет. Повторные обновления спиннер не показывают. */
  isLoading: boolean;
  isRefreshing: boolean;
  refetch: () => Promise<void>;
};

/** Интервал опроса в мс; null или 0 — не опрашивать. Функция получает текущие данные. */
export type PollMs<T> = number | null | ((data: T | null) => number | null);

export type QueryOptions<T> = {
  pollMs?: PollMs<T>;
};

/**
 * Запрос с отменой и опросом.
 *
 * Каждый новый вызов отменяет предыдущий через AbortController (Г6): ответ на устаревший
 * запрос не перезапишет свежие данные, а размонтированный компонент не получит setState.
 * Опрос идёт только пока вкладка видима и только если `pollMs` для текущих данных
 * вернул интервал (Г3): так список файлов опрашивается, пока в нём есть файлы «в работе».
 */
export function useQuery<T>(
  fetcher: (signal: AbortSignal) => Promise<T>,
  options: QueryOptions<T> = {},
): QueryState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const controllerRef = useRef<AbortController | null>(null);
  const hasDataRef = useRef(false);

  const run = useCallback(async () => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;

    if (hasDataRef.current) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }

    try {
      const result = await fetcher(controller.signal);
      if (controller.signal.aborted) return;
      hasDataRef.current = true;
      setData(result);
      setError(null);
    } catch (caught) {
      if (isAbortError(caught) || controller.signal.aborted) return;
      setError(caught instanceof Error ? caught.message : "Произошла ошибка");
    } finally {
      if (!controller.signal.aborted) {
        setIsLoading(false);
        setIsRefreshing(false);
      }
    }
  }, [fetcher]);

  useEffect(() => {
    // Загрузка данных при монтировании и при смене запроса — тот самый случай «синхронизации
    // с внешней системой», ради которого эффекты и существуют; правило React Compiler
    // видит внутри setState и ругается на любой запрос из эффекта.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void run();
    return () => controllerRef.current?.abort();
  }, [run]);

  const { pollMs } = options;
  const interval = (typeof pollMs === "function" ? pollMs(data) : pollMs) ?? null;
  useEffect(() => {
    if (!interval) return;
    const timer = setInterval(() => {
      if (document.visibilityState === "visible") {
        void run();
      }
    }, interval);
    return () => clearInterval(timer);
  }, [interval, run]);

  return { data, error, isLoading, isRefreshing, refetch: run };
}
