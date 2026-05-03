import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

export default function LoginPage() {
  const navigate = useNavigate()
  const [isRegister, setIsRegister] = useState(false)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const modeCopy = useMemo(() => {
    if (isRegister) {
      return {
        eyebrow: 'Create account',
        title: 'Start your workspace',
        subtitle: 'Create an account to generate polished post-meeting deliverables in minutes.',
        cta: 'Create account',
        switchLabel: 'Already have an account?',
        switchAction: 'Sign in',
      }
    }
    return {
      eyebrow: 'Welcome back',
      title: 'Sign in to continue',
      subtitle: 'Access your meeting library, outputs, tasks, and follow-up emails.',
      cta: 'Sign in',
      switchLabel: 'Need an account?',
      switchAction: 'Create one',
    }
  }, [isRegister])

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setIsSubmitting(true)
    try {
      const endpoint = isRegister ? '/auth/register' : '/auth/login'
      const payload = isRegister ? { name, email, password } : { email, password }
      const res = await api.post(endpoint, payload)
      localStorage.setItem('token', res.data.access_token)
      localStorage.setItem('user_email', email.trim().toLowerCase())
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Auth failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-shell">
        <section className="auth-marketing">
          <span className="chip">Meeting Bundle</span>
          <h1>From meeting notes to clear next steps.</h1>
          <p>
            Capture meeting notes once, then generate a summary, CRM update, tasks, and outreach drafts.
            Built to make every customer conversation executable.
          </p>
          <div className="auth-grid">
            <div className="auth-kpi">
              <strong>1 place</strong>
              <span>for meetings, CRM notes, and action lists</span>
            </div>
            <div className="auth-kpi">
              <strong>Email templates</strong>
              <span>for fast post-meeting follow-up</span>
            </div>
            <div className="auth-kpi">
              <strong>Editable outputs</strong>
              <span>before approval and send-off</span>
            </div>
          </div>
        </section>

        <section className="auth-card">
          <p className="eyebrow">{modeCopy.eyebrow}</p>
          <h2>{modeCopy.title}</h2>
          <p className="muted">{modeCopy.subtitle}</p>

          <form onSubmit={submit}>
            {isRegister && (
              <>
                <label>Name</label>
                <input value={name} onChange={(e) => setName(e.target.value)} required autoComplete="name" />
              </>
            )}
            <label>Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
            <label>Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete={isRegister ? 'new-password' : 'current-password'} />
            {error && <div className="banner error">{error}</div>}
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Please wait...' : modeCopy.cta}
            </button>
          </form>

          <div className="auth-switch">
            <span>{modeCopy.switchLabel}</span>
            <button type="button" className="btn-secondary" onClick={() => setIsRegister(!isRegister)}>
              {modeCopy.switchAction}
            </button>
          </div>
        </section>
      </div>
    </div>
  )
}
