import React, { useEffect, useState } from 'react'
import { ShieldCheck, XCircle, FileText, UserPlus, Users, CheckCircle, Clock, ExternalLink } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { authAPI } from '../services/api'

export default function AdminApprovals() {
  const { user } = useAuth()
  const [requests, setRequests] = useState([])
  const [roleRequests, setRoleRequests] = useState([])
  const [pendingUsers, setPendingUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const loadData = async () => {
    try {
      setLoading(true)
      setError('')

      // Only load role requests (registration_requests table) - single source of truth
      const roleReqRes = await authAPI.listRoleRequests().catch(() => ({ data: { requests: [] } }))
      const roleReqs = roleReqRes.data?.requests || []

      setRoleRequests(roleReqs)
      setPendingUsers([])  // Deprecated - legacy users
      setRequests([])      // Deprecated - form requests
    } catch (e) {
      setError(e.message || 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const decideRequest = async (id, approved) => {
    try {
      setError('')
      setSuccess('')
      await authAPI.decideRegisterRequest(id, approved)
      setSuccess(approved ? 'Request approved successfully!' : 'Request rejected')
      await loadData()
    } catch (e) {
      const errorMsg = e.response?.data?.detail || e.response?.data?.message || e.message || 'Failed to submit decision'
      setError(errorMsg)
    }
  }

  const assignRole = async (userId, role) => {
    try {
      setError('')
      setSuccess('')
      await authAPI.assignRoleToPendingUser(userId, role)
      setSuccess(`Role ${role} assigned successfully!`)
      await loadData()
    } catch (e) {
      const errorMsg = e.response?.data?.detail || e.response?.data?.message || e.message || 'Failed to assign role'
      setError(errorMsg)
    }
  }

  const rejectUser = async (userId) => {
    try {
      setError('')
      setSuccess('')
      await authAPI.rejectPendingUser(userId)
      setSuccess('User rejected and removed')
      await loadData()
    } catch (e) {
      const errorMsg = e.response?.data?.detail || e.response?.data?.message || e.message || 'Failed to reject user'
      setError(errorMsg)
    }
  }

  // Approve role request using the requested_role directly
  const approveRoleRequest = async (requestId, requestedRole) => {
    try {
      setError('')
      setSuccess('')
      await authAPI.approveRoleRequest(requestId, requestedRole)
      setSuccess(`Request approved! User assigned as ${requestedRole}`)
      await loadData()
    } catch (e) {
      const errorMsg = e.response?.data?.detail || e.response?.data?.message || e.message || 'Failed to approve request'
      setError(errorMsg)
    }
  }

  const rejectRoleRequest = async (requestId) => {
    if (!confirm('Are you sure you want to reject this request?')) return
    try {
      setError('')
      setSuccess('')
      await authAPI.rejectRoleRequest(requestId, 'Request rejected by admin')
      setSuccess('Request rejected')
      await loadData()
    } catch (e) {
      const errorMsg = e.response?.data?.detail || e.response?.data?.message || e.message || 'Failed to reject request'
      setError(errorMsg)
    }
  }

  useEffect(() => { loadData() }, [])

  const pendingRequestsCount = requests.filter(r => r.status === 'PENDING').length
  const pendingUsersCount = pendingUsers.length
  const pendingRoleRequestsCount = roleRequests.filter(r => r.status === 'PENDING').length
  const totalPending = pendingRequestsCount + pendingUsersCount + pendingRoleRequestsCount

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <ShieldCheck className="w-7 h-7 text-indigo-600" />
              <div>
                <h2 className="text-xl font-bold">User Approvals</h2>
                <p className="text-sm text-gray-500">Approve or reject registration requests</p>
              </div>
            </div>
            {totalPending > 0 && (
              <span className="bg-red-100 text-red-700 px-4 py-2 rounded-full font-semibold">
                {totalPending} Pending
              </span>
            )}
          </div>
        </div>

        {/* Alerts */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 flex justify-between items-center">
            {error}
            <button onClick={() => setError('')} className="text-red-500 hover:text-red-700 text-xl">&times;</button>
          </div>
        )}
        {success && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-4 flex justify-between items-center">
            {success}
            <button onClick={() => setSuccess('')} className="text-green-500 hover:text-green-700 text-xl">&times;</button>
          </div>
        )}

        {loading ? (
          <div className="text-center text-gray-600 py-8">Loading...</div>
        ) : (
          <>
            {/* Role Selection Requests (Google OAuth users) */}
            {pendingRoleRequestsCount > 0 && (
              <div className="mb-8">
                <div className="flex items-center gap-2 mb-4">
                  <Clock className="w-5 h-5 text-purple-600" />
                  <h3 className="text-lg font-semibold">Pending Approvals ({pendingRoleRequestsCount})</h3>
                </div>
                <div className="grid grid-cols-1 gap-4">
                  {roleRequests.filter(req => req.status === 'PENDING').map(req => (
                    <div key={req.id} className="bg-white rounded-xl shadow-sm p-5 border-l-4 border-purple-400">
                      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                        <div className="flex-1">
                          {/* User Info */}
                          <div className="flex items-center gap-3 flex-wrap">
                            <span className="text-lg font-semibold text-gray-900">
                              {req.full_name || req.email?.split('@')[0]}
                            </span>
                            <span className={`text-sm px-3 py-1 rounded-full font-medium ${req.role_requested === 'DOCTOR'
                              ? 'bg-blue-100 text-blue-700'
                              : 'bg-green-100 text-green-700'
                              }`}>
                              {req.role_requested === 'DOCTOR' ? '👨‍⚕️ Doctor' : '👩‍⚕️ ASHA Worker'}
                            </span>
                          </div>
                          <div className="text-sm text-gray-600 mt-1">{req.email}</div>
                          <div className="text-xs text-gray-400 mt-1">
                            Applied: {new Date(req.created_at).toLocaleString()}
                          </div>

                          {/* Doctor Certificate Link */}
                          {req.role_requested === 'DOCTOR' && (
                            <div className="mt-3">
                              {req.degree_cert_url ? (
                                <a
                                  href={req.degree_cert_url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors text-sm font-medium"
                                >
                                  <FileText className="w-4 h-4" />
                                  View Registration Certificate
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                              ) : (
                                <span className="inline-flex items-center gap-2 text-sm text-yellow-600 bg-yellow-50 px-3 py-2 rounded-lg">
                                  ⚠️ No certificate uploaded
                                </span>
                              )}
                            </div>
                          )}
                        </div>

                        {/* Action Buttons - No role selection, just approve/decline */}
                        <div className="flex items-center gap-3 flex-shrink-0">
                          <button
                            onClick={() => approveRoleRequest(req.id, req.role_requested)}
                            className="px-5 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2 font-medium transition-colors"
                          >
                            <CheckCircle className="w-4 h-4" />
                            Approve
                          </button>
                          <button
                            onClick={() => rejectRoleRequest(req.id)}
                            className="px-5 py-2.5 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center gap-2 font-medium transition-colors"
                          >
                            <XCircle className="w-4 h-4" />
                            Decline
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Legacy Pending OAuth Users (if any exist) */}
            {pendingUsersCount > 0 && (
              <div className="mb-8">
                <div className="flex items-center gap-2 mb-4">
                  <Users className="w-5 h-5 text-yellow-600" />
                  <h3 className="text-lg font-semibold">Legacy Pending Users ({pendingUsersCount})</h3>
                </div>
                <div className="grid grid-cols-1 gap-4">
                  {pendingUsers.map(user => (
                    <div key={user.id} className="bg-white rounded-xl shadow-sm p-5 border-l-4 border-yellow-400">
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="font-semibold text-gray-900">{user.full_name || 'No Name'}</div>
                          <div className="text-sm text-gray-600">{user.email}</div>
                          <div className="text-xs text-gray-400 mt-1">
                            {new Date(user.created_at).toLocaleDateString()}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <select
                            id={`role-${user.id}`}
                            className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                            defaultValue=""
                          >
                            <option value="" disabled>Select Role</option>
                            <option value="DOCTOR">Doctor</option>
                            <option value="ASHA_WORKER">ASHA Worker</option>
                          </select>
                          <button
                            onClick={() => {
                              const role = document.getElementById(`role-${user.id}`).value
                              if (role) assignRole(user.id, role)
                              else setError('Please select a role first')
                            }}
                            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => rejectUser(user.id)}
                            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm"
                          >
                            Reject
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Form Registration Requests (if any) */}
            {pendingRequestsCount > 0 && (
              <div className="mb-8">
                <div className="flex items-center gap-2 mb-4">
                  <UserPlus className="w-5 h-5 text-indigo-600" />
                  <h3 className="text-lg font-semibold">Form Registrations ({pendingRequestsCount})</h3>
                </div>
                <div className="grid grid-cols-1 gap-4">
                  {requests.filter(req => req.status === 'PENDING').map(req => (
                    <div key={req.id} className="bg-white rounded-xl shadow-sm p-5 border-l-4 border-indigo-400">
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="font-semibold text-gray-900">
                            {req.full_name}
                            <span className="ml-2 text-xs px-2 py-1 rounded bg-indigo-100 text-indigo-700">{req.role_requested}</span>
                          </div>
                          <div className="text-sm text-gray-600">{req.email}</div>
                          {req.role_requested === 'DOCTOR' && req.degree_cert_url && (
                            <a
                              href={req.degree_cert_url}
                              target="_blank"
                              rel="noreferrer"
                              className="mt-2 inline-flex items-center gap-2 text-indigo-600 hover:text-indigo-800 text-sm"
                            >
                              <FileText className="w-4 h-4" /> View Certificate
                            </a>
                          )}
                        </div>
                        <div className="flex items-center gap-3">
                          <button
                            onClick={() => decideRequest(req.id, true)}
                            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => decideRequest(req.id, false)}
                            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                          >
                            Decline
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* No pending items */}
            {totalPending === 0 && (
              <div className="text-center py-12 bg-white rounded-xl shadow-sm">
                <ShieldCheck className="w-12 h-12 text-green-500 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900">All Caught Up!</h3>
                <p className="text-gray-500">No pending approvals at this time.</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
