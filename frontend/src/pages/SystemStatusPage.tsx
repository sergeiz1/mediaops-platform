import { useEffect, useState } from 'react'
import { fetchApiHealth } from '../api/health'
import { listAssets } from '../api/assets'

function SystemStatusPage() {
  const [apiStatus, setApiStatus] = useState<'operational' | 'degraded'>('degraded')
  const [assetCount, setAssetCount] = useState<number>(0)
  const [lastCheck, setLastCheck] = useState<string>('-')

  useEffect(() => {
    const load = async () => {
      try {
        const [health, assets] = await Promise.all([fetchApiHealth(), listAssets({ sort: 'newest' })])
        setApiStatus(health.status === 'ok' ? 'operational' : 'degraded')
        setAssetCount(assets.length)
      } catch {
        setApiStatus('degraded')
      } finally {
        setLastCheck(new Date().toLocaleString())
      }
    }

    void load()
  }, [])

  return (
    <>
      <h1>System Status</h1>
      <div className="status-panel">
        <div className="status-row">
          <span>API</span>
          <span className={`status-badge ${apiStatus}`}>{apiStatus}</span>
        </div>
        <div className="status-row">
          <span>Indexed/Search Layer</span>
          <span className="status-badge info">OpenSearch-enabled</span>
        </div>
        <div className="status-row">
          <span>Assets in library</span>
          <span>{assetCount}</span>
        </div>
        <div className="status-row">
          <span>Last check</span>
          <span>{lastCheck}</span>
        </div>
      </div>
    </>
  )
}

export default SystemStatusPage
