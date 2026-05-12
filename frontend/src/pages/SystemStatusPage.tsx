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
  const workerBusy = controlBusy?.startsWith('worker:') ?? false
  const apiBusy = controlBusy?.startsWith('api:') ?? false
  const workerStateLabel =
    controlBusy === 'worker:start' || controlBusy === 'worker:restart'
      ? 'starting'
      : workerEffectiveRunning
        ? 'started'
        : 'stopped'
  const apiStateLabel =
    controlBusy === 'api:start' || controlBusy === 'api:restart'
      ? 'starting'
      : apiEffectiveRunning
        ? 'started'
        : 'stopped'

  const runControlAction = async (service: ServiceKey, action: ServiceAction) => {
    const key = `${service}:${action}`
    setControlBusy(key)
    try {
      const updated = await controlService(service, action)
      if (service === 'worker') {
        setWorkerRunning(updated.running)
      } else {
        setApiManagedRunning(updated.running)
      }
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
          <span>{`Worker process (${workerStateLabel})`}</span>
          <div className="status-inline-controls">
            <button
              type="button"
              onClick={() => void runControlAction('worker', 'start')}
              disabled={workerBusy || workerEffectiveRunning}
            >
              Start
            </button>
            <button
              type="button"
              onClick={() => void runControlAction('worker', 'stop')}
              disabled={workerBusy || !workerEffectiveRunning}
            >
              Stop
            </button>
            <button
              type="button"
              onClick={() => void runControlAction('worker', 'restart')}
              disabled={workerBusy}
            >
              Restart
            </button>
          </div>
        </div>
        <div className="status-row">
          <span>{`API log runner (${apiStateLabel})`}</span>
          <div className="status-inline-controls">
            <button
              type="button"
              onClick={() => void runControlAction('api', 'start')}
              disabled={apiBusy || apiEffectiveRunning}
            >
              Start
            </button>
            <button
              type="button"
              onClick={() => void runControlAction('api', 'stop')}
              disabled={apiBusy || !apiEffectiveRunning}
            >
              Stop
            </button>
            <button
              type="button"
              onClick={() => void runControlAction('api', 'restart')}
              disabled={apiBusy}
            >
              Restart
            </button>
          </div>
        </div>
      </div>
    </>
  )
}

export default SystemStatusPage
