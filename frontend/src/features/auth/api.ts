import { createApiClient } from '../../lib/apiClient'
import type { LoginBody, LoginResponse, RegisterBody, RegisterResponse } from './types'
import { clearStoredAuth, getAccessToken, getTokenType } from './store'

const authApi = createApiClient({
  baseUrl: '/api',
  getAccessToken,
  getTokenType,
  onUnauthorized: clearStoredAuth,
})

export async function login(body: LoginBody) {
  return authApi.post<LoginResponse, LoginBody>('/v1/login', body, { auth: false })
}

export async function register(body: RegisterBody) {
  return authApi.post<RegisterResponse, RegisterBody>('/v1/register', body, { auth: false })
}

export async function logout() {
  return authApi.post<void, null>('/v1/logout', null)
}
