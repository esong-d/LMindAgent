import { createApiClient } from '../../lib/apiClient'
import { clearStoredAuth, getAccessToken, getTokenType } from '../auth/store'
import type { OverviewData } from './types'

const overviewApi = createApiClient({
  baseUrl: '/api',
  getAccessToken,
  getTokenType,
  onUnauthorized: clearStoredAuth,
})

export async function getOverview(): Promise<OverviewData> {
  return overviewApi.get<OverviewData>('/v1/overview')
}
