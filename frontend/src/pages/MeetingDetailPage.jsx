import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'

const templateKeys = ['welcome', 'thank_you', 'next_steps', 'proposal_eta', 'follow_up_reminder']

export default function MeetingDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [docx, setDocx] = useState(null)
  const [meetingText, setMeetingText] = useState('')
  const [bundle, setBundle] = useState(null)
  const [activeTemplate, setActiveTemplate] = useState('welcome')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [isLoadingBundle, setIsLoadingBundle] = useState(true)
  const [savingState, setSavingState] = useState('')

  const setTransientNotice = (message) => {
    setNotice(message)
    window.setTimeout(() => setNotice(''), 2400)
  }

  const loadBundle = async () => {
    setIsLoadingBundle(true)
    try {
      const res = await api.get(`/meetings/${id}`)
      setBundle(res.data)
      setError('')
    } catch (err) {
      setBundle(null)
      if (err.response?.status !== 400) {
        setError(err.response?.data?.detail || 'Failed to load meeting bundle')
      }
    } finally {
      setIsLoadingBundle(false)
    }
  }

  useEffect(() => {
    loadBundle()
  }, [id])

  const uploadDocx = async () => {
    if (!docx) return
    setError('')
    setSavingState('uploading')
    const form = new FormData()
    form.append('file', docx)
    try {
      await api.post(`/meetings/${id}/upload-docx`, form)
      setTransientNotice('DOCX uploaded')
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setSavingState('')
    }
  }

  const generate = async () => {
    setIsGenerating(true)
    setError('')
    try {
      const payload = meetingText.trim() ? { meeting_text: meetingText } : {}
      const res = await api.post(`/meetings/${id}/generate-bundle`, payload)
      setBundle(res.data)
      setTransientNotice('Bundle generated')
    } catch (err) {
      setError(err.response?.data?.detail || 'Generation failed')
    } finally {
      setIsGenerating(false)
    }
  }

  const saveOutput = async () => {
    if (!bundle) return
    setSavingState('outputs')
    try {
      await api.patch(`/meetings/${id}/outputs`, {
        summary: bundle.summary,
        crm: bundle.crm,
        participant_tasks: bundle.participant_tasks,
      })
      setTransientNotice('Summary and CRM saved')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save outputs')
    } finally {
      setSavingState('')
    }
  }

  const saveTasks = async () => {
    if (!bundle) return
    setSavingState('tasks')
    try {
      const res = await api.put(`/meetings/${id}/tasks`, { tasks: bundle.my_tasks })
      setBundle(res.data)
      setTransientNotice('My tasks saved')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save tasks')
    } finally {
      setSavingState('')
    }
  }

  const saveEmail = async () => {
    if (!bundle) return
    setSavingState('email')
    const email = bundle.emails.find((e) => e.template_key === activeTemplate)
    if (!email) return
    try {
      const res = await api.patch(`/meetings/${id}/emails/${activeTemplate}`, {
        subject: email.subject,
        body: email.body,
      })
      setBundle(res.data)
      setTransientNotice('Email template saved')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save email')
    } finally {
      setSavingState('')
    }
  }

  const approve = async () => {
    setSavingState('approve')
    try {
      const res = await api.post(`/meetings/${id}/approve`)
      setBundle(res.data)
      setTransientNotice('Bundle approved')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to approve bundle')
    } finally {
      setSavingState('')
    }
  }

  const updateTask = (index, patch) => {
    const copy = [...bundle.my_tasks]
    copy[index] = { ...copy[index], ...patch }
    setBundle({ ...bundle, my_tasks: copy })
  }

  const updateParticipantTask = (index, patch) => {
    const copy = [...bundle.participant_tasks]
    copy[index] = { ...copy[index], ...patch }
    setBundle({ ...bundle, participant_tasks: copy })
  }

  const updateEmailField = (key, field, value) => {
    const copy = bundle.emails.map((e) => (e.template_key === key ? { ...e, [field]: value } : e))
    setBundle({ ...bundle, emails: copy })
  }

  const currentEmail = bundle?.emails.find((e) => e.template_key === activeTemplate)

  return (
    <div className="app-shell">
      <header className="topbar compact">
        <div>
          <button className="btn-secondary" onClick={() => navigate('/')}>Back to meetings</button>
          <h1>Meeting #{id}</h1>
          <p>Upload or paste notes, generate the bundle, edit outputs, and approve.</p>
        </div>
      </header>

      {error && <div className="banner error">{error}</div>}
      {notice && <div className="banner success">{notice}</div>}

      <section className="panel">
        <h2>Source input</h2>
        <div className="grid-2">
          <div className="upload-col">
            <label>Upload Document</label>
            <input
              id={`file-input-${id}`}
              type="file"
              accept=".docx"
              style={{ display: 'none' }}
              onChange={(e) => setDocx(e.target.files?.[0] || null)}
            />
            <div
              className={`upload-zone${docx ? ' upload-zone--selected' : ''}`}
              onClick={() => document.getElementById(`file-input-${id}`).click()}
            >
              <svg className="upload-zone-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              {docx ? (
                <span className="upload-zone-filename">{docx.name}</span>
              ) : (
                <>
                  <span className="upload-zone-text">Click to browse</span>
                  <span className="upload-zone-hint">.docx files only</span>
                </>
              )}
            </div>
            <button
              onClick={uploadDocx}
              disabled={!docx || savingState === 'uploading'}
              className={docx ? '' : 'btn-secondary'}
            >
              {savingState === 'uploading' ? 'Uploading...' : 'Upload Document'}
            </button>
          </div>
          <div>
            <label>Or paste meeting text</label>
            <textarea
              rows={8}
              value={meetingText}
              onChange={(e) => setMeetingText(e.target.value)}
              placeholder="Paste transcript or notes here..."
            />
            <button onClick={generate} disabled={isGenerating}>
              {isGenerating ? 'Generating bundle...' : 'Generate bundle'}
            </button>
          </div>
        </div>
      </section>

      {isLoadingBundle && !bundle ? <div className="panel"><p className="muted">Loading meeting bundle...</p></div> : null}

      {!bundle ? null : (
        <>
          <section className="panel">
            <div className="panel-head">
              <h2>Summary + CRM</h2>
              <button className="btn-secondary" onClick={saveOutput} disabled={savingState === 'outputs'}>
                {savingState === 'outputs' ? 'Saving...' : 'Save section'}
              </button>
            </div>
            <label>Summary</label>
            <textarea rows={5} value={bundle.summary} onChange={(e) => setBundle({ ...bundle, summary: e.target.value })} />

            <div className="grid-2">
              <div>
                <label>Contact type</label>
                <select value={bundle.crm.contact_type} onChange={(e) => setBundle({ ...bundle, crm: { ...bundle.crm, contact_type: e.target.value } })}>
                  <option value="existing">Existing</option>
                  <option value="new">New</option>
                </select>
              </div>
              <div>
                <label>Follow-up date</label>
                <input type="date" value={bundle.crm.follow_up_date || ''} onChange={(e) => setBundle({ ...bundle, crm: { ...bundle.crm, follow_up_date: e.target.value || null } })} />
              </div>
            </div>

            <label>Company</label>
            <input value={bundle.crm.company} onChange={(e) => setBundle({ ...bundle, crm: { ...bundle.crm, company: e.target.value } })} />
            <label>Contact name</label>
            <input value={bundle.crm.contact_name} onChange={(e) => setBundle({ ...bundle, crm: { ...bundle.crm, contact_name: e.target.value } })} />
            <label>Contact email</label>
            <input value={bundle.crm.contact_email} onChange={(e) => setBundle({ ...bundle, crm: { ...bundle.crm, contact_email: e.target.value } })} />
            <label>Recommended services / packages</label>
            <textarea rows={3} value={bundle.crm.recommended_services || ''} onChange={(e) => setBundle({ ...bundle, crm: { ...bundle.crm, recommended_services: e.target.value } })} />
            <label>Lead progression notes</label>
            <textarea rows={4} value={bundle.crm.update_notes} onChange={(e) => setBundle({ ...bundle, crm: { ...bundle.crm, update_notes: e.target.value } })} />
            <label>Next step</label>
            <textarea rows={2} value={bundle.crm.next_step} onChange={(e) => setBundle({ ...bundle, crm: { ...bundle.crm, next_step: e.target.value } })} />
          </section>

          <section className="panel">
            <h2>Participant tasks</h2>
            <div className="tasks">
            {bundle.participant_tasks.map((t, idx) => (
              <div key={idx} className="task">
                  <input type="checkbox" checked={t.is_checked} onChange={(e) => updateParticipantTask(idx, { is_checked: e.target.checked })} />
                  <input value={t.task_text} onChange={(e) => updateParticipantTask(idx, { task_text: e.target.value })} />
              </div>
            ))}
            </div>
            <button className="btn-secondary" onClick={() => setBundle({ ...bundle, participant_tasks: [...bundle.participant_tasks, { task_text: '', is_checked: false }] })}>Add participant task</button>
          </section>

          <section className="panel">
            <div className="panel-head">
              <h2>My tasks</h2>
              <button className="btn-secondary" onClick={saveTasks} disabled={savingState === 'tasks'}>
                {savingState === 'tasks' ? 'Saving...' : 'Save my tasks'}
              </button>
            </div>
            <div className="tasks">
            {bundle.my_tasks.map((t, idx) => (
              <div key={idx} className="task">
                  <input type="checkbox" checked={t.is_checked} onChange={(e) => updateTask(idx, { is_checked: e.target.checked })} />
                  <input value={t.task_text} onChange={(e) => updateTask(idx, { task_text: e.target.value })} />
              </div>
            ))}
            </div>
            <button className="btn-secondary" onClick={() => setBundle({ ...bundle, my_tasks: [...bundle.my_tasks, { task_text: '', is_checked: false }] })}>Add my task</button>
          </section>

          <section className="panel">
            <div className="panel-head">
              <h2>Email templates</h2>
              <button className="btn-secondary" onClick={saveEmail} disabled={savingState === 'email'}>
                {savingState === 'email' ? 'Saving...' : 'Save email'}
              </button>
            </div>
            <label>Template</label>
            <select value={activeTemplate} onChange={(e) => setActiveTemplate(e.target.value)}>
              {templateKeys.map((key) => <option key={key} value={key}>{key}</option>)}
            </select>
            {currentEmail ? (
              <>
                <label>Subject</label>
                <input value={currentEmail.subject} onChange={(e) => updateEmailField(activeTemplate, 'subject', e.target.value)} />
                <label>Body</label>
                <textarea rows={7} value={currentEmail.body} onChange={(e) => updateEmailField(activeTemplate, 'body', e.target.value)} />
              </>
            ) : (
              <p className="muted">No generated email for this template key yet.</p>
            )}
          </section>

          <section className="panel">
            <div className="panel-head">
              <h2>Approve bundle</h2>
              <button onClick={approve} disabled={savingState === 'approve'}>
                {savingState === 'approve' ? 'Approving...' : 'Approve'}
              </button>
            </div>
            <p className="muted">Marks this meeting as approved and attempts owner notification email.</p>
          </section>
        </>
      )}
    </div>
  )
}
