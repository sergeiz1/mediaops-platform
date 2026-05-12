import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { fetchApiHealth } from '../api/health'
import { getAssetStats } from '../api/assets'
import { getServiceControlStatus } from '../api/system'
import type { AssetStats } from '../types/asset'

function DashboardPage() {
  const navigate = useNavigate()
  const [healthStatus, setHealthStatus] = useState<'loading' | 'ok' | 'error'>('loading')
  const [message, setMessage] = useState('Checking')
  const [stats, setStats] = useState<AssetStats | null>(null)
  const [workerRunning, setWorkerRunning] = useState<boolean | null>(null)

  useEffect(() => {
    const runHealthCheck = async () => {
      try {
        const data = await fetchApiHealth()
        if (data.status === 'ok') {
          setHealthStatus('ok')
          setMessage('API is reachable')
          return
        }
        setHealthStatus('error')
        setMessage(`Unexpected health payload: ${data.status}`)
      } catch {
        setHealthStatus('error')
        setMessage('API is not reachable')
      }
    }

    void runHealthCheck()

    const loadStats = async () => {
      try {
        const data = await getAssetStats(14)
        setStats(data)
      } catch {
        setStats(null)
      }
    }

    const loadControl = async () => {
      try {
        const data = await getServiceControlStatus()
        setWorkerRunning(data.worker.running)
      } catch {
        setWorkerRunning(null)
      }
    }

    void loadStats()
    void loadControl()
    const timer = setInterval(() => {
      void loadStats()
      void loadControl()
    }, 5000)
    return () => clearInterval(timer)
  }, [])

  const maxUploads = Math.max(...(stats?.uploads_per_day.map((item) => item.count) ?? [1]))
  const byStatus = stats?.by_status ?? {}
  const byMime = stats?.by_mime_type ?? {}
  const funnel = stats?.processing_funnel ?? { uploaded: 0, processing: 0, ready: 0, failed: 0 }
  const funnelTotal = funnel.uploaded + funnel.processing + funnel.ready + funnel.failed
  const uploadedPct = funnelTotal > 0 ? (funnel.uploaded / funnelTotal) * 100 : 0
  const processingPct = funnelTotal > 0 ? (funnel.processing / funnelTotal) * 100 : 0
  const readyPct = funnelTotal > 0 ? (funnel.ready / funnelTotal) * 100 : 0

  const formatActivityTimestamp = (isoValue: string) =>
    new Date(isoValue).toLocaleString('en-US', {
      month: 'short',
      day: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })

  return (
    <>
      <h1>Dashboard</h1>
      <div className="top-kpi-row top-kpi-row--single">
        <Link className="health-card health-card--status health-card-link" to="/system-status">
          <div className="kpi-label">API health</div>
          <div className={`kpi-value health-kpi-value ${healthStatus === 'ok' ? 'ok' : healthStatus === 'error' ? 'error' : ''}`}>
            {healthStatus === 'loading' ? 'Loading...' : healthStatus === 'ok' ? 'OK' : 'Error'}
          </div>
        </Link>
        <div className="kpi-card">
          <div className="kpi-label">Worker</div>
          <div className={`kpi-value ${(workerRunning ?? stats?.worker_online) ? 'ok' : 'error'}`}>
            {(workerRunning ?? stats?.worker_online) ? 'Online' : 'Offline'}
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Failed</div>
          <div className="kpi-value">{byStatus.failed ?? 0}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Processing</div>
          <div className="kpi-value">{byStatus.processing ?? 0}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Pending jobs</div>
          <div className="kpi-value">{stats?.pending_jobs ?? 0}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Ready</div>
          <div className="kpi-value">{byStatus.ready ?? 0}</div>
        </div>
        <Link className="kpi-card health-card-link" to="/assets">
          <div className="kpi-label">Total assets</div>
          <div className="kpi-value">{stats?.total_assets ?? '-'}</div>
        </Link>
        {healthStatus === 'ok' ? (
          <a
            className="health-card health-card--reachability health-card-link"
            href={`${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'}/docs`}
            target="_blank"
            rel="noreferrer"
          >
            <div className="kpi-label">Backend reachability</div>
            <div className={`kpi-value health-kpi-value health-kpi-text ok`}>{message}</div>
          </a>
        ) : (
          <div className="health-card health-card--reachability">
            <div className="kpi-label">Backend reachability</div>
            <div className={`kpi-value health-kpi-value health-kpi-text error`}>{message}</div>
          </div>
        )}
      </div>

      <div className="chart-grid">
        <div className="chart-card">
          <h3>Uploads by day (last 14 days)</h3>
          <div className="bar-chart">
            {(stats?.uploads_per_day ?? []).map((item) => (
              <div className="bar-chart__item" key={item.date}>
                <div
                  className="bar-chart__bar"
                  style={{ height: `${Math.max((item.count / maxUploads) * 120, item.count > 0 ? 8 : 2)}px` }}
                  title={`${item.date}: ${item.count}`}
                />
                <div className="bar-chart__label">{item.date.slice(5)}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="chart-card">
          <h3>Processing funnel</h3>
          <div className="funnel-pie-wrap">
            <div
              className="funnel-pie"
              style={{
                background: `conic-gradient(
                  #5c7fae 0% ${uploadedPct}%,
                  #2a68b8 ${uploadedPct}% ${uploadedPct + processingPct}%,
                  #1f8f4b ${uploadedPct + processingPct}% ${uploadedPct + processingPct + readyPct}%,
                  #b91f4f ${uploadedPct + processingPct + readyPct}% 100%
                )`,
              }}
              aria-label="Processing funnel distribution"
            >
              <span>{funnelTotal}</span>
            </div>
            <div className="funnel-legend">
              <div className="funnel-legend-item"><i className="dot failed" />failed: <strong>{funnel.failed}</strong></div>
              <div className="funnel-legend-item"><i className="dot processing" />processing: <strong>{funnel.processing}</strong></div>
              <div className="funnel-legend-item"><i className="dot uploaded" />uploaded: <strong>{funnel.uploaded}</strong></div>
              <div className="funnel-legend-item"><i className="dot ready" />ready: <strong>{funnel.ready}</strong></div>
            </div>
          </div>
        </div>

        <div className="chart-card">
          <h3>MIME type distribution</h3>
          <div className="stat-list">
            {Object.entries(byMime).map(([key, value]) => (
              <div className="stat-row" key={key}>
                <span>{key}</span>
                <strong>{value}</strong>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="chart-grid chart-grid--logs">
        <div className="chart-card">
          <h3>Worker logs</h3>
          <div className="stat-list">
            <div className="stat-row">
              <span>Status</span>
              <strong className={(workerRunning ?? stats?.worker_online) ? 'ok' : 'error'}>
                {(workerRunning ?? stats?.worker_online) ? 'online' : 'offline'}
              </strong>
            </div>
          </div>
          <button className="log-cmd-btn" onClick={() => navigate('/logs?service=worker')} type="button">
            View logs
          </button>
        </div>

        <div className="chart-card">
          <h3>OpenSearch logs</h3>
          <div className="stat-list">
            <div className="stat-row">
              <span>Service</span>
              <strong>docker</strong>
            </div>
          </div>
          <button className="log-cmd-btn" onClick={() => navigate('/logs?service=opensearch')} type="button">
            View logs
          </button>
        </div>

        <div className="chart-card">
          <h3>Backend logs</h3>
          <div className="stat-list">
            <div className="stat-row">
              <span>API</span>
              <strong className={healthStatus === 'ok' ? 'ok' : 'error'}>{healthStatus === 'ok' ? 'running' : 'down'}</strong>
            </div>
          </div>
          <button className="log-cmd-btn" onClick={() => navigate('/logs?service=backend')} type="button">
            View logs
          </button>
        </div>
      </div>

      <div className="chart-grid">
        <div className="chart-card">
          <h3>Activity</h3>
          <div className="stat-list">
            {[
              ...(stats?.recent_activity.uploads ?? []).map((item) => ({
                key: `u-${item.id}-${item.at}`,
                title: item.title,
                at: item.at,
                kind: 'upload',
              })),
              ...(stats?.recent_activity.process_starts ?? []).map((item) => ({
                key: `p-${item.id}-${item.at}`,
                title: item.title,
                at: item.at,
                kind: 'process start',
              })),
              ...(stats?.recent_activity.fails ?? []).map((item) => ({
                key: `f-${item.id}-${item.at}`,
                title: item.title,
                at: item.at,
                kind: 'failure',
              })),
            ]
              .sort((a, b) => new Date(b.at).getTime() - new Date(a.at).getTime())
              .slice(0, 8)
              .map((item) => (
                <div className="stat-row" key={item.key}>
                  <span>[{item.kind}] {item.title}</span>
                  <strong>{formatActivityTimestamp(item.at)}</strong>
                </div>
              ))}
          </div>
        </div>

        <div className="chart-card chart-card--double">
          <h3>Failure monitor</h3>
          <div className="stat-list">
            {(stats?.failure_insights ?? []).length === 0 && (stats?.recent_activity.fails ?? []).length === 0 ? (
              <p className="chart-empty">No failures.</p>
            ) : null}
            {(stats?.failure_insights ?? []).map((item) => (
              <div className="stat-row" key={`reason-${item.reason}`}>
                <span title={item.reason}>{item.reason}</span>
                <strong>{item.count}</strong>
              </div>
            ))}
            {(stats?.recent_activity.fails ?? []).slice(0, 4).map((item) => (
              <div className="stat-row" key={`recent-fail-${item.id}-${item.at}`}>
                <span title={item.reason}>{item.title}</span>
                <strong>{formatActivityTimestamp(item.at)}</strong>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  )
}

export default DashboardPage
