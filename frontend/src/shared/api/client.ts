import { API_URL } from "@/shared/config/env";

/**
 * Ошибка HTTP-уровня: код и текст из `detail`, если бэкенд его прислал.
 * Компоненты показывают `message` как есть, решения по коду принимают по `status`.
 */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: BodyInit;
  json?: unknown;
  signal?: AbortSignal;
};

const FALLBACK_MESSAGES: Record<number, string> = {
  400: "Некорректный запрос",
  404: "Не найдено",
  413: "Файл слишком большой",
  422: "Данные не прошли проверку",
};

async function readDetail(response: Response): Promise<string | null> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
    if (Array.isArray(payload.detail)) {
      // Ошибка валидации FastAPI: массив { loc, msg }.
      const first = payload.detail[0] as { msg?: string } | undefined;
      return first?.msg ?? null;
    }
  } catch {
    // тело не JSON — покажем запасной текст по коду
  }
  return null;
}

export function apiUrl(path: string): string {
  return `${API_URL}${path}`;
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: HeadersInit = {};
  let body = options.body;
  if (options.json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(options.json);
  }

  let response: Response;
  try {
    response = await fetch(apiUrl(path), {
      method: options.method ?? "GET",
      headers,
      body,
      signal: options.signal,
      cache: "no-store",
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    throw new ApiError(0, "Сервер недоступен");
  }

  if (!response.ok) {
    const detail = await readDetail(response);
    throw new ApiError(
      response.status,
      detail ?? FALLBACK_MESSAGES[response.status] ?? `Ошибка сервера (${response.status})`,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}
