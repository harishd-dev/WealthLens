import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { Input, Button } from '@/components/shared/UI'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const { signIn } = useAuth()
  const navigate   = useNavigate()
  const [form, setForm] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [showPw,  setShowPw]  = useState(false)

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.email || !form.password) { toast.error('Please fill in all fields.'); return }
    setLoading(true)
    try {
      await signIn(form)
      navigate('/dashboard')
    } catch (err) {
      toast.error(err.message || 'Invalid email or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface-900 flex items-center justify-center p-6"
      style={{ backgroundImage: 'radial-gradient(ellipse at 50% 0%, rgba(16,185,129,.1) 0%, transparent 60%)' }}>

      {/* Logo */}
      <div className="fixed top-6 left-7 flex items-center gap-2.5">
        <div className="w-9 h-9 rounded-[10px] bg-brand-gradient flex items-center justify-center text-lg">💰</div>
        <span className="font-display font-bold text-lg text-text-primary tracking-tight">WealthLens</span>
      </div>

      <div className="w-full max-w-[420px] animate-fade-in">
        <div className="bg-surface-700 border border-surface-600 rounded-[20px] p-10 shadow-2xl">
          <div className="text-center mb-8">
            <h1 className="font-display font-bold text-2xl text-text-primary tracking-tight">Welcome back</h1>
            <p className="text-text-secondary text-sm mt-2">Sign in to your account</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input label="Email" type="email" value={form.email}
              onChange={set('email')} placeholder="you@example.com" />

            <div>
              <div className="relative">
                <Input label="Password" type={showPw ? 'text' : 'password'}
                  value={form.password} onChange={set('password')} placeholder="••••••••" />
                <button type="button" onClick={() => setShowPw(s => !s)}
                  className="absolute right-3 top-7 text-text-secondary text-sm">
                  {showPw ? '🙈' : '👁'}
                </button>
              </div>
              <div className="text-right mt-1.5">
                <Link to="/forgot" className="text-brand-green text-xs hover:underline">Forgot password?</Link>
              </div>
            </div>

            <Button type="submit" size="lg" className="w-full mt-2" disabled={loading}>
              {loading ? 'Signing in…' : 'Sign In →'}
            </Button>
          </form>

          <p className="text-center text-text-secondary text-sm mt-6">
            Don't have an account?{' '}
            <Link to="/signup" className="text-brand-green font-medium hover:underline">Sign up</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
