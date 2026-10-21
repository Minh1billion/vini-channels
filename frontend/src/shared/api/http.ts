export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: unknown;

  constructor(status: number, code: string, message: string, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

const BASE = '/api/v1';
const SILENT_401 = new Set(['/auth/login', '/me']);

type Query = Record<string, string | number | boolean | null | undefined>;

let unauthorizedHandler: (() => void) | null = null;

export function setUnauthorizedHandler(handler: (() => void) | null) {
  unauthorizedHandler = handler;
}

function buildUrl(path: string, query?: Query) {
  if (!query) return `${BASE}${path}`;
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null || value === '') continue;
    params.set(key, String(value));
  }
  const suffix = params.toString();
  return suffix ? `${BASE}${path}?${suffix}` : `${BASE}${path}`;
}

async function send<T>(
  method: string,
  path: string,
  body?: unknown,
  query?: Query,
): Promise<{ payload: T; response: Response }> {
  let response: Response;
  try {
    response = await fetch(buildUrl(path, query), {
      method,
      credentials: 'same-origin',
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, 'network_error', 'Không kết nối được máy chủ');
  }

  if (response.status === 204) return { payload: undefined as T, response };

  const payload: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    const error = (payload ?? {}) as { code?: string; message?: string; details?: unknown };
    if (response.status === 401 && !SILENT_401.has(path)) unauthorizedHandler?.();
    throw new ApiError(
      response.status,
      error.code ?? 'unknown_error',
      error.message ?? 'Có lỗi xảy ra, vui lòng thử lại',
      error.details,
    );
  }

  return { payload: payload as T, response };
}

async function request<T>(method: string, path: string, body?: unknown, query?: Query): Promise<T> {
  const { payload } = await send<T>(method, path, body, query);
  return payload;
}

export interface Page<T> {
  items: T[];
  total: number;
}

async function getPage<T>(path: string, query?: Query): Promise<Page<T>> {
  const { payload, response } = await send<T[]>('GET', path, undefined, query);
  const header = Number(response.headers.get('X-Total-Count'));
  return { items: payload, total: Number.isFinite(header) && header > 0 ? header : payload.length };
}

export const http = {
  get: <T>(path: string, query?: Query) => request<T>('GET', path, undefined, query),
  getPage,
  post: <T>(path: string, body?: unknown) => request<T>('POST', path, body ?? {}),
  put: <T>(path: string, body?: unknown) => request<T>('PUT', path, body ?? {}),
  patch: <T>(path: string, body?: unknown) => request<T>('PATCH', path, body ?? {}),
  delete: <T>(path: string) => request<T>('DELETE', path),
};
