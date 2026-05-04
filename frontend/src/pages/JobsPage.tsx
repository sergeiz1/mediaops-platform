import { useEffect, useState } from 'react'
import { listAssets, processAsset } from '../api/assets'
import type { Asset } from '../types/asset'

function JobsPage() {
  const [assets, setAssets] = useState<Asset[]>([])
  const [loading, setLoading] = useState(true)
  const [busyAssetId, setBusyAssetId] = useState<number | null>(null)

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

  return (
    <>
      <h1>Jobs</h1>
      {loading ? <p className="muted">Loading jobs...</p> : null}
      {!loading && assets.length === 0 ? <p className="muted">No running or failed jobs.</p> : null}
      <div className="job-list">
        {assets.map((asset) => (
          <div className="job-card" key={asset.id}>
            <div>
              <strong>{asset.title}</strong>
              <div className="muted">Status: {asset.status}</div>
            </div>
            <button onClick={() => handleRetry(asset.id)} disabled={busyAssetId === asset.id}>
              Retry
            </button>
          </div>
        ))}
      </div>
    </>
  )
}

export default JobsPage
