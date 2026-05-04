import { createBrowserRouter } from 'react-router-dom'
import AppShell from '../components/layout/AppShell'
import DashboardPage from '../pages/DashboardPage'
import AssetsPage from '../pages/AssetsPage'
import UploadPage from '../pages/UploadPage'
import JobsPage from '../pages/JobsPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'assets', element: <AssetsPage /> },
      { path: 'upload', element: <UploadPage /> },
      { path: 'jobs', element: <JobsPage /> },
    ],
  },
])