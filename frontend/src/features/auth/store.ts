import type { UserOut, LoginResponse } from './types'

type StoredAuth = UserOut

const AUTH_STORAGE_KEY = 'auth'
const ACCESS_TOKEN_KEY = 'access_token'

export function getStoredAuth(): StoredAuth | null {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY)
    if (!raw) return null
    return JSON.parse(raw) as StoredAuth
  } catch {
    return null
  }
}

export function setStoredAuth(auth: LoginResponse) {
  console.log('setStoredAuth', auth)
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(auth.user))
  localStorage.setItem(ACCESS_TOKEN_KEY, JSON.stringify(auth.token))
}

export function clearStoredAuth() {
  localStorage.removeItem(AUTH_STORAGE_KEY)
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.clear()
}

export function getAccessToken() {
  const token = getStoredToken()
  return token ? token.access_token : null
}

export function getStoredToken() {
  const token = localStorage.getItem(ACCESS_TOKEN_KEY)
  return token ? JSON.parse(token) : null
}

export function getTokenType() {
  const token = getStoredToken()
  return token ? token.token_type : null
}

export function getStorageAuth() {
  const auth = getStoredAuth()
  return auth ? auth : null
}
