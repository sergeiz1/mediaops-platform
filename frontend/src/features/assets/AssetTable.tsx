import type { Asset } from '../../types/asset'

type Props = {
  assets: Asset[]
  onProcess?: (assetId: number) => void
  onDelete?: (assetId: number) => void
  busyAssetId?: number | null
}

function AssetTable({ assets, onProcess, onDelete, busyAssetId = null }: Props) {
  if (assets.length === 0) {
    return <p className="muted">No assets found.</p>
  }

  return (
    <div className="table-wrap">
      <table className="asset-table">
        <thead>
          <tr>
            <th>Title</th>
            <th>Type</th>
            <th>Speaker</th>
            <th>Event</th>
            <th>Visibility</th>
            <th>Status</th>
            <th>Uploaded</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {assets.map((asset) => (
            <tr key={asset.id}>
              <td>{asset.title}</td>
              <td>{asset.mime_type ?? '-'}</td>
              <td>{asset.speaker ?? '-'}</td>
              <td>{asset.event_name ?? '-'}</td>
              <td>{asset.visibility}</td>
              <td>{asset.status}</td>
              <td>{new Date(asset.uploaded_at).toLocaleString()}</td>
              <td className="actions">
                  <button
                    onClick={() => onProcess?.(asset.id)}
                    disabled={!onProcess || busyAssetId === asset.id || asset.status === 'ready' || asset.status === 'processing'}
                  >
                    Process
                  </button>
                <button
                  className="danger"
                  onClick={() => onDelete?.(asset.id)}
                  disabled={!onDelete || busyAssetId === asset.id}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default AssetTable
