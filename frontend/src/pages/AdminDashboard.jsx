import React, { useEffect, useState, useCallback } from 'react'
import { Shield, Users, UserCog, Baby, Edit2, Check, X, RefreshCw, Search, ChevronDown, ChevronUp, Save, Trash2, FileText, ExternalLink } from 'lucide-react'
import { Link } from 'react-router-dom'
import { adminAPI } from '../services/api'

export default function AdminDashboard() {
  const [stats, setStats] = useState(null)
  const [doctors, setDoctors] = useState([])
  const [ashaWorkers, setAshaWorkers] = useState([])
  const [mothers, setMothers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [activeTab, setActiveTab] = useState('overview')
  const [searchTerm, setSearchTerm] = useState('')

  // For editing doctors/asha
  const [editingId, setEditingId] = useState(null)
  const [editData, setEditData] = useState({})

  // For tracking pending assignment changes
  const [pendingChanges, setPendingChanges] = useState({}) // { motherId: { doctor_id?, asha_worker_id? } }
  const [saving, setSaving] = useState(false)

  const loadData = useCallback(async () => {
    try {
      setLoading(true)
      setError('')

      // OPTIMIZED: Try combined endpoint first (1 API call instead of 4)
      try {
        const fullRes = await adminAPI.getFull()
        if (fullRes.data?.data) {
          console.log('Admin full data loaded:', fullRes.data.cached ? '(cached)' : '(fresh)')
          const fullData = fullRes.data.data
          setStats(fullData.stats || {})
          setDoctors(fullData.doctors || [])
          setAshaWorkers(fullData.asha_workers || [])
          setMothers(fullData.mothers || [])
          setPendingChanges({})
          return
        }
      } catch (combinedError) {
        console.log('Combined endpoint not available, falling back to parallel calls:', combinedError.message)
      }

      // FALLBACK: Parallel fetch (still better than sequential)
      const [statsRes, doctorsRes, ashaRes, mothersRes] = await Promise.all([
        adminAPI.getStats().catch(() => ({ data: { stats: {} } })),
        adminAPI.getDoctors().catch(() => ({ data: { doctors: [] } })),
        adminAPI.getAshaWorkers().catch(() => ({ data: { asha_workers: [] } })),
        adminAPI.getMothers().catch(() => ({ data: { mothers: [] } }))
      ])

      setStats(statsRes.data?.stats || {})
      setDoctors(doctorsRes.data?.doctors || [])
      setAshaWorkers(ashaRes.data?.asha_workers || [])
      setMothers(mothersRes.data?.mothers || [])
      setPendingChanges({}) // Clear pending changes on reload
    } catch (e) {
      setError(e.message || 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }, [])


  useEffect(() => { loadData() }, [loadData])

  // Clear success message after 3 seconds
  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(''), 3000)
      return () => clearTimeout(timer)
    }
  }, [success])

  // Track assignment changes locally (don't save immediately)
  const handleAssignmentChange = (motherId, type, value) => {
    console.log('Assignment change:', { motherId, type, value })
    setPendingChanges(prev => ({
      ...prev,
      [motherId]: {
        ...(prev[motherId] || {}),
        [type === 'doctor' ? 'doctor_id' : 'asha_worker_id']: value ? parseInt(value) : null
      }
    }))
  }

  // Save all pending changes
  const saveAllChanges = async () => {
    console.log('🔄 Saving changes:', pendingChanges)
    const changeCount = Object.keys(pendingChanges).length
    if (changeCount === 0) {
      setError('No changes to save')
      return
    }

    setSaving(true)
    let successCount = 0
    let errorCount = 0

    try {
      for (const [motherId, changes] of Object.entries(pendingChanges)) {
        console.log(`📝 Processing mother ${motherId}:`, changes)
        try {
          // motherId is a UUID string - pass as-is
          if ('doctor_id' in changes) {
            console.log(`  → Assigning doctor ${changes.doctor_id}`)
            await adminAPI.assignMotherToDoctor(motherId, changes.doctor_id)
            console.log(`  ✅ Doctor assigned`)
          }
          if ('asha_worker_id' in changes) {
            console.log(`  → Assigning ASHA ${changes.asha_worker_id}`)
            await adminAPI.assignMotherToAsha(motherId, changes.asha_worker_id)
            console.log(`  ✅ ASHA assigned`)
          }
          successCount++
        } catch (e) {
          console.error(`❌ Failed to update mother ${motherId}:`, e)
          errorCount++
        }
      }

      console.log(`✅ Done: ${successCount} success, ${errorCount} errors`)

      if (successCount > 0) {
        setSuccess(`Successfully updated ${successCount} assignment(s)!`)
      }
      if (errorCount > 0) {
        setError(`Failed to update ${errorCount} assignment(s)`)
      }

      // Reload data
      await loadData()
    } finally {
      setSaving(false)
    }
  }

  // Get effective value (pending or original)
  const getEffectiveValue = (mother, field) => {
    if (pendingChanges[mother.id] && field in pendingChanges[mother.id]) {
      return pendingChanges[mother.id][field]
    }
    return mother[field]
  }

  // Edit doctor/asha
  const handleEditDoctor = (doctor) => {
    setEditingId(`doctor-${doctor.id}`)
    setEditData({
      name: doctor.name,
      phone: doctor.phone || '',
      assigned_area: doctor.assigned_area || '',
      is_active: doctor.is_active
    })
  }

  const handleEditAsha = (asha) => {
    setEditingId(`asha-${asha.id}`)
    setEditData({
      name: asha.name,
      phone: asha.phone || '',
      assigned_area: asha.assigned_area || '',
      is_active: asha.is_active
    })
  }

  const saveDoctor = async (id) => {
    try {
      await adminAPI.updateDoctor(id, editData)
      setSuccess('Doctor updated successfully')
      setEditingId(null)
      await loadData()
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to update doctor')
    }
  }

  const saveAsha = async (id) => {
    try {
      await adminAPI.updateAshaWorker(id, editData)
      setSuccess('ASHA Worker updated successfully')
      setEditingId(null)
      await loadData()
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to update ASHA worker')
    }
  }

  const deleteDoctor = async (id, name) => {
    if (!window.confirm(`Are you sure you want to delete Dr. ${name}? This will unassign all their patients.`)) {
      return
    }
    try {
      await adminAPI.deleteDoctor(id)
      setSuccess('Doctor deleted successfully')
      await loadData()
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to delete doctor')
    }
  }

  const deleteAsha = async (id, name) => {
    if (!window.confirm(`Are you sure you want to delete ${name}? This will unassign all their patients.`)) {
      return
    }
    try {
      await adminAPI.deleteAshaWorker(id)
      setSuccess('ASHA Worker deleted successfully')
      await loadData()
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to delete ASHA worker')
    }
  }

  // Filter mothers based on search
  const filteredMothers = mothers.filter(m =>
    m.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    m.phone?.includes(searchTerm) ||
    m.location?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const pendingChangesCount = Object.keys(pendingChanges).length

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
          <p className="mt-4 text-gray-600">Loading admin dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <div className="bg-indigo-600 p-3 rounded-lg">
              <Shield className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
              <p className="text-gray-500">Manage system users and assignments</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/admin/approvals"
              className="flex items-center gap-2 px-4 py-2 bg-yellow-100 text-yellow-800 rounded-lg hover:bg-yellow-200"
            >
              <Shield className="w-4 h-4" />
              Approvals ({stats?.pending_approvals || 0})
            </Link>
            <button
              onClick={loadData}
              className="flex items-center gap-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          </div>
        </div>

        {/* Alerts */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 flex justify-between">
            {error}
            <button onClick={() => setError('')}>&times;</button>
          </div>
        )}
        {success && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-4 flex justify-between items-center">
            <span>✅ {success}</span>
            <button onClick={() => setSuccess('')}>&times;</button>
          </div>
        )}

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-xl shadow-sm p-5 border-l-4 border-pink-500">
            <p className="text-sm text-gray-500">Total Mothers</p>
            <p className="text-3xl font-bold text-gray-900">{stats?.total_mothers ?? '-'}</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-5 border-l-4 border-indigo-500">
            <p className="text-sm text-gray-500">Doctors</p>
            <p className="text-3xl font-bold text-gray-900">{stats?.total_doctors ?? '-'}</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-5 border-l-4 border-purple-500">
            <p className="text-sm text-gray-500">ASHA Workers</p>
            <p className="text-3xl font-bold text-gray-900">{stats?.total_asha_workers ?? '-'}</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-5 border-l-4 border-green-500">
            <p className="text-sm text-gray-500">Fully Assigned</p>
            <p className="text-3xl font-bold text-gray-900">
              {mothers.filter(m => m.doctor_id && m.asha_worker_id).length}
            </p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-xl shadow-sm mb-6">
          <div className="flex border-b">
            {['overview', 'doctors', 'asha', 'mothers'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-6 py-4 text-sm font-medium ${activeTab === tab
                  ? 'border-b-2 border-indigo-500 text-indigo-600'
                  : 'text-gray-500 hover:text-gray-700'
                  }`}
              >
                {tab === 'asha' ? 'ASHA Workers' : tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>

          <div className="p-6">
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                {/* Quick Summary Stats */}
                <div>
                  <h3 className="font-semibold text-lg mb-4">📊 System Overview</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-green-50 p-4 rounded-lg text-center border border-green-200">
                      <p className="text-3xl font-bold text-green-600">
                        {mothers.filter(m => m.doctor_id && m.asha_worker_id).length}
                      </p>
                      <p className="text-sm text-green-700">Fully Assigned</p>
                    </div>
                    <div className="bg-yellow-50 p-4 rounded-lg text-center border border-yellow-200">
                      <p className="text-3xl font-bold text-yellow-600">
                        {mothers.filter(m => !m.doctor_id || !m.asha_worker_id).length}
                      </p>
                      <p className="text-sm text-yellow-700">Needs Assignment</p>
                    </div>
                    <div className="bg-indigo-50 p-4 rounded-lg text-center border border-indigo-200">
                      <p className="text-3xl font-bold text-indigo-600">{doctors.length}</p>
                      <p className="text-sm text-indigo-700">Active Doctors</p>
                    </div>
                    <div className="bg-purple-50 p-4 rounded-lg text-center border border-purple-200">
                      <p className="text-3xl font-bold text-purple-600">{ashaWorkers.length}</p>
                      <p className="text-sm text-purple-700">Active ASHA Workers</p>
                    </div>
                  </div>
                </div>

                {/* Workload Distribution */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Doctor Workload */}
                  <div className="bg-white border rounded-lg p-4">
                    <h4 className="font-semibold text-indigo-800 mb-3">👨‍⚕️ Doctor Workload</h4>
                    {doctors.length === 0 ? (
                      <p className="text-gray-500 text-sm">No doctors registered</p>
                    ) : (
                      <div className="space-y-2">
                        {doctors.slice(0, 5).map(d => {
                          const count = mothers.filter(m => m.doctor_id === d.id).length
                          const maxCount = Math.max(...doctors.map(doc => mothers.filter(m => m.doctor_id === doc.id).length), 1)
                          const percentage = (count / maxCount) * 100
                          return (
                            <div key={d.id} className="flex items-center gap-3">
                              <span className="text-sm w-24 truncate" title={d.name}>{d.name}</span>
                              <div className="flex-1 bg-gray-200 rounded-full h-3">
                                <div
                                  className="bg-indigo-500 h-3 rounded-full transition-all"
                                  style={{ width: `${percentage}%` }}
                                ></div>
                              </div>
                              <span className="text-sm font-semibold text-indigo-600 w-8">{count}</span>
                            </div>
                          )
                        })}
                        {doctors.length > 5 && (
                          <p className="text-xs text-gray-500 mt-2">+{doctors.length - 5} more doctors</p>
                        )}
                      </div>
                    )}
                  </div>

                  {/* ASHA Worker Workload */}
                  <div className="bg-white border rounded-lg p-4">
                    <h4 className="font-semibold text-purple-800 mb-3">👩‍⚕️ ASHA Worker Workload</h4>
                    {ashaWorkers.length === 0 ? (
                      <p className="text-gray-500 text-sm">No ASHA workers registered</p>
                    ) : (
                      <div className="space-y-2">
                        {ashaWorkers.slice(0, 5).map(a => {
                          const count = mothers.filter(m => m.asha_worker_id === a.id).length
                          const maxCount = Math.max(...ashaWorkers.map(asha => mothers.filter(m => m.asha_worker_id === asha.id).length), 1)
                          const percentage = (count / maxCount) * 100
                          return (
                            <div key={a.id} className="flex items-center gap-3">
                              <span className="text-sm w-24 truncate" title={a.name}>{a.name}</span>
                              <div className="flex-1 bg-gray-200 rounded-full h-3">
                                <div
                                  className="bg-purple-500 h-3 rounded-full transition-all"
                                  style={{ width: `${percentage}%` }}
                                ></div>
                              </div>
                              <span className="text-sm font-semibold text-purple-600 w-8">{count}</span>
                            </div>
                          )
                        })}
                        {ashaWorkers.length > 5 && (
                          <p className="text-xs text-gray-500 mt-2">+{ashaWorkers.length - 5} more workers</p>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* Assignment Status */}
                <div className="bg-white border rounded-lg p-4">
                  <h4 className="font-semibold text-gray-800 mb-3">📋 Assignment Status Breakdown</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-3 bg-green-50 rounded-lg">
                      <p className="text-2xl font-bold text-green-600">
                        {mothers.filter(m => m.doctor_id && m.asha_worker_id).length}
                      </p>
                      <p className="text-xs text-green-700">Both Assigned</p>
                    </div>
                    <div className="text-center p-3 bg-blue-50 rounded-lg">
                      <p className="text-2xl font-bold text-blue-600">
                        {mothers.filter(m => m.doctor_id && !m.asha_worker_id).length}
                      </p>
                      <p className="text-xs text-blue-700">Doctor Only</p>
                    </div>
                    <div className="text-center p-3 bg-purple-50 rounded-lg">
                      <p className="text-2xl font-bold text-purple-600">
                        {mothers.filter(m => !m.doctor_id && m.asha_worker_id).length}
                      </p>
                      <p className="text-xs text-purple-700">ASHA Only</p>
                    </div>
                    <div className="text-center p-3 bg-red-50 rounded-lg">
                      <p className="text-2xl font-bold text-red-600">
                        {mothers.filter(m => !m.doctor_id && !m.asha_worker_id).length}
                      </p>
                      <p className="text-xs text-red-700">Unassigned</p>
                    </div>
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-800 mb-3">🚀 Quick Actions</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Link
                      to="/admin/approvals"
                      className="p-4 bg-yellow-100 border border-yellow-300 rounded-lg hover:bg-yellow-200 transition-colors"
                    >
                      <h5 className="font-semibold text-yellow-800">Review Approvals</h5>
                      <p className="text-sm text-yellow-600">{stats?.pending_approvals || 0} pending requests</p>
                    </Link>
                    <button
                      onClick={() => setActiveTab('mothers')}
                      className="p-4 bg-pink-100 border border-pink-300 rounded-lg hover:bg-pink-200 transition-colors text-left"
                    >
                      <h5 className="font-semibold text-pink-800">Manage Mothers</h5>
                      <p className="text-sm text-pink-600">{mothers.length} registered mothers</p>
                    </button>
                    <button
                      onClick={loadData}
                      className="p-4 bg-blue-100 border border-blue-300 rounded-lg hover:bg-blue-200 transition-colors text-left"
                    >
                      <h5 className="font-semibold text-blue-800">Refresh Data</h5>
                      <p className="text-sm text-blue-600">Sync latest information</p>
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Doctors Tab */}
            {activeTab === 'doctors' && (
              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Manage Doctors ({doctors.length})</h3>
                {doctors.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No doctors registered</p>
                ) : (
                  <div className="space-y-3">
                    {doctors.map(d => (
                      <div key={d.id} className="border rounded-lg p-4">
                        {editingId === `doctor-${d.id}` ? (
                          <div className="space-y-3">
                            <div className="grid grid-cols-2 gap-3">
                              <input
                                type="text"
                                value={editData.name}
                                onChange={e => setEditData({ ...editData, name: e.target.value })}
                                className="px-3 py-2 border rounded-lg"
                                placeholder="Name"
                              />
                              <input
                                type="text"
                                value={editData.phone}
                                onChange={e => setEditData({ ...editData, phone: e.target.value })}
                                className="px-3 py-2 border rounded-lg"
                                placeholder="Phone"
                              />
                              <input
                                type="text"
                                value={editData.assigned_area}
                                onChange={e => setEditData({ ...editData, assigned_area: e.target.value })}
                                className="px-3 py-2 border rounded-lg"
                                placeholder="Assigned Area"
                              />
                              <label className="flex items-center gap-2">
                                <input
                                  type="checkbox"
                                  checked={editData.is_active}
                                  onChange={e => setEditData({ ...editData, is_active: e.target.checked })}
                                />
                                Active
                              </label>
                            </div>
                            <div className="flex gap-2">
                              <button
                                onClick={() => saveDoctor(d.id)}
                                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                              >
                                <Check className="w-4 h-4 inline mr-1" /> Save
                              </button>
                              <button
                                onClick={() => setEditingId(null)}
                                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                              >
                                <X className="w-4 h-4 inline mr-1" /> Cancel
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="flex items-center gap-2">
                                <div className={`w-2 h-2 rounded-full ${d.is_active ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                                <span className="font-semibold text-gray-900">{d.name}</span>
                              </div>
                              <p className="text-sm text-gray-500 mt-1">{d.email}</p>
                              <p className="text-xs text-gray-400">{d.assigned_area || 'No area'} · {d.phone || 'No phone'}</p>
                              {/* View Certificate Link */}
                              {d.degree_cert_url && (
                                <a
                                  href={d.degree_cert_url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="mt-2 inline-flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-800"
                                >
                                  <FileText className="w-3.5 h-3.5" />
                                  View Certificate
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                              )}
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="bg-indigo-100 text-indigo-700 text-xs px-2 py-1 rounded-full">
                                {d.mothers_count || 0} mothers
                              </span>
                              <button
                                onClick={() => handleEditDoctor(d)}
                                className="p-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                                title="Edit"
                              >
                                <Edit2 className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => deleteDoctor(d.id, d.name)}
                                className="p-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
                                title="Delete"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* ASHA Workers Tab */}
            {activeTab === 'asha' && (
              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Manage ASHA Workers ({ashaWorkers.length})</h3>
                {ashaWorkers.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No ASHA workers registered</p>
                ) : (
                  <div className="space-y-3">
                    {ashaWorkers.map(a => (
                      <div key={a.id} className="border rounded-lg p-4">
                        {editingId === `asha-${a.id}` ? (
                          <div className="space-y-3">
                            <div className="grid grid-cols-2 gap-3">
                              <input
                                type="text"
                                value={editData.name}
                                onChange={e => setEditData({ ...editData, name: e.target.value })}
                                className="px-3 py-2 border rounded-lg"
                                placeholder="Name"
                              />
                              <input
                                type="text"
                                value={editData.phone}
                                onChange={e => setEditData({ ...editData, phone: e.target.value })}
                                className="px-3 py-2 border rounded-lg"
                                placeholder="Phone"
                              />
                              <input
                                type="text"
                                value={editData.assigned_area}
                                onChange={e => setEditData({ ...editData, assigned_area: e.target.value })}
                                className="px-3 py-2 border rounded-lg"
                                placeholder="Assigned Area"
                              />
                              <label className="flex items-center gap-2">
                                <input
                                  type="checkbox"
                                  checked={editData.is_active}
                                  onChange={e => setEditData({ ...editData, is_active: e.target.checked })}
                                />
                                Active
                              </label>
                            </div>
                            <div className="flex gap-2">
                              <button
                                onClick={() => saveAsha(a.id)}
                                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                              >
                                <Check className="w-4 h-4 inline mr-1" /> Save
                              </button>
                              <button
                                onClick={() => setEditingId(null)}
                                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                              >
                                <X className="w-4 h-4 inline mr-1" /> Cancel
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="flex items-center gap-2">
                                <div className={`w-2 h-2 rounded-full ${a.is_active ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                                <span className="font-semibold text-gray-900">{a.name}</span>
                              </div>
                              <p className="text-sm text-gray-500 mt-1">{a.email}</p>
                              <p className="text-xs text-gray-400">{a.assigned_area || 'No area'} · {a.phone || 'No phone'}</p>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="bg-purple-100 text-purple-700 text-xs px-2 py-1 rounded-full">
                                {a.mothers_count || 0} mothers
                              </span>
                              <button
                                onClick={() => handleEditAsha(a)}
                                className="p-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                                title="Edit"
                              >
                                <Edit2 className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => deleteAsha(a.id, a.name)}
                                className="p-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
                                title="Delete"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Mothers Tab */}
            {activeTab === 'mothers' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-lg">Manage Mothers ({mothers.length})</h3>
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
                      <input
                        type="text"
                        placeholder="Search..."
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                        className="pl-9 pr-4 py-2 border rounded-lg text-sm w-48"
                      />
                    </div>
                    {pendingChangesCount > 0 && (
                      <button
                        onClick={saveAllChanges}
                        disabled={saving}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                      >
                        {saving ? (
                          <RefreshCw className="w-4 h-4 animate-spin" />
                        ) : (
                          <Save className="w-4 h-4" />
                        )}
                        Save {pendingChangesCount} Change{pendingChangesCount > 1 ? 's' : ''}
                      </button>
                    )}
                  </div>
                </div>

                {filteredMothers.length === 0 ? (
                  <p className="text-gray-500 py-8 text-center">
                    {searchTerm ? 'No mothers match your search' : 'No mothers registered yet'}
                  </p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left font-semibold">Name</th>
                          <th className="px-4 py-3 text-left font-semibold">Phone</th>
                          <th className="px-4 py-3 text-left font-semibold">Location</th>
                          <th className="px-4 py-3 text-left font-semibold text-purple-600">ASHA Worker</th>
                          <th className="px-4 py-3 text-left font-semibold text-indigo-600">Doctor</th>
                          <th className="px-4 py-3 text-left font-semibold">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredMothers.map(mother => {
                          const effectiveDoctor = getEffectiveValue(mother, 'doctor_id')
                          const effectiveAsha = getEffectiveValue(mother, 'asha_worker_id')
                          const isFullyAssigned = effectiveDoctor && effectiveAsha
                          const hasChanges = pendingChanges[mother.id]

                          return (
                            <tr key={mother.id} className={`border-b hover:bg-gray-50 ${hasChanges ? 'bg-yellow-50' : ''}`}>
                              <td className="px-4 py-3 font-medium">
                                {mother.name}
                                {hasChanges && <span className="ml-2 text-yellow-600 text-xs">*</span>}
                              </td>
                              <td className="px-4 py-3 text-gray-600">{mother.phone}</td>
                              <td className="px-4 py-3 text-gray-600">{mother.location || '-'}</td>
                              <td className="px-4 py-3">
                                <select
                                  value={effectiveAsha || ''}
                                  onChange={e => handleAssignmentChange(mother.id, 'asha', e.target.value)}
                                  className={`text-sm border rounded px-2 py-1.5 w-36 ${hasChanges && 'asha_worker_id' in pendingChanges[mother.id] ? 'border-yellow-400 bg-yellow-50' :
                                    effectiveAsha ? 'border-purple-300 bg-purple-50' : 'border-gray-300'
                                    }`}
                                >
                                  <option value="">-- Select --</option>
                                  {ashaWorkers.map(a => (
                                    <option key={a.id} value={a.id}>{a.name}</option>
                                  ))}
                                </select>
                              </td>
                              <td className="px-4 py-3">
                                <select
                                  value={effectiveDoctor || ''}
                                  onChange={e => handleAssignmentChange(mother.id, 'doctor', e.target.value)}
                                  className={`text-sm border rounded px-2 py-1.5 w-36 ${hasChanges && 'doctor_id' in pendingChanges[mother.id] ? 'border-yellow-400 bg-yellow-50' :
                                    effectiveDoctor ? 'border-indigo-300 bg-indigo-50' : 'border-gray-300'
                                    }`}
                                >
                                  <option value="">-- Select --</option>
                                  {doctors.map(d => (
                                    <option key={d.id} value={d.id}>{d.name}</option>
                                  ))}
                                </select>
                              </td>
                              <td className="px-4 py-3">
                                {isFullyAssigned ? (
                                  <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-semibold">
                                    <Check className="w-3 h-3" /> OK
                                  </span>
                                ) : (
                                  <span className="inline-flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-700 rounded-full text-xs font-semibold">
                                    ⚠️
                                  </span>
                                )}
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
