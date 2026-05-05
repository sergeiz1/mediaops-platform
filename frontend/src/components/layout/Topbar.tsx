import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { fetchApiHealth } from '../../api/health'

const pageTitles: Record<string, string> = {
  '/': 'Dashboard',
  '/assets': 'Assets',
  '/upload': 'Upload',
  '/jobs': 'Jobs',
  '/system-status': 'System Status',
  '/logs': 'Logs',
}

function Topbar() {
  const location = useLocation()
  const navigate = useNavigate()
  const [statusState, setStatusState] = useState<'operational' | 'degraded'>('degraded')
  const title = pageTitles[location.pathname] ?? 'Media Operations Platform'

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const data = await fetchApiHealth()
        setStatusState(data.status === 'ok' ? 'operational' : 'degraded')
      } catch {
        setStatusState('degraded')
      }
    }
    void checkHealth()
  }, [location.pathname])

  return (
    <header className="topbar">
      <div className="topbar__title">{title}</div>
      <button className="topbar__status" onClick={() => navigate('/system-status')}>
        <span className={`topbar__status-dot ${statusState}`} />
        {statusState === 'operational' ? 'Operational' : 'Degraded'}
      </button>
    </header>
  )
}

export default Topbar
