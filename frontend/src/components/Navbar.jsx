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
      ? 'bg-green-600 text-white'
      : 'bg-teal-600 text-white'

  const showToggle = isAuthenticated &&
    (user?.role === 'ASHA_WORKER' || user?.role === 'DOCTOR') &&
    (location.pathname === '/asha/dashboard' || location.pathname === '/doctor' ||
      location.pathname === '/asha' || location.pathname === '/doctor/dashboard')

  return (
    <nav aria-label="Main Navigation" className="bg-gradient-to-r from-teal-700 to-teal-600 text-white shadow-xl">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <Link to="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
            <div className="bg-white/20 backdrop-blur-sm p-2 rounded-xl shadow-lg shadow-teal-900/20">
              <Heart className="w-6 h-6 text-white fill-current" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">
                Aanchal AI
              </h1>
              <p className="text-teal-100 text-xs">Maternal & Child Health Guardian</p>
            </div>
          </Link>

          <div className="flex items-center gap-4">
            {showToggle && (
              <div className="flex bg-white/15 backdrop-blur-md border border-teal-400/30 rounded-lg p-1 mr-4">
                <button
                  onClick={() => setCurrentView('pregnancy')}
                  aria-pressed={currentView === 'pregnancy'}
                  className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${currentView === 'pregnancy'
                    ? 'bg-white text-teal-700 shadow-md'
                    : 'text-teal-100 hover:text-white'
                    }`}
                >🤰 Pregnancy</button>
                <button
                  onClick={() => setCurrentView('postnatal')}
                  aria-pressed={currentView === 'postnatal'}
                  className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${currentView === 'postnatal'
                    ? 'bg-white text-teal-700 shadow-md'
                    : 'text-teal-100 hover:text-white'
                    }`}
                >🍼 Postnatal</button>
              </div>
            )}

            <Link to="/" className="text-teal-100 hover:text-white transition-colors text-sm">Home</Link>
            {user?.role === 'DOCTOR' && <Link to="/doctor" className="text-teal-100 hover:text-white transition-colors text-sm">Doctor Portal</Link>}
            {user?.role === 'ASHA_WORKER' && <Link to="/asha" className="text-teal-100 hover:text-white transition-colors text-sm">ASHA Portal</Link>}
            {user?.role === 'ADMIN' && (
              <>
                <Link to="/admin" className="text-teal-100 hover:text-white transition-colors text-sm font-medium">Admin</Link>
                <Link to="/admin/approvals" className="text-teal-100 hover:text-white transition-colors text-sm">Approvals</Link>
              </>
            )}

            {isAuthenticated ? (
              <div className="flex items-center gap-3">
                <span className={`px-2.5 py-1 rounded-lg text-xs font-semibold ${roleColor}`}>{user?.role}</span>
                <span className="text-teal-100 text-sm hidden sm:inline">{user?.full_name || user?.email}</span>
                <button onClick={handleSignOut} className="px-3 py-2 bg-white/15 hover:bg-white/25 border border-teal-400/30 rounded-lg text-sm transition-all text-white">Sign Out</button>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <Link to="/auth/login" className="px-4 py-2 bg-white/15 hover:bg-white/25 border border-teal-400/30 rounded-lg text-sm transition-all text-white">Login</Link>
                <Link to="/auth/signup" className="px-4 py-2 bg-white hover:bg-teal-50 rounded-lg text-sm font-semibold text-teal-700 shadow-md transition-all">Signup</Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
