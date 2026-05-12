import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { clearServiceLogs, getServiceLogs } from '../api/system'
import axios from 'axios'

type LogService = 'worker' | 'opensearch' | 'backend'

function LogsPage() {
  const [params, setParams] = useSearchParams()
  const requested = (params.get('service') ?? 'worker').toLowerCase()
  const initialService: LogService =
    requested === 'opensearch' || requested === 'backend' ? (requested as LogService) : 'worker'

  const [service, setService] = useState<LogService>(initialService)
  const [lines, setLines] = useState(120)
  const [content, setContent] = useState('Loading logs...')
  const [logSizeBytes, setLogSizeBytes] = useState(0)
  const [loading, setLoading] = useState(false)
  const [clearing, setClearing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const title = useMemo(() => `${service[0].toUpperCase()}${service.slice(1)} Logs`, [service])

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getServiceLogs(service, lines)
      setContent(data.content || '(no log output)')
      setLogSizeBytes(data.log_size_bytes ?? 0)
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        const detail = (err.response?.data as { detail?: string } | undefined)?.detail
        setError(detail ?? 'Could not load logs')
      } else {
        setError('Could not load logs')
      }
    } finally {
      setLoading(false)
    }
  }, [service, lines])

  const formatSize = (bytes: number) => {
    const gb = bytes / (1024 * 1024 * 1024)
    return `${gb.toFixed(2)} GB`
  }

  const sizeClass = logSizeBytes >= 1.8 * 1024 * 1024 * 1024 ? 'danger' : logSizeBytes >= 1.6 * 1024 * 1024 * 1024 ? 'warn' : 'ok'

  const clearLogs = useCallback(async () => {
    setClearing(true)
    setError(null)
    try {
      await clearServiceLogs(service)
      await load()
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        const detail = (err.response?.data as { detail?: string } | undefined)?.detail
        setError(detail ?? 'Could not clear logs')
      } else {
        setError('Could not clear logs')
      }
    } finally {
      setClearing(false)
    }
  }, [service, load])

  useEffect(() => {
    setParams({ service })
    const bootstrap = setTimeout(() => {
      void load()
    }, 0)
    const timer = setInterval(() => void load(), 5000)
    return () => {
      clearTimeout(bootstrap)
      clearInterval(timer)
    }
  }, [service, load, setParams])

  return (
    <>
      <h1>Logs</h1>
      <div className="toolbar">
        <select value={service} onChange={(e) => setService(e.target.value as LogService)}>
          <option value="worker">Worker logs</option>
          <option value="opensearch">OpenSearch logs</option>
          <option value="backend">Backend logs</option>
        </select>
        <select value={lines} onChange={(e) => setLines(Number(e.target.value))}>
          <option value={80}>80 lines</option>
          <option value={120}>120 lines</option>
          <option value={250}>250 lines</option>
          <option value={500}>500 lines</option>
        </select>
        <button className="log-refresh-btn" type="button" onClick={() => void load()} disabled={loading} title={loading ? 'Refreshing logs' : 'Refresh logs'}>
          <span aria-hidden="true">{loading ? '...' : '↻'}</span>
          <span className="sr-only">{loading ? 'Refreshing logs' : 'Refresh logs'}</span>
        </button>
        <button className="log-clear-btn" type="button" onClick={() => void clearLogs()} disabled={clearing || loading} title={clearing ? 'Clearing logs...' : 'Clear logs'}>
          <span aria-hidden="true">{clearing ? '…' : '🗑'}</span>
          <span className="sr-only">{clearing ? 'Clearing logs' : 'Clear logs'}</span>
        </button>
        <div className={`log-size-pill ${sizeClass}`}>Log size: {formatSize(logSizeBytes)}</div>
      </div>

      <div className="chart-card">
        <h3>{title}</h3>
        {error ? <p className="chart-empty">{error}</p> : null}
        <pre className="logs-pre">{content}</pre>
      </div>
    </>
  )
}

export default LogsPage
