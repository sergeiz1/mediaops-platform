import { apiClient } from './client'

export type ServiceLogsResponse = {
  service: string
  lines: number
  content: string
  log_size_bytes: number
}

export type ManagedService = 'worker' | 'api'
export type ManagedAction = 'start' | 'stop' | 'restart'

export type ServiceControlState = {
  service: ManagedService
  running: boolean
  pid: number | null
}

export type ServiceControlStatusResponse = {
  worker: ServiceControlState
  api: ServiceControlState
}

export async function getServiceLogs(service: 'worker' | 'opensearch' | 'backend', lines = 120): Promise<ServiceLogsResponse> {
  const { data } = await apiClient.get<ServiceLogsResponse>(`/api/v1/system/logs/${service}`, { params: { lines } })
  return data
}

export async function clearServiceLogs(service: 'worker' | 'opensearch' | 'backend'): Promise<{ service: string; status: string }> {
  const { data } = await apiClient.post<{ service: string; status: string }>(`/api/v1/system/logs/${service}/clear`)
  return data
}

export async function getServiceControlStatus(): Promise<ServiceControlStatusResponse> {
  const { data } = await apiClient.get<ServiceControlStatusResponse>('/api/v1/system/control/status')
  return data
}

export async function controlService(service: ManagedService, action: ManagedAction): Promise<ServiceControlState> {
  const { data } = await apiClient.post<ServiceControlState>(`/api/v1/system/control/${service}/${action}`)
  return data
}
