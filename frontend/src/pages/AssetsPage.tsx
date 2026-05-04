import { useEffect, useState } from 'react'
import { deleteAsset, listAssets, processAsset } from '../api/assets'
import AssetTable from '../features/assets/AssetTable'
import type { Asset, AssetStatus, AssetVisibility } from '../types/asset'

function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([])
  const [loading, setLoading] = useState(true)
  const [busyAssetId, setBusyAssetId] = useState<number | null>(null)
  const [q, setQ] = useState('')
  const [status, setStatus] = useState<AssetStatus | ''>('')
  const [visibility, setVisibility] = useState<AssetVisibility | ''>('')

  const load = async () => {
    setLoading(true)
    try {
      const data = await listAssets({
        q: q || undefined,
        status: status || undefined,
        visibility: visibility || undefined,
        sort: 'newest',
      })
      setAssets(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const timer = setTimeout(() => {
      void load()
    }, 250)
    return () => clearTimeout(timer)
  }, [q, status, visibility])

  const handleProcess = async (assetId: number) => {
    setBusyAssetId(assetId)
    try {
      await processAsset(assetId)
      await load()
    } finally {
      setBusyAssetId(null)
    }
  }

  const handleDelete = async (assetId: number) => {
    const confirmed = window.confirm(`Delete asset #${assetId}? This action cannot be undone.`)
    if (!confirmed) {
      return
    }

    setBusyAssetId(assetId)
    try {
      await deleteAsset(assetId)
      await load()
    } finally {
      setBusyAssetId(null)
    }
  }

  return (
    <>
      <h1>Assets</h1>
      <div className="toolbar">
        <input placeholder="Search title/description" value={q} onChange={(e) => setQ(e.target.value)} />
        <select value={status} onChange={(e) => setStatus(e.target.value as AssetStatus | '')}>
          <option value="">All statuses</option>
          <option value="uploaded">uploaded</option>
          <option value="processing">processing</option>
          <option value="ready">ready</option>
          <option value="failed">failed</option>
        </select>
        <select value={visibility} onChange={(e) => setVisibility(e.target.value as AssetVisibility | '')}>
          <option value="">All visibility</option>
          <option value="private">private</option>
          <option value="public">public</option>
        </select>
      </div>

      {loading ? (
        <p className="muted">Loading assets...</p>
      ) : (
        <AssetTable assets={assets} onProcess={handleProcess} onDelete={handleDelete} busyAssetId={busyAssetId} />
      )}
    </>
  )
}

export default AssetsPage
