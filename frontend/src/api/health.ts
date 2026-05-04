import { apiClient } from './client'

export type HealthResponse = {
  status: string
}

export async function fetchApiHealth(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>('/api/v1/health')
  return data
}
