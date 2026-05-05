import { useEffect, useState } from 'react'
import { fetchApiHealth } from '../api/health'
import { getAssetStats, listAssets } from '../api/assets'
import { controlService, getServiceControlStatus } from '../api/system'

type ServiceKey = 'worker' | 'api'
type ServiceAction = 'start' | 'stop' | 'restart'

function SystemStatusPage() {
  const [apiStatus, setApiStatus] = useState<'operational' | 'degraded'>('degraded')
  const [assetCount, setAssetCount] = useState<number>(0)
  const [lastCheck, setLastCheck] = useState<string>('-')
  const [workerRunning, setWorkerRunning] = useState(false)
  const [apiManagedRunning, setApiManagedRunning] = useState(false)
  const [workerLiveOnline, setWorkerLiveOnline] = useState(false)
  const [controlBusy, setControlBusy] = useState<string | null>(null)
  const [controlMessage, setControlMessage] = useState<string>('')

  useEffect(() => {
    const load = async () => {
      try {
        const [health, assets, controlStatus, stats] = await Promise.all([
          fetchApiHealth(),
          listAssets({ sort: 'newest' }),
          getServiceControlStatus(),
          getAssetStats(1),
        ])
        setApiStatus(health.status === 'ok' ? 'operational' : 'degraded')
        setAssetCount(assets.length)
        setWorkerRunning(controlStatus.worker.running)
        setApiManagedRunning(controlStatus.api.running)
        setWorkerLiveOnline(Boolean(stats.worker_online))
      } catch {
        setApiStatus('degraded')
      } finally {
        setLastCheck(new Date().toLocaleString())
      }
    }

    void load()
    const timer = setInterval(() => {
      void load()
    }, 5000)
    return () => clearInterval(timer)
  }, [])

  const workerEffectiveRunning = workerRunning || workerLiveOnline
  const apiEffectiveRunning = apiManagedRunning || apiStatus === 'operational'

  const runControlAction = async (service: ServiceKey, action: ServiceAction) => {
    const key = `${service}:${action}`
    setControlBusy(key)
    setControlMessage('')
    try {
      const updated = await controlService(service, action)
      if (service === 'worker') {
        setWorkerRunning(updated.running)
      } else {
        setApiManagedRunning(updated.running)
      }
      setControlMessage(`${service.toUpperCase()} ${action} executed`)
    } catch {
      setControlMessage(`Could not ${action} ${service}`)
    } finally {
      setControlBusy(null)
      setLastCheck(new Date().toLocaleString())
    }
  }

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
        <div className="status-row">
          <span>Worker process</span>
          <div className="status-inline-controls">
            <button
              type="button"
              onClick={() => void runControlAction('worker', 'start')}
              disabled={controlBusy !== null || workerEffectiveRunning}
            >
              Start
            </button>
            <button
              type="button"
              onClick={() => void runControlAction('worker', 'stop')}
              disabled={controlBusy !== null || !workerEffectiveRunning}
            >
              Stop
            </button>
            <button
              type="button"
              onClick={() => void runControlAction('worker', 'restart')}
              disabled={controlBusy !== null}
            >
              Restart
            </button>
          </div>
        </div>
        <div className="status-row">
          <span>API log runner</span>
          <div className="status-inline-controls">
            <button
              type="button"
              onClick={() => void runControlAction('api', 'start')}
              disabled={controlBusy !== null || apiEffectiveRunning}
            >
              Start
            </button>
            <button
              type="button"
              onClick={() => void runControlAction('api', 'stop')}
              disabled={controlBusy !== null || !apiEffectiveRunning}
            >
              Stop
            </button>
            <button
              type="button"
              onClick={() => void runControlAction('api', 'restart')}
              disabled={controlBusy !== null}
            >
              Restart
            </button>
          </div>
        </div>
        {controlMessage ? <p className="status-control-message">{controlMessage}</p> : null}
      </div>
    </>
  )
}

export default SystemStatusPage
