import React, { Suspense } from 'react'
import { useTranslation } from 'react-i18next'
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ViewProvider } from './contexts/ViewContext'
import ProtectedRoute from './components/ProtectedRoute'
import Navbar from './components/Navbar'
import LoadingSpinner from './components/LoadingSpinner'
import Home from './pages/Home.jsx' // Keep Home synchronous for fast LCP

// Lazy Load Pages
const Login = React.lazy(() => import('./pages/Login'))
const Signup = React.lazy(() => import('./pages/Signup'))
const AuthCallback = React.lazy(() => import('./pages/AuthCallback'))
const RiskDashboard = React.lazy(() => import('./pages/RiskDashboard'))
const DoctorDashboard = React.lazy(() => import('./pages/DoctorDashboard.jsx'))
const ASHAInterface = React.lazy(() => import('./pages/ASHAInterface.jsx'))
const AdminDashboard = React.lazy(() => import('./pages/AdminDashboard'))
const AdminApprovals = React.lazy(() => import('./pages/AdminApprovals'))

import ErrorBoundary from './components/ErrorBoundary'

export default function App() {
  const { t, i18n } = useTranslation()

  return (
    <>
      <div className="orb-3"></div>
      <AuthProvider>
        <ViewProvider>
          <ErrorBoundary>
            <BrowserRouter>
              <Navbar />
              <Suspense fallback={<LoadingSpinner />}>
                <Routes>
                  {/* Public Routes */}
                  <Route path="/auth/login" element={<Login />} />
                  <Route path="/auth/signup" element={<Signup />} />
                  <Route path="/auth/callback" element={<AuthCallback />} />

                  {/* Public Homepage */}
                  <Route path="/" element={<Home />} />
                  {/* Protected Routes */}
                  <Route
                    path="/dashboard"
                    element={
                      <ProtectedRoute allowedRoles={['ADMIN']}>
                        <RiskDashboard />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/doctor"
                    element={
                      <ProtectedRoute allowedRoles={['DOCTOR', 'ADMIN']}>
                        <DoctorDashboard />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/asha"
                    element={
                      <ProtectedRoute allowedRoles={['ASHA_WORKER', 'ADMIN']}>
                        <ASHAInterface />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/admin"
                    element={
                      <ProtectedRoute allowedRoles={['ADMIN']}>
                        <AdminDashboard />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/admin/dashboard"
                    element={
                      <ProtectedRoute allowedRoles={['ADMIN']}>
                        <AdminDashboard />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/admin/approvals"
                    element={
                      <ProtectedRoute allowedRoles={['ADMIN']}>
                        <AdminApprovals />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/doctor/dashboard"
                    element={
                      <ProtectedRoute allowedRoles={['DOCTOR', 'ADMIN']}>
                        <DoctorDashboard />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/asha/dashboard"
                    element={
                      <ProtectedRoute allowedRoles={['ASHA_WORKER', 'DOCTOR', 'ADMIN']}>
                        <ASHAInterface />
                      </ProtectedRoute>
                    }
                  />
                </Routes>
              </Suspense>
            </BrowserRouter>
          </ErrorBoundary>
        </ViewProvider>
      </AuthProvider>
    </>
  )
}
