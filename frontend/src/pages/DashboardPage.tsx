import { useEffect, useState } from 'react'
import { fetchApiHealth } from '../api/health'

function DashboardPage() {
  const [healthStatus, setHealthStatus] = useState<'loading' | 'ok' | 'error'>('loading')
  const [message, setMessage] = useState('Checking backend connection...')

  useEffect(() => {
    const runHealthCheck = async () => {
      try {
        const data = await fetchApiHealth()
        if (data.status === 'ok') {
          setHealthStatus('ok')
          setMessage('Backend API is reachable.')
          return
        }
        setHealthStatus('error')
        setMessage(`Unexpected health payload: ${data.status}`)
      } catch {
        setHealthStatus('error')
        setMessage('Backend API is not reachable.')
      }
    }

    void runHealthCheck()
  }, [])

  return (
    <>
      <h1>Media Operations Platform</h1>
      <p>
        API health:{' '}
        {healthStatus === 'loading' ? 'Loading...' : healthStatus === 'ok' ? 'OK' : 'Error'}
      </p>
      <p>{message}</p>
    </>
  )
}

export default DashboardPage
