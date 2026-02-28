import React, { useEffect, useState, useCallback } from 'react'
import { Shield, Users, UserCog, Baby, Edit2, Check, X, RefreshCw, Search, ChevronDown, ChevronUp, Save, Trash2, FileText, ExternalLink } from 'lucide-react'
import { Link } from 'react-router-dom'
import { adminAPI } from '../services/api'

export default function AdminDashboard() {
  const [stats, setStats] = useState(null)
  const [santanStats, setSantanStats] = useState(null) // SantanRaksha stats
  const [doctors, setDoctors] = useState([])
  const [ashaWorkers, setAshaWorkers] = useState([])
  const [mothers, setMothers] = useState([])
  const [children, setChildren] = useState([]) // Children from SantanRaksha
  const [metrics, setMetrics] = useState(null) // Token and Cost metrics
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [activeTab, setActiveTab] = useState('overview')
  const [searchTerm, setSearchTerm] = useState('')
  const [motherStatusFilter, setMotherStatusFilter] = useState('all') // Filter mothers by status

  // For editing doctors/asha/children
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

          // Also fetch SantanRaksha data (children + stats) - NOT included in /admin/full
          try {
            const [childrenRes, santanStatsRes, metricsRes] = await Promise.all([
              adminAPI.getChildren().catch(() => ({ data: { children: [] } })),
              adminAPI.getSantanRakshaStats().catch(() => ({ data: { stats: {} } })),
              adminAPI.getMetrics().catch(() => ({ data: { metrics: {} } }))
            ])
            setChildren(childrenRes.data?.children || [])
            setSantanStats(santanStatsRes.data?.stats || {})
            setMetrics(metricsRes.data?.metrics || null)
          } catch (childErr) {
            console.warn('Children data not loaded:', childErr.message)
          }

          setLoading(false)
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

      // Fetch SantanRaksha data (children + stats)
      try {
        const [childrenRes, santanStatsRes, metricsRes] = await Promise.all([
          adminAPI.getChildren().catch(() => ({ data: { children: [] } })),
          adminAPI.getSantanRakshaStats().catch(() => ({ data: { stats: {} } })),
          adminAPI.getMetrics().catch(() => ({ data: { metrics: {} } }))
        ])
        setChildren(childrenRes.data?.children || [])
        setSantanStats(santanStatsRes.data?.stats || {})
        setMetrics(metricsRes.data?.metrics || null)
      } catch (childErr) {
        console.warn('Children data not loaded:', childErr.message)
      }
    } catch (e) {
      setError(e.message || 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }, [])


  useEffect(() => {
    let isMounted = true

    const fetchData = async () => {
      try {
        await loadData()
      } catch (error) {
        if (isMounted) {
          console.error('Failed to load data:', error)
        }
      }
    }

    fetchData()

    return () => {
      isMounted = false
    }
  }, [loadData])

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

  // ==================== Children Handlers ====================
  const handleEditChild = (child) => {
    setEditingId(`child-${child.id}`)
    setEditData({
      name: child.name || '',
      gender: child.gender || '',
      birth_date: child.birth_date?.split('T')[0] || '',
      birth_weight_kg: child.birth_weight_kg || '',
      blood_group: child.blood_group || '',
      notes: child.notes || ''
    })
  }

  const saveChild = async (id) => {
    try {
      await adminAPI.updateChild(id, editData)
      setSuccess('Child updated successfully')
      setEditingId(null)
      await loadData()
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to update child')
    }
  }

  const deleteChild = async (id, name) => {
    if (!window.confirm(`Are you sure you want to delete ${name}? This will also delete their vaccinations, growth records, and assessments.`)) {
      return
    }
    try {
      await adminAPI.deleteChild(id)
      setSuccess('Child deleted successfully')
      await loadData()
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to delete child')
    }
  }

  // Filter mothers based on search and status
  const filteredMothers = mothers.filter(m => {
    const matchesSearch = m.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.phone?.includes(searchTerm) ||
      m.location?.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = motherStatusFilter === 'all' || m.delivery_status === motherStatusFilter
    return matchesSearch && matchesStatus
  })

  // Filter children based on search
  const filteredChildren = children.filter(c =>
    c.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.mother_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.mother_phone?.includes(searchTerm)
  )

  const pendingChangesCount = Object.keys(pendingChanges).length

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-blue-50/50">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-teal-500"></div>
          <p className="mt-4 text-gray-600">Loading admin dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-blue-50/50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <div className="bg-teal-600 p-3 rounded-lg">
              <Shield className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-800">Admin Dashboard</h1>
              <p className="text-slate-400">Manage system users and assignments</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/admin/approvals"
              className="flex items-center gap-2 px-4 py-2 bg-yellow-500/100/15 text-yellow-700 rounded-lg hover:bg-yellow-200"
            >
              <Shield className="w-4 h-4" />
              Approvals ({stats?.pending_approvals || 0})
            </Link>
            <button
              onClick={loadData}
              className="flex items-center gap-2 px-4 py-2 bg-white/60 text-slate-600 rounded-lg hover:bg-gray-300"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          </div>
        </div>

        {/* Alerts */}
        {error && (
          <div className="bg-red-500/10 border border-red-200 text-red-600 px-4 py-3 rounded-lg mb-4 flex justify-between">
            {error}
            <button onClick={() => setError('')}>&times;</button>
          </div>
        )}
        {success && (
          <div className="bg-emerald-500/10 border border-emerald-200 text-emerald-600 px-4 py-3 rounded-lg mb-4 flex justify-between items-center">
            <span>✅ {success}</span>
            <button onClick={() => setSuccess('')}>&times;</button>
          </div>
        )}

        {/* Stats Overview - MatruRaksha + SantanRaksha */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-white/60 backdrop-blur-xl rounded-xl shadow-sm p-5 border-l-4 border-pink-500">
            <p className="text-sm text-slate-400">Total Mothers</p>
            <p className="text-3xl font-bold text-slate-800">{stats?.total_mothers ?? '-'}</p>
          </div>
          <div className="bg-white/60 backdrop-blur-xl rounded-xl shadow-sm p-5 border-l-4 border-cyan-500">
            <p className="text-sm text-slate-400">Total Children</p>
            <p className="text-3xl font-bold text-slate-800">{santanStats?.total_children ?? children.length}</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-5 border-l-4 border-teal-500">
            <p className="text-sm text-gray-500">Doctors</p>
            <p className="text-3xl font-bold text-gray-900">{stats?.total_doctors ?? '-'}</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-5 border-l-4 border-teal-500">
            <p className="text-sm text-gray-500">ASHA Workers</p>
            <p className="text-3xl font-bold text-gray-900">{stats?.total_asha_workers ?? '-'}</p>
          </div>
          <div className="bg-white/60 backdrop-blur-xl rounded-xl shadow-sm p-5 border-l-4 border-emerald-500">
            <p className="text-sm text-slate-400">Fully Assigned</p>
            <p className="text-3xl font-bold text-slate-800">
              {mothers.filter(m => m.doctor_id && m.asha_worker_id).length}
            </p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white/60 backdrop-blur-xl rounded-xl shadow-sm mb-6">
          <div className="flex border-b overflow-x-auto">
            {['overview', 'analytics', 'doctors', 'asha', 'mothers', 'children'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-6 py-4 text-sm font-medium whitespace-nowrap ${activeTab === tab
                  ? 'border-b-2 border-teal-500 text-teal-600'
                  : 'text-gray-500 hover:text-gray-700'
                  }`}
              >
                {tab === 'asha' ? 'ASHA Workers' : tab === 'children' ? '👶 Children' : tab === 'analytics' ? '📈 Analytics' : tab.charAt(0).toUpperCase() + tab.slice(1)}
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
                    <div className="bg-emerald-500/10 p-4 rounded-lg text-center border border-emerald-200">
                      <p className="text-3xl font-bold text-emerald-600">
                        {mothers.filter(m => m.doctor_id && m.asha_worker_id).length}
                      </p>
                      <p className="text-sm text-emerald-600">Fully Assigned</p>
                    </div>
                    <div className="bg-yellow-500/10 p-4 rounded-lg text-center border border-yellow-200">
                      <p className="text-3xl font-bold text-yellow-600">
                        {mothers.filter(m => !m.doctor_id || !m.asha_worker_id).length}
                      </p>
                      <p className="text-sm text-yellow-600">Needs Assignment</p>
                    </div>
                    <div className="bg-teal-50 p-4 rounded-lg text-center border border-teal-200">
                      <p className="text-3xl font-bold text-teal-600">{doctors.length}</p>
                      <p className="text-sm text-teal-700">Active Doctors</p>
                    </div>
                    <div className="bg-teal-50 p-4 rounded-lg text-center border border-teal-200">
                      <p className="text-3xl font-bold text-teal-600">{ashaWorkers.length}</p>
                      <p className="text-sm text-teal-700">Active ASHA Workers</p>
                    </div>
                  </div>
                </div>

                {/* Workload Distribution */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Doctor Workload */}
                  <div className="bg-white/60 backdrop-blur-xl border rounded-lg p-4">
                    <h4 className="font-semibold text-teal-800 mb-3">👨‍⚕️ Doctor Workload</h4>
                    {doctors.length === 0 ? (
                      <p className="text-slate-400 text-sm">No doctors registered</p>
                    ) : (
                      <div className="space-y-2">
                        {doctors.slice(0, 5).map(d => {
                          const count = mothers.filter(m => m.doctor_id === d.id).length
                          const maxCount = Math.max(...doctors.map(doc => mothers.filter(m => m.doctor_id === doc.id).length), 1)
                          const percentage = (count / maxCount) * 100
                          return (
                            <div key={d.id} className="flex items-center gap-3">
                              <span className="text-sm w-24 truncate" title={d.name}>{d.name}</span>
                              <div className="flex-1 bg-white/60 rounded-full h-3">
                                <div
                                  className="bg-teal-500 h-3 rounded-full transition-all"
                                  style={{ width: `${percentage}%` }}
                                ></div>
                              </div>
                              <span className="text-sm font-semibold text-teal-600 w-8">{count}</span>
                            </div>
                          )
                        })}
                        {doctors.length > 5 && (
                          <p className="text-xs text-slate-400 mt-2">+{doctors.length - 5} more doctors</p>
                        )}
                      </div>
                    )}
                  </div>

                  {/* ASHA Worker Workload */}
                  <div className="bg-white border rounded-lg p-4">
                    <h4 className="font-semibold text-teal-800 mb-3">👩‍⚕️ ASHA Worker Workload</h4>
                    {ashaWorkers.length === 0 ? (
                      <p className="text-slate-400 text-sm">No ASHA workers registered</p>
                    ) : (
                      <div className="space-y-2">
                        {ashaWorkers.slice(0, 5).map(a => {
                          const count = mothers.filter(m => m.asha_worker_id === a.id).length
                          const maxCount = Math.max(...ashaWorkers.map(asha => mothers.filter(m => m.asha_worker_id === asha.id).length), 1)
                          const percentage = (count / maxCount) * 100
                          return (
                            <div key={a.id} className="flex items-center gap-3">
                              <span className="text-sm w-24 truncate" title={a.name}>{a.name}</span>
                              <div className="flex-1 bg-white/60 rounded-full h-3">
                                <div
                                  className="bg-teal-500 h-3 rounded-full transition-all"
                                  style={{ width: `${percentage}%` }}
                                ></div>
                              </div>
                              <span className="text-sm font-semibold text-teal-600 w-8">{count}</span>
                            </div>
                          )
                        })}
                        {ashaWorkers.length > 5 && (
                          <p className="text-xs text-slate-400 mt-2">+{ashaWorkers.length - 5} more workers</p>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* Assignment Status */}
                <div className="bg-white/60 backdrop-blur-xl border rounded-lg p-4">
                  <h4 className="font-semibold text-slate-800 mb-3">📋 Assignment Status Breakdown</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-3 bg-emerald-500/10 rounded-lg">
                      <p className="text-2xl font-bold text-emerald-600">
                        {mothers.filter(m => m.doctor_id && m.asha_worker_id).length}
                      </p>
                      <p className="text-xs text-emerald-600">Both Assigned</p>
                    </div>
                    <div className="text-center p-3 bg-blue-500/10 rounded-lg">
                      <p className="text-2xl font-bold text-blue-600">
                        {mothers.filter(m => m.doctor_id && !m.asha_worker_id).length}
                      </p>
                      <p className="text-xs text-blue-600">Doctor Only</p>
                    </div>
                    <div className="text-center p-3 bg-teal-50 rounded-lg">
                      <p className="text-2xl font-bold text-teal-600">
                        {mothers.filter(m => !m.doctor_id && m.asha_worker_id).length}
                      </p>
                      <p className="text-xs text-teal-700">ASHA Only</p>
                    </div>
                    <div className="text-center p-3 bg-red-500/10 rounded-lg">
                      <p className="text-2xl font-bold text-red-600">
                        {mothers.filter(m => !m.doctor_id && !m.asha_worker_id).length}
                      </p>
                      <p className="text-xs text-red-600">Unassigned</p>
                    </div>
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="bg-blue-50/50 rounded-lg p-4">
                  <h4 className="font-semibold text-slate-800 mb-3">🚀 Quick Actions</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Link
                      to="/admin/approvals"
                      className="p-4 bg-yellow-500/100/15 border border-yellow-300 rounded-lg hover:bg-yellow-200 transition-colors"
                    >
                      <h5 className="font-semibold text-yellow-700">Review Approvals</h5>
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
                      className="p-4 bg-blue-500/100/15 border border-blue-300 rounded-lg hover:bg-blue-200 transition-colors text-left"
                    >
                      <h5 className="font-semibold text-blue-700">Refresh Data</h5>
                      <p className="text-sm text-blue-600">Sync latest information</p>
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Analytics Tab */}
            {activeTab === 'analytics' && (
              <div className="space-y-6">
                <div>
                  <h3 className="font-semibold text-lg mb-4">📈 AI Token & Cost Analytics</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-teal-50 p-4 rounded-lg text-center border border-teal-200">
                      <p className="text-3xl font-bold text-teal-600">
                        {metrics?.token_usage_estimated?.toLocaleString() || 0}
                      </p>
                      <p className="text-sm text-teal-700">Estimated Tokens</p>
                    </div>
                    <div className="bg-yellow-500/10 p-4 rounded-lg text-center border border-yellow-200">
                      <p className="text-3xl font-bold text-yellow-600">
                        ${metrics?.cost_usd_estimated?.toFixed(4) || "0.0000"}
                      </p>
                      <p className="text-sm text-yellow-600">Estimated USD Cost</p>
                    </div>
                    <div className="bg-emerald-500/10 p-4 rounded-lg text-center border border-emerald-200">
                      <p className="text-3xl font-bold text-emerald-600">
                        {metrics?.ai_calls_total?.toLocaleString() || 0}
                      </p>
                      <p className="text-sm text-emerald-600">Total AI Inferences</p>
                    </div>
                  </div>
                </div>

                {/* Word Cloud */}
                <div className="bg-white/60 backdrop-blur-xl border rounded-lg p-4 mt-6">
                  <h4 className="font-semibold text-slate-800 mb-3">🗣️ Common Risk Topics (Word Cloud)</h4>
                  <div className="flex flex-wrap gap-2 p-4 bg-blue-50/50 rounded-lg min-h-[200px] items-center justify-center">
                    {!metrics?.word_cloud || !Array.isArray(metrics.word_cloud) ? (
                      <p className="text-slate-400">No word data available</p>
                    ) : (
                      metrics.word_cloud.map((w, idx) => (
                        <span
                          key={idx}
                          className="px-3 py-1 bg-white border border-gray-200 shadow-sm rounded-full text-teal-600 font-medium whitespace-nowrap"
                          style={{ fontSize: `${Math.max(0.8, Math.min(2, w.value / 10))}rem`, opacity: Math.max(0.5, Math.min(1, w.value / 20)) }}
                        >
                          {w.text} <span className="text-xs text-slate-400 ml-1">({w.value})</span>
                        </span>
                      ))
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Doctors Tab */}
            {activeTab === 'doctors' && (
              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Manage Doctors ({doctors.length})</h3>
                {doctors.length === 0 ? (
                  <p className="text-slate-400 text-center py-8">No doctors registered</p>
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
                                className="px-4 py-2 bg-green-600 text-slate-800 rounded-lg hover:bg-green-700"
                              >
                                <Check className="w-4 h-4 inline mr-1" /> Save
                              </button>
                              <button
                                onClick={() => setEditingId(null)}
                                className="px-4 py-2 bg-white/60 text-slate-600 rounded-lg hover:bg-gray-300"
                              >
                                <X className="w-4 h-4 inline mr-1" /> Cancel
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="flex items-center gap-2">
                                <div className={`w-2 h-2 rounded-full ${d.is_active ? 'bg-emerald-500/100' : 'bg-gray-400'}`}></div>
                                <span className="font-semibold text-slate-800">{d.name}</span>
                              </div>
                              <p className="text-sm text-slate-400 mt-1">{d.email}</p>
                              <p className="text-xs text-slate-400">{d.assigned_area || 'No area'} · {d.phone || 'No phone'}</p>
                              {/* View Certificate Link */}
                              {d.degree_cert_url && (
                                <a
                                  href={d.degree_cert_url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="mt-2 inline-flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-700"
                                >
                                  <FileText className="w-3.5 h-3.5" />
                                  View Certificate
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                              )}
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="bg-teal-100 text-teal-700 text-xs px-2 py-1 rounded-full">
                                {d.mothers_count || 0} mothers
                              </span>
                              <button
                                onClick={() => handleEditDoctor(d)}
                                className="p-2 bg-white/50 text-slate-600 rounded-lg hover:bg-white/60"
                                title="Edit"
                              >
                                <Edit2 className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => deleteDoctor(d.id, d.name)}
                                className="p-2 bg-red-500/100/15 text-red-600 rounded-lg hover:bg-red-200"
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
                  <p className="text-slate-400 text-center py-8">No ASHA workers registered</p>
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
                                className="px-4 py-2 bg-green-600 text-slate-800 rounded-lg hover:bg-green-700"
                              >
                                <Check className="w-4 h-4 inline mr-1" /> Save
                              </button>
                              <button
                                onClick={() => setEditingId(null)}
                                className="px-4 py-2 bg-white/60 text-slate-600 rounded-lg hover:bg-gray-300"
                              >
                                <X className="w-4 h-4 inline mr-1" /> Cancel
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="flex items-center gap-2">
                                <div className={`w-2 h-2 rounded-full ${a.is_active ? 'bg-emerald-500/100' : 'bg-gray-400'}`}></div>
                                <span className="font-semibold text-slate-800">{a.name}</span>
                              </div>
                              <p className="text-sm text-slate-400 mt-1">{a.email}</p>
                              <p className="text-xs text-slate-400">{a.assigned_area || 'No area'} · {a.phone || 'No phone'}</p>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="bg-teal-100 text-teal-700 text-xs px-2 py-1 rounded-full">
                                {a.mothers_count || 0} mothers
                              </span>
                              <button
                                onClick={() => handleEditAsha(a)}
                                className="p-2 bg-white/50 text-slate-600 rounded-lg hover:bg-white/60"
                                title="Edit"
                              >
                                <Edit2 className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => deleteAsha(a.id, a.name)}
                                className="p-2 bg-red-500/100/15 text-red-600 rounded-lg hover:bg-red-200"
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
                <div className="flex items-center justify-between flex-wrap gap-3">
                  <h3 className="font-semibold text-lg">Manage Mothers ({filteredMothers.length} of {mothers.length})</h3>
                  <div className="flex items-center gap-3 flex-wrap">
                    {/* Status Filter */}
                    <select
                      value={motherStatusFilter}
                      onChange={e => setMotherStatusFilter(e.target.value)}
                      className="px-3 py-2 border rounded-lg text-sm"
                    >
                      <option value="all">All Statuses</option>
                      <option value="pregnant">🤰 Pregnant</option>
                      <option value="delivered">✅ Delivered</option>
                    </select>
                    <div className="relative">
                      <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
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
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-slate-800 rounded-lg hover:bg-green-700 disabled:opacity-50"
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
                  <p className="text-slate-400 py-8 text-center">
                    {searchTerm ? 'No mothers match your search' : 'No mothers registered yet'}
                  </p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-blue-50/50">
                        <tr>
                          <th className="px-4 py-3 text-left font-semibold">Name</th>
                          <th className="px-4 py-3 text-left font-semibold">Phone</th>
                          <th className="px-4 py-3 text-left font-semibold">Location</th>
                          <th className="px-4 py-3 text-left font-semibold">Delivery Status</th>
                          <th className="px-4 py-3 text-left font-semibold text-teal-600">ASHA Worker</th>
                          <th className="px-4 py-3 text-left font-semibold text-teal-600">Doctor</th>
                          <th className="px-4 py-3 text-left font-semibold">Assignment</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredMothers.map(mother => {
                          const effectiveDoctor = getEffectiveValue(mother, 'doctor_id')
                          const effectiveAsha = getEffectiveValue(mother, 'asha_worker_id')
                          const isFullyAssigned = effectiveDoctor && effectiveAsha
                          const hasChanges = pendingChanges[mother.id]

                          return (
                            <tr key={mother.id} className={`border-b hover:bg-blue-50/50 ${hasChanges ? 'bg-yellow-500/10' : ''}`}>
                              <td className="px-4 py-3 font-medium">
                                {mother.name}
                                {hasChanges && <span className="ml-2 text-yellow-600 text-xs">*</span>}
                              </td>
                              <td className="px-4 py-3 text-slate-500">{mother.phone}</td>
                              <td className="px-4 py-3 text-slate-500">{mother.location || '-'}</td>
                              <td className="px-4 py-3">
                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${mother.delivery_status === 'pregnant' ? 'bg-pink-100 text-pink-700' :
                                  mother.delivery_status === 'delivered' ? 'bg-emerald-500/15 text-emerald-600' :
                                    'bg-white/50 text-slate-500'
                                  }`}>
                                  {mother.delivery_status === 'pregnant' ? '🤰 Pregnant' :
                                    mother.delivery_status === 'delivered' ? '✅ Delivered' :
                                      mother.delivery_status || 'Unknown'}
                                </span>
                              </td>
                              <td className="px-4 py-3">
                                <select
                                  value={effectiveAsha || ''}
                                  onChange={e => handleAssignmentChange(mother.id, 'asha', e.target.value)}
                                  className={`text-sm border rounded px-2 py-1.5 w-36 ${hasChanges && 'asha_worker_id' in pendingChanges[mother.id] ? 'border-yellow-400 bg-yellow-50' :
                                    effectiveAsha ? 'border-teal-300 bg-teal-50' : 'border-gray-300'
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
                                    effectiveDoctor ? 'border-teal-300 bg-teal-50' : 'border-gray-300'
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
                                  <span className="inline-flex items-center gap-1 px-2 py-1 bg-emerald-500/15 text-emerald-600 rounded-full text-xs font-semibold">
                                    <Check className="w-3 h-3" /> OK
                                  </span>
                                ) : (
                                  <span className="inline-flex items-center gap-1 px-2 py-1 bg-yellow-500/100/15 text-yellow-600 rounded-full text-xs font-semibold">
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

            {/* Children Tab (SantanRaksha) */}
            {activeTab === 'children' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-lg">Manage Children ({children.length})</h3>
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
                      <input
                        type="text"
                        placeholder="Search by name/mother..."
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                        className="pl-9 pr-4 py-2 border rounded-lg text-sm w-56"
                      />
                    </div>
                  </div>
                </div>

                {filteredChildren.length === 0 ? (
                  <p className="text-slate-400 py-8 text-center">
                    {searchTerm ? 'No children match your search' : 'No children registered yet'}
                  </p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-blue-50/50">
                        <tr>
                          <th className="px-4 py-3 text-left font-semibold">Child Name</th>
                          <th className="px-4 py-3 text-left font-semibold">Age</th>
                          <th className="px-4 py-3 text-left font-semibold">Gender</th>
                          <th className="px-4 py-3 text-left font-semibold">Mother</th>
                          <th className="px-4 py-3 text-left font-semibold text-teal-600">ASHA Worker</th>
                          <th className="px-4 py-3 text-left font-semibold text-teal-600">Doctor</th>
                          <th className="px-4 py-3 text-left font-semibold">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredChildren.map(child => (
                          <tr key={child.id} className="border-b hover:bg-blue-50/50">
                            {editingId === `child-${child.id}` ? (
                              // Edit mode
                              <>
                                <td className="px-4 py-3">
                                  <input
                                    type="text"
                                    value={editData.name}
                                    onChange={e => setEditData({ ...editData, name: e.target.value })}
                                    className="px-2 py-1 border rounded w-full"
                                    placeholder="Name"
                                  />
                                </td>
                                <td className="px-4 py-3">
                                  <input
                                    type="date"
                                    value={editData.birth_date}
                                    onChange={e => setEditData({ ...editData, birth_date: e.target.value })}
                                    className="px-2 py-1 border rounded"
                                  />
                                </td>
                                <td className="px-4 py-3">
                                  <select
                                    value={editData.gender}
                                    onChange={e => setEditData({ ...editData, gender: e.target.value })}
                                    className="px-2 py-1 border rounded"
                                  >
                                    <option value="">Select</option>
                                    <option value="male">Male</option>
                                    <option value="female">Female</option>
                                    <option value="other">Other</option>
                                  </select>
                                </td>
                                <td className="px-4 py-3 text-slate-400">{child.mother_name}</td>
                                <td className="px-4 py-3 text-slate-400">{child.asha_worker_name}</td>
                                <td className="px-4 py-3 text-slate-400">{child.doctor_name}</td>
                                <td className="px-4 py-3">
                                  <div className="flex gap-2">
                                    <button
                                      onClick={() => saveChild(child.id)}
                                      className="p-1.5 bg-emerald-500/15 text-emerald-600 rounded hover:bg-green-200"
                                      title="Save"
                                    >
                                      <Check className="w-4 h-4" />
                                    </button>
                                    <button
                                      onClick={() => setEditingId(null)}
                                      className="p-1.5 bg-white/50 text-slate-600 rounded hover:bg-white/60"
                                      title="Cancel"
                                    >
                                      <X className="w-4 h-4" />
                                    </button>
                                  </div>
                                </td>
                              </>
                            ) : (
                              // View mode
                              <>
                                <td className="px-4 py-3 font-medium">{child.name}</td>
                                <td className="px-4 py-3 text-slate-500">
                                  <span className="bg-cyan-100 text-cyan-700 px-2 py-0.5 rounded-full text-xs">
                                    {child.age_display || 'N/A'}
                                  </span>
                                </td>
                                <td className="px-4 py-3 text-slate-500 capitalize">{child.gender || '-'}</td>
                                <td className="px-4 py-3">
                                  <div>
                                    <p className="font-medium">{child.mother_name}</p>
                                    <p className="text-xs text-slate-400">{child.mother_phone}</p>
                                    {child.mother_status && (
                                      <span className={`text-xs px-1.5 py-0.5 rounded ${child.mother_status === 'postnatal' ? 'bg-emerald-500/15 text-emerald-600' :
                                        child.mother_status === 'pregnant' ? 'bg-pink-100 text-pink-700' :
                                          'bg-white/50 text-slate-500'
                                        }`}>
                                        {child.mother_status}
                                      </span>
                                    )}
                                  </div>
                                </td>
                                <td className="px-4 py-3">
                                  <span className={child.asha_worker_name !== 'Unassigned' ? 'text-teal-600' : 'text-gray-400'}>
                                    {child.asha_worker_name}
                                  </span>
                                </td>
                                <td className="px-4 py-3">
                                  <span className={child.doctor_name !== 'Unassigned' ? 'text-teal-600' : 'text-gray-400'}>
                                    {child.doctor_name}
                                  </span>
                                </td>
                                <td className="px-4 py-3">
                                  <div className="flex gap-2">
                                    <button
                                      onClick={() => handleEditChild(child)}
                                      className="p-1.5 bg-white/50 text-slate-600 rounded hover:bg-white/60"
                                      title="Edit"
                                    >
                                      <Edit2 className="w-4 h-4" />
                                    </button>
                                    <button
                                      onClick={() => deleteChild(child.id, child.name)}
                                      className="p-1.5 bg-red-500/100/15 text-red-600 rounded hover:bg-red-200"
                                      title="Delete"
                                    >
                                      <Trash2 className="w-4 h-4" />
                                    </button>
                                  </div>
                                </td>
                              </>
                            )}
                          </tr>
                        ))}
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
