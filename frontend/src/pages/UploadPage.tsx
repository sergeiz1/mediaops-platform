import { type FormEvent, useState } from 'react'
import { processAsset, uploadAsset } from '../api/assets'

function UploadPage() {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [speaker, setSpeaker] = useState('')
  const [eventName, setEventName] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [autoProcess, setAutoProcess] = useState(true)
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const onSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!file || !title.trim()) {
      setMessage('Title and file are required.')
      return
    }

    setSubmitting(true)
    try {
      const res = await uploadAsset({
        file,
        title,
        description: description || undefined,
        speaker: speaker || undefined,
        event_name: eventName || undefined,
      })
      if (autoProcess) {
        await processAsset(res.asset.id)
      }
      setMessage(`Uploaded asset #${res.asset.id}${autoProcess ? ' and started processing.' : '.'}`)
      setTitle('')
      setDescription('')
      setSpeaker('')
      setEventName('')
      setFile(null)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <h1>Upload</h1>
      <form className="stack-form" onSubmit={onSubmit}>
        <label>
          Title
          <input value={title} onChange={(e) => setTitle(e.target.value)} required />
        </label>
        <label>
          Description
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={4} />
        </label>
        <label>
          Speaker
          <input value={speaker} onChange={(e) => setSpeaker(e.target.value)} />
        </label>
        <label>
          Event
          <input value={eventName} onChange={(e) => setEventName(e.target.value)} />
        </label>
        <label>
          File
          <input
            type="file"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            required
          />
        </label>
        <label className="inline">
          <input type="checkbox" checked={autoProcess} onChange={(e) => setAutoProcess(e.target.checked)} />
          Start processing after upload
        </label>
        <button type="submit" className="upload-btn" disabled={submitting}>
          {submitting ? 'Uploading...' : 'Upload Asset'}
        </button>
      </form>
      {message ? <p className="muted">{message}</p> : null}
    </>
  )
}

export default UploadPage
