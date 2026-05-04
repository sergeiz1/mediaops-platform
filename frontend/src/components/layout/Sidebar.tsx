import { NavLink } from 'react-router-dom'

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar__brand">OpenMedia Hub</div>

      <nav className="sidebar__nav">
        <NavLink to="/">Dashboard</NavLink>
        <NavLink to="/assets">Assets</NavLink>
        <NavLink to="/upload">Upload</NavLink>
        <NavLink to="/jobs">Jobs</NavLink>
      </nav>
    </aside>
  )
}

export default Sidebar
