import { useLocation } from 'react-router-dom'

const pageTitles: Record<string, string> = {
  '/': 'Dashboard',
  '/assets': 'Assets',
  '/upload': 'Upload',
  '/jobs': 'Jobs',
}

function Topbar() {
  const location = useLocation()
  const title = pageTitles[location.pathname] ?? 'Media Operations Platform'

  return (
    <header className="topbar">
      <div className="topbar__title">{title}</div>
      <div className="topbar__status">
        <span className="topbar__status-dot" />
        Operational
      </div>
    </header>
  )
}

export default Topbar
