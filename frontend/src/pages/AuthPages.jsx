// SignupPage.jsx
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { Input, Button } from '@/components/shared/UI'
import toast from 'react-hot-toast'

export function SignupPage() {
  const { signUp } = useAuth()
  const navigate   = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.name || !form.email || !form.password) { toast.error('Please fill in all fields.'); return }
    if (form.password.length < 8) { toast.error('Password must be at least 8 characters.'); return }
    setLoading(true)
    try {
      await signUp(form)
      toast.success('Account created! Please check your email to verify.')
      navigate('/login')
    } catch (err) {
      toast.error(err.message || 'Failed to create account.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface-900 flex items-center justify-center p-6"
      style={{ backgroundImage: 'radial-gradient(ellipse at 50% 0%, rgba(16,185,129,.1) 0%, transparent 60%)' }}>
      <div className="fixed top-6 left-7 flex items-center gap-2.5">
        <div className="w-9 h-9 rounded-[10px] bg-brand-gradient flex items-center justify-center text-lg">💰</div>
        <span className="font-display font-bold text-lg text-text-primary tracking-tight">WealthLens</span>
      </div>
      <div className="w-full max-w-[420px] animate-fade-in">
        <div className="bg-surface-700 border border-surface-600 rounded-[20px] p-10 shadow-2xl">
          <div className="text-center mb-8">
            <h1 className="font-display font-bold text-2xl text-text-primary tracking-tight">Get started</h1>
            <p className="text-text-secondary text-sm mt-2">Create your free WealthLens account</p>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input label="Full Name"  type="text"  value={form.name}     onChange={set('name')}     placeholder="Rahul Sharma" />
            <Input label="Email"      type="email" value={form.email}    onChange={set('email')}    placeholder="you@example.com" />
            <Input label="Password"  type="password" value={form.password} onChange={set('password')} placeholder="Min. 8 characters" />
            <Button type="submit" size="lg" className="w-full mt-2" disabled={loading}>
              {loading ? 'Creating account…' : 'Create Account →'}
            </Button>
          </form>
          <p className="text-center text-text-secondary text-sm mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-brand-green font-medium hover:underline">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export function ForgotPage() {
  const { resetPassword } = useAuth()
  const [email, setEmail] = useState('')
  const [sent,    setSent]    = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!email) return
    setLoading(true)
    try {
      await resetPassword(email)
      setSent(true)
    } catch (err) {
      toast.error(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface-900 flex items-center justify-center p-6">
      <div className="w-full max-w-[420px] animate-fade-in">
        <div className="bg-surface-700 border border-surface-600 rounded-[20px] p-10 shadow-2xl">
          {sent ? (
            <div className="text-center">
              <div className="text-5xl mb-4">📬</div>
              <h2 className="font-display font-bold text-xl text-text-primary mb-2">Check your email</h2>
              <p className="text-text-secondary text-sm">We sent a password reset link to <strong>{email}</strong></p>
              <Link to="/login" className="text-brand-green text-sm font-medium mt-6 block hover:underline">← Back to login</Link>
            </div>
          ) : (
            <>
              <div className="text-center mb-8">
                <h1 className="font-display font-bold text-2xl text-text-primary tracking-tight">Reset password</h1>
                <p className="text-text-secondary text-sm mt-2">We'll send you a reset link</p>
              </div>
              <form onSubmit={handleSubmit} className="space-y-4">
                <Input label="Email" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" />
                <Button type="submit" size="lg" className="w-full" disabled={loading}>
                  {loading ? 'Sending…' : 'Send Reset Link'}
                </Button>
              </form>
              <Link to="/login" className="block text-center text-text-secondary text-sm mt-6 hover:text-text-primary">← Back to login</Link>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
