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
  processing_started_at: string | null
  processing_finished_at: string | null
  last_error: string | null
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

export type AssetStats = {
  total_assets: number
  by_status: Record<string, number>
  by_mime_type: Record<string, number>
  uploads_per_day: Array<{ date: string; count: number }>
  pending_jobs: number
  worker_online: boolean
  processing_funnel: {
    uploaded: number
    processing: number
    ready: number
    failed: number
  }
  failure_insights: Array<{ reason: string; count: number }>
  time_to_ready: {
    avg_seconds: number
    median_seconds: number
    last_runtime_seconds: number
  }
  recent_activity: {
    uploads: Array<{ id: number; title: string; at: string }>
    process_starts: Array<{ id: number; title: string; at: string }>
    fails: Array<{ id: number; title: string; at: string; reason: string }>
  }
}
