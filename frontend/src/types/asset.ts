export type AssetStatus = 'uploaded' | 'processing' | 'ready' | 'failed'
export type AssetVisibility = 'private' | 'public'

export type Asset = {
  id: number
  title: string
  description: string | null
  file_key: string | null
  file_name: string
  mime_type: string | null
  duration_seconds: number | null
  speaker: string | null
  event_name: string | null
  visibility: AssetVisibility
  status: AssetStatus
  uploaded_at: string
  published_at: string | null
  created_at: string
  updated_at: string
}

export type ListAssetsParams = {
  q?: string
  status?: AssetStatus
  visibility?: AssetVisibility
  speaker?: string
  event_name?: string
  sort?: 'newest' | 'oldest' | 'title'
}

export type UploadAssetPayload = {
  file: File
  title: string
  description?: string
  speaker?: string
  event_name?: string
}

export type UploadAssetResponse = {
  asset: Asset
  stored_path: string
}
