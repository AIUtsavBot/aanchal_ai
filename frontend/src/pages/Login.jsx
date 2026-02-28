import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const Login = () => {
  const navigate = useNavigate()
  const { signIn, signInWithGoogle } = useAuth()
  const [formData, setFormData] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
    setError('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    const timeout = setTimeout(() => {
      setError('Connection is taking longer than usual. The server might be waking up (Cold Start). Please wait...')
    }, 5000)
    try {
      const result = await signIn(formData.email, formData.password)
      clearTimeout(timeout)
      if (result.user.role === 'ADMIN') navigate('/admin/dashboard')
      else if (result.user.role === 'DOCTOR') navigate('/doctor/dashboard')
      else if (result.user.role === 'ASHA_WORKER') navigate('/asha/dashboard')
      else navigate('/dashboard')
    } catch (err) {
      clearTimeout(timeout)
      setError(err.message || 'Failed to sign in')
    } finally { setLoading(false) }
  }

  const handleGoogleSignIn = async () => {
    try { setLoading(true); await signInWithGoogle() }
    catch (err) { setError(err.message || 'Failed to sign in with Google'); setLoading(false) }
  }

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent mb-2">🤰 Aanchal AI</h1>
          <h2 className="text-2xl font-bold text-slate-800">Welcome Back</h2>
          <p className="mt-2 text-sm text-slate-500">Sign in to your account</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl">{error}</div>
        )}

        <form className="mt-8 space-y-6 glass-card-strong p-8 rounded-2xl" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-600 mb-1">Email Address</label>
              <input id="email" name="email" type="email" required value={formData.email} onChange={handleChange}
                className="glass-input w-full rounded-xl" placeholder="your@email.com" />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-600 mb-1">Password</label>
              <input id="password" name="password" type="password" required value={formData.password} onChange={handleChange}
                className="glass-input w-full rounded-xl" placeholder="••••••••" />
            </div>
          </div>

          <div className="flex items-center justify-between">
            <Link to="/auth/forgot-password" className="text-sm font-medium text-blue-600 hover:text-blue-500 transition-colors">Forgot your password?</Link>
          </div>

          <button type="submit" disabled={loading} className="glass-btn-primary w-full py-3 rounded-xl text-sm">
            {loading ? 'Signing in...' : 'Sign In'}
          </button>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-blue-200/40"></div></div>
            <div className="relative flex justify-center text-sm">
              <span className="px-3 bg-white/60 backdrop-blur-sm rounded-full text-slate-400 text-xs">Or continue with</span>
            </div>
          </div>

          <button type="button" onClick={handleGoogleSignIn} disabled={loading}
            className="w-full flex items-center justify-center gap-3 py-3 px-4 bg-white/60 border border-blue-200/40 rounded-xl text-sm font-medium text-slate-600 hover:bg-white/80 focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:opacity-50 transition-all backdrop-blur-sm">
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
            </svg>
            Sign in with Google
          </button>

          <div className="text-center mt-4">
            <p className="text-sm text-slate-500">Don't have an account?{' '}
              <Link to="/auth/signup" className="font-medium text-blue-600 hover:text-blue-500 transition-colors">Sign up</Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  )
}

export default Login
