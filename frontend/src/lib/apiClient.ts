export class ApiError extends Error {
  status: number
  payload: unknown

  constructor(message: string, status: number, payload: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

export type ApiEnvelope<T> = {
  success: boolean
  data: T
}

function defaultBaseUrl() {
  const env = import.meta.env as unknown as { VITE_API_BASE_URL?: string }
  return env.VITE_API_BASE_URL ?? '/api'
}

function buildUrl(path: string, baseUrl: string) {
  if (/^https?:\/\//i.test(path)) return path

  const normalizedBase = baseUrl.replace(/\/$/, '')
  if (path.startsWith(normalizedBase)) return path

  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${normalizedBase}${normalizedPath}`
}

function isFormData(value: unknown): value is FormData {
  return typeof FormData !== 'undefined' && value instanceof FormData
}

function tryParseJson(text: string) {
  try {
    return JSON.parse(text) as unknown
  } catch {
    return undefined
  }
}

export type ErrorMessage = {
  message: string
  code: string
}

export type Payload = {
  success: boolean
  data?: unknown
  error?: ErrorMessage
  
}


function coerceErrorMessage(payload: Payload | null, fallback: string) {
  if (!payload || typeof payload !== 'object') return fallback
  console.log("payload", payload)
  if (payload.error) return payload.error.message
  const maybeMessage =
    (payload as { message?: unknown; detail?: unknown; msg?: unknown; error?: unknown }).message ??
    (payload as { detail?: unknown }).detail ??
    (payload as { msg?: unknown }).msg ??
    (payload as { error?: unknown }).error
  console.log('maybeMessage', maybeMessage)
  if (typeof maybeMessage === 'string' && maybeMessage.trim()) return maybeMessage

  return fallback
}

function isEnvelope(payload: unknown): payload is { success: boolean; data?: unknown } {
  return !!payload && typeof payload === 'object' && 'success' in payload && typeof (payload as { success?: unknown }).success === 'boolean'
}

export type ApiRequestOptions = Omit<RequestInit, 'body'> & {
  baseUrl?: string
  auth?: boolean
  body?: unknown
  getAccessToken?: () => string | null
  getTokenType?: () => string | null
  onUnauthorized?: () => void
}

export async function apiFetch(path: string, options: ApiRequestOptions = {}): Promise<Response> {
  const url = buildUrl(path, options.baseUrl ?? defaultBaseUrl())
  const headers = new Headers(options.headers)

  if (!headers.has('Accept')) headers.set('Accept', 'application/json')

  const includeAuth = options.auth !== false
  if (includeAuth) {
    const accessToken = options.getAccessToken?.() ?? null
    const tokenType = options.getTokenType?.() ?? 'Bearer'
    if (accessToken) headers.set('Authorization', `${tokenType} ${accessToken}`)
  }

  let body: BodyInit | undefined
  if (options.body !== undefined) {
    if (isFormData(options.body)) {
      body = options.body
    } else {
      if (!headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
      body = JSON.stringify(options.body)
    }
  }

  const res = await fetch(url, {
    ...options,
    headers,
    body,
  })

  if (!res.ok) {
    const contentType = res.headers.get('content-type') ?? ''
    const isJson = contentType.includes('application/json')

    let payload: Payload | null = null
    if (isJson) {
      payload = (await res.json().catch(() => null)) as Payload | null
    } else {
      const text = await res.text().catch(() => '')
      payload = (tryParseJson(text) as Payload) ?? null
    }

    if (res.status === 401) {
      options.onUnauthorized?.()
      window.location.replace('/login')
      throw new ApiError('Unauthorized', res.status, payload)
    }
    const message = coerceErrorMessage(payload, res.statusText || 'Request failed')
    throw new ApiError(message, res.status, payload)
  }

  return res
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const url = buildUrl(path, options.baseUrl ?? defaultBaseUrl())
  const headers = new Headers(options.headers)

  if (!headers.has('Accept')) headers.set('Accept', 'application/json')

  const includeAuth = options.auth !== false
  if (includeAuth) {
    const accessToken = options.getAccessToken?.() ?? null
    const tokenType = options.getTokenType?.() ?? 'Bearer'
    if (accessToken) headers.set('Authorization', `${tokenType} ${accessToken}`)
  }

  let body: BodyInit | undefined
  if (options.body !== undefined) {
    if (isFormData(options.body)) {
      body = options.body
    } else {
      if (!headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
      body = JSON.stringify(options.body)
    }
  }

  const res = await fetch(url, {
    ...options,
    headers,
    body,
  })

  const contentType = res.headers.get('content-type') ?? ''
  const isJson = contentType.includes('application/json')

  let payload: Payload | null = null
  if (isJson) {
    payload = (await res.json().catch(() => null)) as Payload | null
  } else {
    const text = await res.text().catch(() => '')
    payload = (tryParseJson(text) as Payload) ?? null
  }
  console.log("res", res)

  if (!res.ok) {
    if (res.status === 401) {
      options.onUnauthorized?.()
      window.location.replace('/login')
      throw new ApiError('Unauthorized', res.status, payload)
    }
    const message = coerceErrorMessage(payload, res.statusText || 'Request failed')
    console.log("message", message)
    throw new ApiError(message, res.status, payload)
  }

  if (isEnvelope(payload)) {
    if (!payload.success) {
      const message = coerceErrorMessage(payload, 'Request failed')
      throw new ApiError(message, res.status, payload)
    }
    return (payload as { data?: unknown }).data as T
  }
  console.log("payload", payload)
  return payload as T
}

export type ApiClientConfig = {
  baseUrl?: string
  getAccessToken?: () => string | null
  getTokenType?: () => string | null
  onUnauthorized?: () => void
}

export function createApiClient(config: ApiClientConfig = {}) {
  const baseUrl = config.baseUrl ?? defaultBaseUrl()

  return {
    fetch: (path: string, options: Omit<ApiRequestOptions, 'baseUrl' | 'getAccessToken' | 'getTokenType' | 'onUnauthorized'> = {}) =>
      apiFetch(path, { ...options, baseUrl, ...config }),

    get: <T>(path: string, options: Omit<ApiRequestOptions, 'method' | 'body' | 'baseUrl'> = {}) =>
      apiRequest<T>(path, { ...options, method: 'GET', baseUrl, ...config }),

    post: <T, TBody = unknown>(
      path: string,
      body: TBody,
      options: Omit<ApiRequestOptions, 'method' | 'body' | 'baseUrl'> = {},
    ) => apiRequest<T>(path, { ...options, method: 'POST', body, baseUrl, ...config }),

    put: <T, TBody = unknown>(
      path: string,
      body: TBody,
      options: Omit<ApiRequestOptions, 'method' | 'body' | 'baseUrl'> = {},
    ) => apiRequest<T>(path, { ...options, method: 'PUT', body, baseUrl, ...config }),

    del: <T>(path: string, options: Omit<ApiRequestOptions, 'method' | 'body' | 'baseUrl'> = {}) =>
      apiRequest<T>(path, { ...options, method: 'DELETE', baseUrl, ...config }),
  }
}
