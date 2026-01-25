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
    ? 'bg-red-600'
    : user?.role === 'DOCTOR'
      ? 'bg-green-600'
      : 'bg-purple-600'

  // Only show toggle on ASHA/Doctor dashboard pages
  const showToggle = isAuthenticated &&
    (user?.role === 'ASHA_WORKER' || user?.role === 'DOCTOR') &&
    (location.pathname === '/asha/dashboard' || location.pathname === '/doctor' ||
      location.pathname === '/asha' || location.pathname === '/doctor/dashboard')

  return (
    <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white shadow-xl">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <Heart className="w-8 h-8 fill-current" />
            <div>
              <h1 className="text-2xl font-bold">Aanchal AI</h1>
              <p className="text-blue-100 text-xs">Maternal Health Guardian System</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* View Toggle - Only on dashboard pages */}
            {showToggle && (
              <div className="flex bg-white/20 rounded-lg p-1 mr-4">
                <button
                  onClick={() => setCurrentView('pregnancy')}
                  className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${currentView === 'pregnancy'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-white/80 hover:text-white'
                    }`}
                >
                  🤰 Pregnancy
                </button>
                <button
                  onClick={() => setCurrentView('postnatal')}
                  className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${currentView === 'postnatal'
                    ? 'bg-white text-green-600 shadow-sm'
                    : 'text-white/80 hover:text-white'
                    }`}
                >
                  🍼 Postnatal
                </button>
              </div>
            )}

            <Link to="/" className="text-white/90 hover:text-white">Home</Link>

            {/* Doctor link - visible ONLY to doctors */}
            {user?.role === 'DOCTOR' && (
              <Link to="/doctor" className="text-white/90 hover:text-white">Doctor Portal</Link>
            )}

            {/* ASHA link - visible ONLY to ASHA workers */}
            {user?.role === 'ASHA_WORKER' && (
              <Link to="/asha" className="text-white/90 hover:text-white">ASHA Portal</Link>
            )}

            {/* Admin links - visible ONLY to admin */}
            {user?.role === 'ADMIN' && (
              <>
                <Link to="/admin" className="text-white/90 hover:text-white font-medium">Admin</Link>
                <Link to="/admin/approvals" className="text-white/90 hover:text-white">Approvals</Link>
              </>
            )}

            {isAuthenticated ? (
              <div className="flex items-center gap-3">
                <span className={`px-2 py-1 rounded text-xs ${roleColor}`}>{user?.role}</span>
                <span className="text-white/90 text-sm">{user?.full_name || user?.email}</span>
                <button
                  onClick={handleSignOut}
                  className="px-3 py-2 bg-white/20 hover:bg-white/30 rounded-lg text-sm"
                >
                  Sign Out
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <Link to="/auth/login" className="px-3 py-2 bg-white/20 hover:bg-white/30 rounded-lg text-sm">Login</Link>
                <Link to="/auth/signup" className="px-3 py-2 bg-white/20 hover:bg-white/30 rounded-lg text-sm">Signup</Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
