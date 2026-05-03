import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'

export default function MeetingsPage() {
  const navigate = useNavigate()
  const [meetings, setMeetings] = useState([])
  const [title, setTitle] = useState('')
  const [meetingDate, setMeetingDate] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isCreating, setIsCreating] = useState(false)
  const [error, setError] = useState('')
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const menuRef = useRef(null)
  const userEmail = localStorage.getItem('user_email') || 'you@example.com'
  const userName = (userEmail.split('@')[0] || 'you').replace(/[._-]+/g, ' ')
  const initials = userName
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || '')
    .join('')
    .slice(0, 2)

  useEffect(() => {
    const onPointerDown = (event) => {
      if (!menuRef.current?.contains(event.target)) {
        setIsMenuOpen(false)
        setIsSettingsOpen(false)
      }
    }
    window.addEventListener('pointerdown', onPointerDown)
    return () => window.removeEventListener('pointerdown', onPointerDown)
  }, [])

  const load = async () => {
    setIsLoading(true)
    setError('')
    try {
      const res = await api.get('/meetings')
      setMeetings(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load meetings')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const createMeeting = async (e) => {
    e.preventDefault()
    setIsCreating(true)
    setError('')
    try {
      const res = await api.post('/meetings', { title, meeting_date: meetingDate })
      setTitle('')
      setMeetingDate('')
      navigate(`/meetings/${res.data.id}`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create meeting')
    } finally {
      setIsCreating(false)
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    navigate('/login')
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Dashboard</p>
          <h1>Meetings workspace</h1>
          <p>Create a meeting, generate outputs, and move from conversation to execution in one flow.</p>
        </div>
        <div className="actions">
          <div className="metric">
            <span>Total meetings</span>
            <strong>{meetings.length}</strong>
          </div>
          <div className="account-menu" ref={menuRef}>
            <button
              type="button"
              className="avatar-button"
              aria-haspopup="menu"
              aria-expanded={isMenuOpen || isSettingsOpen}
              onClick={() => {
                setIsSettingsOpen(false)
                setIsMenuOpen((open) => !open)
              }}
            >
              <span className="avatar-dot">{initials || 'U'}</span>
            </button>
            {isMenuOpen ? (
              <div className="menu-popover" role="menu">
                <button
                  type="button"
                  className="menu-item"
                  role="menuitem"
                  onClick={() => {
                    setIsMenuOpen(false)
                    setIsSettingsOpen(true)
                  }}
                >
                  <span className="menu-icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" focusable="false">
                      <path d="M19.14 12.94a7.43 7.43 0 0 0 .05-.94 7.43 7.43 0 0 0-.05-.94l2.03-1.58a.5.5 0 0 0 .12-.64l-1.92-3.32a.5.5 0 0 0-.6-.22l-2.39.96a7.22 7.22 0 0 0-1.63-.94l-.36-2.54a.5.5 0 0 0-.5-.42h-3.84a.5.5 0 0 0-.5.42l-.36 2.54a7.22 7.22 0 0 0-1.63.94l-2.39-.96a.5.5 0 0 0-.6.22L2.71 8.84a.5.5 0 0 0 .12.64l2.03 1.58a7.43 7.43 0 0 0-.05.94 7.43 7.43 0 0 0 .05.94L2.83 14.52a.5.5 0 0 0-.12.64l1.92 3.32a.5.5 0 0 0 .6.22l2.39-.96c.5.39 1.05.71 1.63.94l.36 2.54a.5.5 0 0 0 .5.42h3.84a.5.5 0 0 0 .5-.42l.36-2.54c.58-.23 1.13-.55 1.63-.94l2.39.96a.5.5 0 0 0 .6-.22l1.92-3.32a.5.5 0 0 0-.12-.64l-2.03-1.58ZM12 15.5A3.5 3.5 0 1 1 12 8.5a3.5 3.5 0 0 1 0 7Z" />
                    </svg>
                  </span>
                  <span className="menu-title">Settings</span>
                </button>
                <button type="button" className="menu-item danger" role="menuitem" onClick={logout}>
                  <span className="menu-icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" focusable="false">
                      <path d="M14 16.5a1 1 0 0 1 0-2h4.59l-1.8-1.8a1 1 0 1 1 1.42-1.4l3.5 3.5a1 1 0 0 1 0 1.4l-3.5 3.5a1 1 0 0 1-1.42-1.4l1.8-1.8H14ZM11.5 3A2.5 2.5 0 0 1 14 5.5v1a1 1 0 1 1-2 0v-1a.5.5 0 0 0-.5-.5h-7a.5.5 0 0 0-.5.5v13a.5.5 0 0 0 .5.5h7a.5.5 0 0 0 .5-.5v-1a1 1 0 1 1 2 0v1a2.5 2.5 0 0 1-2.5 2.5h-7A2.5 2.5 0 0 1 2 18.5v-13A2.5 2.5 0 0 1 4.5 3h7Z" />
                    </svg>
                  </span>
                  <span className="menu-title">Log out</span>
                </button>
              </div>
            ) : null}
            {isSettingsOpen ? (
              <div className="settings-popover" role="dialog" aria-label="Account settings">
                <p className="settings-title">Account</p>
                <div className="settings-row">
                  <span className="settings-label">Username</span>
                  <span className="settings-value">{userName}</span>
                </div>
                <div className="settings-row">
                  <span className="settings-label">Email</span>
                  <span className="settings-value">{userEmail}</span>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </header>

      {error && <div className="banner error">{error}</div>}

      <div className="grid-2">
        <section className="panel">
          <h2>Create meeting</h2>
          <p className="muted">Start a new workspace for one conversation.</p>
          <form onSubmit={createMeeting}>
            <label>Title</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Q2 planning sync" required />
            <label>Meeting date</label>
            <input type="date" value={meetingDate} onChange={(e) => setMeetingDate(e.target.value)} required />
            <button type="submit" disabled={isCreating}>{isCreating ? 'Creating...' : 'Create meeting'}</button>
          </form>
        </section>

        <section className="panel">
          <h2>How it works</h2>
          <div className="steps">
            <div><strong>1.</strong> Create meeting record</div>
            <div><strong>2.</strong> Upload docx or paste transcript</div>
            <div><strong>3.</strong> Generate and edit outputs</div>
            <div><strong>4.</strong> Approve and notify owner</div>
          </div>
        </section>
      </div>

      <section className="panel">
        <div className="panel-head">
          <h2>Recent meetings</h2>
          <button className="btn-secondary" onClick={load} disabled={isLoading}>
            {isLoading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
        {isLoading ? (
          <p className="muted">Loading meetings...</p>
        ) : meetings.length === 0 ? (
          <div className="empty">No meetings yet. Create your first meeting above.</div>
        ) : (
          <div className="list">
            {meetings.map((meeting) => (
              <article className="list-item" key={meeting.id}>
                <div>
                  <h3>{meeting.title}</h3>
                  <p className="muted">Date: {meeting.meeting_date || 'N/A'}</p>
                  <span className="status">{meeting.status}</span>
                </div>
                <Link className="btn-secondary list-item-cta" to={`/meetings/${meeting.id}`}>Open</Link>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
