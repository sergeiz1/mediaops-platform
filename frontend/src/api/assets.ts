import { apiClient } from './client'
import type { Asset, ListAssetsParams, UploadAssetPayload, UploadAssetResponse } from '../types/asset'

export async function listAssets(params: ListAssetsParams = {}): Promise<Asset[]> {
  const { data } = await apiClient.get<Asset[]>('/api/v1/assets', { params })
  return data
}

export async function processAsset(assetId: number): Promise<void> {
  await apiClient.post(`/api/v1/assets/${assetId}/process`)
}

export async function deleteAsset(assetId: number): Promise<void> {
  await apiClient.delete(`/api/v1/assets/${assetId}`)
}

export async function uploadAsset(payload: UploadAssetPayload): Promise<UploadAssetResponse> {
  const formData = new FormData()
  formData.append('file', payload.file)
  formData.append('title', payload.title)
  if (payload.description) formData.append('description', payload.description)
  if (payload.speaker) formData.append('speaker', payload.speaker)
  if (payload.event_name) formData.append('event_name', payload.event_name)

  const { data } = await apiClient.post<UploadAssetResponse>('/api/v1/assets/upload', formData)
  return data
}
