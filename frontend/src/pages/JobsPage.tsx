import { useEffect, useState } from 'react'
import { listAssets, processAsset } from '../api/assets'
import type { Asset } from '../types/asset'

function JobsPage() {
  const [assets, setAssets] = useState<Asset[]>([])
  const [loading, setLoading] = useState(true)
  const [busyAssetId, setBusyAssetId] = useState<number | null>(null)
  const [expandedAssetIds, setExpandedAssetIds] = useState<number[]>([])

  const load = async () => {
    setLoading(true)
    try {
      const data = await listAssets({ sort: 'newest' })
      setAssets(data.filter((asset) => asset.status !== 'ready'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const handleRetry = async (assetId: number) => {
    setBusyAssetId(assetId)
    try {
      await processAsset(assetId)
      await load()
    } finally {
      setBusyAssetId(null)
    }
  }

  const toggleDetails = (assetId: number) => {
    setExpandedAssetIds((prev) =>
      prev.includes(assetId) ? prev.filter((id) => id !== assetId) : [...prev, assetId],
    )
  }

  return (
    <>
      <h1>Jobs</h1>
      {loading ? <p className="muted">Loading jobs...</p> : null}
      {!loading && assets.length === 0 ? <p className="muted">No running or failed jobs.</p> : null}
      <div className="job-list">
        {assets.map((asset) => (
          <div className={`job-card ${expandedAssetIds.includes(asset.id) ? 'expanded' : ''}`} key={asset.id}>
            <div className="job-card__main">
              <strong>{asset.title}</strong>
              <div className="muted">Status: {asset.status}</div>
              {expandedAssetIds.includes(asset.id) ? (
                <div className="job-card__details">
                  <div>ID: {asset.id}</div>
                  <div>File: {asset.file_name}</div>
                  <div>MIME: {asset.mime_type ?? '-'}</div>
                  <div>Speaker: {asset.speaker ?? '-'}</div>
                  <div>Event: {asset.event_name ?? '-'}</div>
                  <div>Visibility: {asset.visibility}</div>
                  <div>Uploaded: {new Date(asset.uploaded_at).toLocaleString()}</div>
                  <div>Updated: {new Date(asset.updated_at).toLocaleString()}</div>
                </div>
              ) : null}
            </div>
            {asset.status === 'failed' ? (
              <button onClick={() => handleRetry(asset.id)} disabled={busyAssetId === asset.id}>
                Retry
              </button>
            ) : (
              <button onClick={() => toggleDetails(asset.id)}>
                {expandedAssetIds.includes(asset.id) ? 'Hide details' : 'Details'}
              </button>
            )}
          </div>
        ))}
      </div>
    </>
  )
}

export default JobsPage
