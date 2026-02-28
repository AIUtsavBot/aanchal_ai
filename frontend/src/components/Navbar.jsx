import React from 'react'
import { Heart } from 'lucide-react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useView } from '../contexts/ViewContext'

export default function Navbar() {
  const { user, isAuthenticated, signOut } = useAuth()
  const { currentView, setCurrentView } = useView()
  const navigate = useNavigate()
  const location = useLocation()

  const handleSignOut = async () => {
    await signOut()
    navigate('/auth/login', { replace: true })
  }

  const roleColor = user?.role === 'ADMIN'
    ? 'bg-red-100 text-red-700 border border-red-200'
    : user?.role === 'DOCTOR'
      ? 'bg-emerald-100 text-emerald-700 border border-emerald-200'
      : 'bg-blue-100 text-blue-700 border border-blue-200'

  const showToggle = isAuthenticated &&
    (user?.role === 'ASHA_WORKER' || user?.role === 'DOCTOR') &&
    (location.pathname === '/asha/dashboard' || location.pathname === '/doctor' ||
      location.pathname === '/asha' || location.pathname === '/doctor/dashboard')

  return (
    <nav aria-label="Main Navigation" className="bg-white/60 backdrop-blur-xl border-b border-blue-200/40 text-slate-800">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <Link to="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
            <div className="bg-gradient-to-br from-blue-500 to-cyan-500 p-2 rounded-xl shadow-lg shadow-blue-500/20">
              <Heart className="w-6 h-6 text-white fill-current" />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
                Aanchal AI
              </h1>
              <p className="text-slate-400 text-xs">Maternal & Child Health Guardian</p>
            </div>
          </Link>

          <div className="flex items-center gap-4">
            {showToggle && (
              <div className="flex bg-white/50 backdrop-blur-md border border-blue-200/40 rounded-lg p-1 mr-4">
                <button
                  onClick={() => setCurrentView('pregnancy')}
                  aria-pressed={currentView === 'pregnancy'}
                  className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${currentView === 'pregnancy'
                    ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-md shadow-blue-500/20'
                    : 'text-slate-500 hover:text-slate-700'
                    }`}
                >🤰 Pregnancy</button>
                <button
                  onClick={() => setCurrentView('postnatal')}
                  aria-pressed={currentView === 'postnatal'}
                  className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${currentView === 'postnatal'
                    ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-md shadow-blue-500/20'
                    : 'text-slate-500 hover:text-slate-700'
                    }`}
                >🍼 Postnatal</button>
              </div>
            )}

            <Link to="/" className="text-slate-500 hover:text-blue-600 transition-colors text-sm">Home</Link>
            {user?.role === 'DOCTOR' && <Link to="/doctor" className="text-slate-500 hover:text-blue-600 transition-colors text-sm">Doctor Portal</Link>}
            {user?.role === 'ASHA_WORKER' && <Link to="/asha" className="text-slate-500 hover:text-blue-600 transition-colors text-sm">ASHA Portal</Link>}
            {user?.role === 'ADMIN' && (
              <>
                <Link to="/admin" className="text-slate-500 hover:text-blue-600 transition-colors text-sm font-medium">Admin</Link>
                <Link to="/admin/approvals" className="text-slate-500 hover:text-blue-600 transition-colors text-sm">Approvals</Link>
              </>
            )}

            {isAuthenticated ? (
              <div className="flex items-center gap-3">
                <span className={`px-2.5 py-1 rounded-lg text-xs font-semibold ${roleColor}`}>{user?.role}</span>
                <span className="text-slate-600 text-sm hidden sm:inline">{user?.full_name || user?.email}</span>
                <button onClick={handleSignOut} className="px-3 py-2 bg-white/50 hover:bg-white/80 border border-blue-200/40 rounded-lg text-sm transition-all text-slate-600 hover:text-slate-800">Sign Out</button>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <Link to="/auth/login" className="px-4 py-2 bg-white/50 hover:bg-white/80 border border-blue-200/40 rounded-lg text-sm transition-all text-slate-600">Login</Link>
                <Link to="/auth/signup" className="px-4 py-2 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 rounded-lg text-sm font-semibold text-white shadow-md shadow-blue-500/20 transition-all">Signup</Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
