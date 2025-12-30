// FILE: frontend/src/pages/RiskDashboard.jsx
import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

// Simple API calls without external library
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiCall = async (method, endpoint, data = null) => {
  try {
    const options = {
      method: method,
      headers: {
        'Content-Type': 'application/json',
      },
    }

    if (data) {
      options.body = JSON.stringify(data)
    }

    const response = await fetch(`${API_URL}${endpoint}`, options)

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error(`API Error [${method} ${endpoint}]:`, error.message)
    throw error
  }
}

export default function RiskDashboard() {
  const { t, i18n } = useTranslation()
  const [activeTab, setActiveTab] = useState('dashboard')
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('maatruDarkMode')
    return saved ? JSON.parse(saved) : false
  })
  const [mothers, setMothers] = useState([])
  const [analytics, setAnalytics] = useState({
    totalMothers: 0,
    highRiskCount: 0,
    moderateRiskCount: 0,
    lowRiskCount: 0,
    totalAssessments: 0
  })
  const [riskTrend, setRiskTrend] = useState([])
  const [ageDistribution, setAgeDistribution] = useState([])
  const [vitalStats, setVitalStats] = useState([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [chartsLoading, setChartsLoading] = useState(false)

  // Save dark mode preference
  useEffect(() => {
    localStorage.setItem('maatruDarkMode', JSON.stringify(darkMode))
  }, [darkMode])

  // Register form state
  const [registerForm, setRegisterForm] = useState({
    name: '',
    phone: '',
    age: '',
    gravida: 'Gravida 1',
    parity: 'Parity 0',
    bmi: '',
    location: '',
    preferred_language: 'en',
    telegram_chat_id: ''
  })

  // Risk assessment form state
  const [assessmentForm, setAssessmentForm] = useState({
    mother_id: '',
    systolic_bp: '',
    diastolic_bp: '',
    heart_rate: '',
    blood_glucose: '',
    hemoglobin: '',
    proteinuria: 0,
    edema: 0,
    headache: 0,
    vision_changes: 0,
    epigastric_pain: 0,
    vaginal_bleeding: 0
  })

  const [riskResult, setRiskResult] = useState(null)
  const [expandedMother, setExpandedMother] = useState(null)

  // Fetch analytics only on mount and manual refresh
  useEffect(() => {
    fetchAnalyticsData()
  }, [])

  // Fetch mothers for dropdowns
  useEffect(() => {
    if (activeTab === 'risk-assessment' || activeTab === 'all-mothers') {
      fetchMothers()
    }
  }, [activeTab])

  const fetchAnalyticsData = async () => {
    try {
      setChartsLoading(true)

      // OPTIMIZED: Try combined endpoint first (1 API call instead of 3)
      try {
        const fullData = await apiCall('GET', '/dashboard/full')
        console.log('Full dashboard response:', fullData, fullData.cached ? '(cached)' : '(fresh)')

        // Set analytics from combined response
        setAnalytics({
          totalMothers: fullData.analytics?.total_mothers || 0,
          highRiskCount: fullData.analytics?.high_risk_count || 0,
          moderateRiskCount: fullData.analytics?.moderate_risk_count || 0,
          lowRiskCount: fullData.analytics?.low_risk_count || 0,
          totalAssessments: fullData.analytics?.total_assessments || 0
        })

        // Set chart data directly from combined response
        if (fullData.age_distribution) {
          setAgeDistribution(fullData.age_distribution)
        }
        if (fullData.risk_trend) {
          setRiskTrend(fullData.risk_trend)
        }
        if (fullData.vital_stats) {
          setVitalStats(fullData.vital_stats)
        }

        return // Success with combined endpoint
      } catch (combinedError) {
        console.log('Combined endpoint not available, falling back to separate calls:', combinedError.message)
      }

      // FALLBACK: Use parallel fetching with Promise.all (still faster than sequential)
      const [analyticsRes, mothersRes, risksRes] = await Promise.all([
        apiCall('GET', '/analytics/dashboard'),
        apiCall('GET', '/mothers'),
        apiCall('GET', '/risk/all').catch(() => ({ data: [] }))
      ])

      console.log('Analytics response (parallel fetch):', analyticsRes)

      setAnalytics({
        totalMothers: analyticsRes.total_mothers || 0,
        highRiskCount: analyticsRes.high_risk_count || 0,
        moderateRiskCount: analyticsRes.moderate_risk_count || 0,
        lowRiskCount: analyticsRes.low_risk_count || 0,
        totalAssessments: analyticsRes.total_assessments || 0
      })

      // Process chart data from parallel results
      processChartData(mothersRes.data || [], risksRes.data || [])

    } catch (error) {
      console.error('Failed to load analytics:', error.message)
      showMessage('Failed to refresh analytics', 'error')
    } finally {
      setChartsLoading(false)
    }
  }

  // Helper function to process chart data (used as fallback)
  const processChartData = (mothersData, allAssessments) => {
    // Age Distribution
    const ageGroups = {
      '15-20': 0,
      '20-25': 0,
      '25-30': 0,
      '30-35': 0,
      '35-40': 0,
      '40+': 0
    }

    mothersData.forEach(m => {
      if (m.age >= 15 && m.age < 20) ageGroups['15-20']++
      else if (m.age >= 20 && m.age < 25) ageGroups['20-25']++
      else if (m.age >= 25 && m.age < 30) ageGroups['25-30']++
      else if (m.age >= 30 && m.age < 35) ageGroups['30-35']++
      else if (m.age >= 35 && m.age < 40) ageGroups['35-40']++
      else ageGroups['40+']++
    })

    const ageData = Object.entries(ageGroups).map(([age, count]) => ({
      name: age,
      value: count
    }))
    setAgeDistribution(ageData)

    // Risk Trend (last 7 days)
    const sortedAssessments = allAssessments.sort((a, b) =>
      new Date(a.created_at) - new Date(b.created_at)
    )

    const dailyRisk = {}
    sortedAssessments.forEach(assessment => {
      const date = new Date(assessment.created_at).toLocaleDateString()
      if (!dailyRisk[date]) {
        dailyRisk[date] = { date, HIGH: 0, MODERATE: 0, LOW: 0 }
      }
      dailyRisk[date][assessment.risk_level]++
    })

    const riskData = Object.values(dailyRisk).slice(-7)
    setRiskTrend(riskData)

    // Vital Stats
    const vitals = {
      avgSystolic: 0,
      avgDiastolic: 0,
      avgHeartRate: 0,
      avgGlucose: 0,
      avgHemoglobin: 0
    }

    let systolicCount = 0, diastolicCount = 0, hrCount = 0, glucoseCount = 0, hbCount = 0

    allAssessments.forEach(assessment => {
      if (assessment.systolic_bp) {
        vitals.avgSystolic += assessment.systolic_bp
        systolicCount++
      }
      if (assessment.diastolic_bp) {
        vitals.avgDiastolic += assessment.diastolic_bp
        diastolicCount++
      }
      if (assessment.heart_rate) {
        vitals.avgHeartRate += assessment.heart_rate
        hrCount++
      }
      if (assessment.blood_glucose) {
        vitals.avgGlucose += assessment.blood_glucose
        glucoseCount++
      }
      if (assessment.hemoglobin) {
        vitals.avgHemoglobin += assessment.hemoglobin
        hbCount++
      }
    })

    const vitalData = [
      {
        name: 'Systolic BP',
        value: systolicCount > 0 ? Math.round(vitals.avgSystolic / systolicCount) : 0,
        normal: 120
      },
      {
        name: 'Diastolic BP',
        value: diastolicCount > 0 ? Math.round(vitals.avgDiastolic / diastolicCount) : 0,
        normal: 80
      },
      {
        name: 'Heart Rate',
        value: hrCount > 0 ? Math.round(vitals.avgHeartRate / hrCount) : 0,
        normal: 75
      },
      {
        name: 'Glucose',
        value: glucoseCount > 0 ? Math.round(vitals.avgGlucose / glucoseCount) : 0,
        normal: 100
      },
      {
        name: 'Hemoglobin',
        value: hbCount > 0 ? (vitals.avgHemoglobin / hbCount).toFixed(1) : 0,
        normal: 12
      }
    ]
    setVitalStats(vitalData)
  }


  const fetchMothers = async () => {
    try {
      setLoading(true)
      const response = await apiCall('GET', '/mothers')
      const mothersData = response.data || []

      // Fetch all assessments in a single request
      let allAssessments = []
      try {
        const allRes = await apiCall('GET', '/risk/all')
        allAssessments = allRes.data || []
      } catch (e) {
        console.log('Could not fetch assessments')
      }

      // Group assessments by mother_id
      const assessmentsByMother = {}
      allAssessments.forEach(assessment => {
        if (!assessmentsByMother[assessment.mother_id]) {
          assessmentsByMother[assessment.mother_id] = []
        }
        assessmentsByMother[assessment.mother_id].push(assessment)
      })

      // Attach assessments to each mother
      const mothersWithAssessments = mothersData.map(mother => {
        const assessments = assessmentsByMother[mother.id] || []
        return {
          ...mother,
          assessments: assessments,
          latestRisk: assessments.length > 0 ? assessments[0] : null
        }
      })

      setMothers(mothersWithAssessments)
    } catch (error) {
      showMessage('Failed to load mothers: ' + error.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleRegisterSubmit = async (e) => {
    e.preventDefault()
    try {
      setLoading(true)

      const gravida = parseInt(registerForm.gravida.split(' ')[1], 10)
      const parity = parseInt(registerForm.parity.split(' ')[1], 10)

      const payload = {
        name: registerForm.name,
        phone: registerForm.phone,
        age: parseInt(registerForm.age, 10),
        gravida: gravida,
        parity: parity,
        bmi: parseFloat(registerForm.bmi),
        location: registerForm.location,
        preferred_language: registerForm.preferred_language,
        telegram_chat_id: registerForm.telegram_chat_id || null
      }

      console.log('Sending register payload:', payload)
      await apiCall('POST', '/mothers/register', payload)

      showMessage('✅ Mother registered successfully!', 'success')

      setRegisterForm({
        name: '',
        phone: '',
        age: '',
        gravida: 'Gravida 1',
        parity: 'Parity 0',
        bmi: '',
        location: '',
        preferred_language: 'en',
        telegram_chat_id: ''
      })

      fetchAnalyticsData()
    } catch (error) {
      showMessage('❌ Error: ' + error.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleAssessRisk = async (e) => {
    e.preventDefault()
    if (!assessmentForm.mother_id) {
      showMessage('Please select a mother', 'error')
      return
    }

    try {
      setLoading(true)

      const payload = {
        mother_id: assessmentForm.mother_id,
        systolic_bp: assessmentForm.systolic_bp ? parseInt(assessmentForm.systolic_bp, 10) : null,
        diastolic_bp: assessmentForm.diastolic_bp ? parseInt(assessmentForm.diastolic_bp, 10) : null,
        heart_rate: assessmentForm.heart_rate ? parseInt(assessmentForm.heart_rate, 10) : null,
        blood_glucose: assessmentForm.blood_glucose ? parseFloat(assessmentForm.blood_glucose) : null,
        hemoglobin: assessmentForm.hemoglobin ? parseFloat(assessmentForm.hemoglobin) : null,
        proteinuria: 0,
        edema: 0,
        headache: 0,
        vision_changes: 0,
        epigastric_pain: 0,
        vaginal_bleeding: 0
      }

      console.log('Sending assessment payload:', payload)
      const response = await apiCall('POST', '/risk/assess', payload)

      setRiskResult(response)

      // Show message with Telegram notification status
      const telegramMsg = response.telegram_sent
        ? '📱 Report sent to mother via Telegram!'
        : ''
      showMessage(`✅ Risk assessment completed! ${telegramMsg}`, 'success')

      // Clear form
      setAssessmentForm({
        mother_id: '',
        systolic_bp: '',
        diastolic_bp: '',
        heart_rate: '',
        blood_glucose: '',
        hemoglobin: '',
        proteinuria: 0,
        edema: 0,
        headache: 0,
        vision_changes: 0,
        epigastric_pain: 0,
        vaginal_bleeding: 0
      })

      fetchAnalyticsData()
    } catch (error) {
      showMessage('❌ Error: ' + error.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleRegisterChange = (e) => {
    const { name, value } = e.target
    setRegisterForm(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleAssessmentChange = (e) => {
    const { name, value } = e.target

    if (name === 'mother_id') {
      setAssessmentForm({
        mother_id: value,
        systolic_bp: '',
        diastolic_bp: '',
        heart_rate: '',
        blood_glucose: '',
        hemoglobin: '',
        proteinuria: 0,
        edema: 0,
        headache: 0,
        vision_changes: 0,
        epigastric_pain: 0,
        vaginal_bleeding: 0
      })
      setRiskResult(null)
    } else {
      setAssessmentForm(prev => ({
        ...prev,
        [name]: value
      }))
    }
  }

  const showMessage = (text, type = 'info') => {
    setMessage({ text, type })
    setTimeout(() => setMessage(''), 4000)
  }

  const COLORS = {
    HIGH: '#ef4444',
    MODERATE: '#f59e0b',
    LOW: '#10b981',
    primary: '#6366f1',
    secondary: '#8b5cf6'
  }

  return (
    <div className={`${darkMode ? 'bg-[#1a1a2e]' : 'bg-[#f0f4f8]'} min-h-screen py-6 transition-colors`}>
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className={`text-2xl font-extrabold ${darkMode ? 'text-white' : 'text-gray-900'}`}>🏥 MaatruRaksha AI</h1>
            <p className={`${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>{t('maternal_system')}</p>
          </div>
          <button
            onClick={() => setDarkMode(!darkMode)}
            className={`px-4 py-2 rounded-lg font-semibold shadow-sm ${darkMode ? 'bg-gray-700 text-white hover:bg-gray-600' : 'bg-gray-200 text-gray-800 hover:bg-gray-300'}`}
            title={darkMode ? t('light_mode') : t('dark_mode')}
          >
            {darkMode ? `☀️ ${t('light')}` : `🌙 ${t('dark')}`}
          </button>
        </div>

        {message && (
          <div className={`fixed top-5 right-5 rounded-lg shadow-lg text-sm max-w-sm px-5 py-4 animate-fade-in ${message.type === 'success' ? 'bg-green-100 text-green-900 border border-green-200' :
            message.type === 'error' ? 'bg-red-100 text-red-900 border border-red-200' : 'bg-blue-100 text-blue-900 border border-blue-200'
            }`}>
            {message.text}
          </div>
        )}

        <div className={`mb-6 p-2 rounded-xl shadow ${darkMode ? 'bg-[#262641]' : 'bg-white'}`}>
          <div className="flex flex-wrap gap-2">
            {[
              { id: 'dashboard', label: `📊 ${t('dashboard')}` },
              { id: 'register', label: `➕ ${t('register')}` },
              { id: 'risk-assessment', label: `⚠️ ${t('risk_assessment')}` }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-5 py-2 rounded-lg font-semibold text-sm transition-colors ${activeTab === tab.id
                  ? 'bg-indigo-600 text-white'
                  : darkMode
                    ? 'bg-gray-700 text-gray-200 hover:bg-gray-600'
                    : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                  }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Dashboard Tab - With Analytics */}
        {activeTab === 'dashboard' && (
          <div className="flex flex-col gap-6">
            {/* Top KPI Cards */}
            <div>
              <div className="flex items-center justify-between mb-5 px-5 py-4 rounded-xl text-white bg-gradient-to-r from-indigo-600 to-purple-700">
                <h2 className="m-0 text-lg font-bold">📈 {t('health_analytics')}</h2>
                <div className="bg-white/20 px-4 py-2 rounded-lg text-base font-semibold">
                  {t('total_mothers')}: <strong>{analytics.totalMothers}</strong>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-white p-5 rounded-lg border-l-4 border-red-500 shadow">
                  <div className="text-xs text-gray-600 font-semibold mb-3">🔴 {t('high_risk')}</div>
                  <div className="text-4xl font-bold text-red-600">{analytics.highRiskCount}</div>
                </div>

                <div className="bg-white p-5 rounded-lg border-l-4 border-yellow-500 shadow">
                  <div className="text-xs text-gray-600 font-semibold mb-3">🟡 {t('moderate_risk')}</div>
                  <div className="text-4xl font-bold text-yellow-600">{analytics.moderateRiskCount}</div>
                </div>

                <div className="bg-white p-5 rounded-lg border-l-4 border-green-500 shadow">
                  <div className="text-xs text-gray-600 font-semibold mb-3">🟢 {t('low_risk')}</div>
                  <div className="text-4xl font-bold text-green-600">{analytics.lowRiskCount}</div>
                </div>

                <div className="bg-white p-5 rounded-lg border-l-4 border-blue-500 shadow">
                  <div className="text-xs text-gray-600 font-semibold mb-3">📋 {t('total_assessments')}</div>
                  <div className="text-4xl font-bold text-blue-600">{analytics.totalAssessments}</div>
                </div>
              </div>
            </div>

            {/* Charts Section */}
            <div className="flex flex-col gap-6">
              {/* Risk Trend Chart */}
              <div className={`${darkMode ? 'bg-[#262641]' : 'bg-white'} p-5 rounded-lg shadow transition-colors`}>
                <h3 className={`${darkMode ? 'text-white' : 'text-gray-900'} mb-4 text-base font-semibold`}>📊 {t('risk_trend')}</h3>
                {riskTrend.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={riskTrend} margin={{ top: 20, right: 30, left: 0, bottom: 60 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="date" angle={-45} textAnchor="end" height={80} tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }} />
                      <Legend wrapperStyle={{ paddingTop: '20px' }} />
                      <Bar dataKey="HIGH" stackId="a" fill={COLORS.HIGH} name={t('high_risk')} />
                      <Bar dataKey="MODERATE" stackId="a" fill={COLORS.MODERATE} name={t('moderate_risk')} />
                      <Bar dataKey="LOW" stackId="a" fill={COLORS.LOW} name={t('low_risk')} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-gray-600 text-center py-10">{t('no_assessment_data')}</p>
                )}
              </div>

              {/* Age Distribution & Risk Distribution */}
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
                <div className={`${darkMode ? 'bg-[#262641]' : 'bg-white'} p-5 rounded-lg shadow transition-colors`}>
                  <h3 className={`${darkMode ? 'text-white' : 'text-gray-900'} mb-4 text-base font-semibold`}>👶 {t('age_distribution')}</h3>
                  {ageDistribution.some(d => d.value > 0) ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie data={ageDistribution} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                          {ageDistribution.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={['#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899', '#f43f5e'][index % 6]} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="text-gray-600 text-center py-10">{t('no_data')}</p>
                  )}
                </div>

                <div className={`${darkMode ? 'bg-[#262641]' : 'bg-white'} p-5 rounded-lg shadow transition-colors`}>
                  <h3 className={`${darkMode ? 'text-white' : 'text-gray-900'} mb-4 text-base font-semibold`}>⚠️ {t('overall_risk_distribution')}</h3>
                  {analytics && (analytics.highRiskCount + analytics.moderateRiskCount + analytics.lowRiskCount) > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={[
                            { name: t('high_risk'), value: analytics.highRiskCount },
                            { name: t('moderate_risk'), value: analytics.moderateRiskCount },
                            { name: t('low_risk'), value: analytics.lowRiskCount }
                          ]}
                          dataKey="value"
                          cx="50%"
                          cy="50%"
                          outerRadius={80}
                          label
                        >
                          <Cell fill={COLORS.HIGH} />
                          <Cell fill={COLORS.MODERATE} />
                          <Cell fill={COLORS.LOW} />
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="text-gray-600 text-center py-10">{t('no_data')}</p>
                  )}
                </div>
              </div>

              {/* Vital Signs Chart */}
              <div className={`${darkMode ? 'bg-[#262641]' : 'bg-white'} p-5 rounded-lg shadow transition-colors`}>
                <h3 className={`${darkMode ? 'text-white' : 'text-gray-900'} mb-4 text-base font-semibold`}>💓 {t('avg_vitals_vs_normal')}</h3>
                {vitalStats.some(v => v.value > 0) ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={vitalStats} margin={{ top: 20, right: 30, left: 0, bottom: 100 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="name" angle={-45} textAnchor="end" height={120} tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }} />
                      <Legend wrapperStyle={{ paddingTop: '20px' }} />
                      <Bar dataKey="value" fill={COLORS.primary} name={t('average_value')} />
                      <Bar dataKey="normal" fill={COLORS.secondary} name={t('normal_range')} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-gray-600 text-center py-10">{t('no_vitals')}</p>
                )}
              </div>

              {/* Refresh Button */}
              <div className="flex justify-center gap-3">
                <button
                  onClick={fetchAnalyticsData}
                  disabled={chartsLoading}
                  className="px-6 py-3 bg-indigo-600 text-white rounded-lg font-semibold text-sm disabled:opacity-60 disabled:cursor-not-allowed hover:bg-indigo-700 transition"
                >
                  {chartsLoading ? `⏳ ${t('refreshing')}` : `🔄 ${t('refresh_analytics')}`}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Register Tab */}
        {activeTab === 'register' && (
          <div className={`${darkMode ? 'bg-[#262641]' : 'bg-white'} p-6 rounded-lg shadow max-w-[600px] transition-colors`}>
            <h2 className={`${darkMode ? 'text-white' : 'text-gray-900'} mb-2`}>📝 {t('register_pregnant_mother')}</h2>
            <p className={`${darkMode ? 'text-gray-400' : 'text-gray-600'} mb-5 text-sm`}>{t('register_helptext')}</p>

            <form onSubmit={handleRegisterSubmit}>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className={`${darkMode ? 'text-gray-200' : 'text-gray-700'} block text-sm font-semibold mb-1`}>{t('full_name')} *</label>
                  <input type="text" name="name" placeholder={t('full_name_placeholder')} value={registerForm.name} onChange={handleRegisterChange} required className={`w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent ${darkMode ? 'bg-[#1a1a2e] text-white border-gray-700' : 'bg-white text-black border-gray-300'}`} />
                </div>
                <div>
                  <label className="text-gray-700 block text-sm font-semibold mb-1">📱 {t('phone_number')} *</label>
                  <input type="tel" name="phone" placeholder="9876543210" value={registerForm.phone} onChange={handleRegisterChange} required className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent" />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="text-gray-700 block text-sm font-semibold mb-1">👤 {t('age_years')} *</label>
                  <input type="number" name="age" placeholder="28" value={registerForm.age} onChange={handleRegisterChange} required className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent" />
                </div>
                <div>
                  <label className="text-gray-700 block text-sm font-semibold mb-1">⚖️ {t('bmi')} *</label>
                  <input type="number" name="bmi" placeholder="22.5" step="0.1" value={registerForm.bmi} onChange={handleRegisterChange} required className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent" />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="text-gray-700 block text-sm font-semibold mb-1">{t('gravida')}</label>
                  <select name="gravida" value={registerForm.gravida} onChange={handleRegisterChange} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent">
                    <option>Gravida 1</option>
                    <option>Gravida 2</option>
                    <option>Gravida 3</option>
                  </select>
                </div>
                <div>
                  <label className="text-gray-700 block text-sm font-semibold mb-1">{t('parity')}</label>
                  <select name="parity" value={registerForm.parity} onChange={handleRegisterChange} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent">
                    <option>Parity 0</option>
                    <option>Parity 1</option>
                    <option>Parity 2</option>
                  </select>
                </div>
              </div>

              <div className="mb-4">
                <label className="text-gray-700 block text-sm font-semibold mb-1">📍 {t('location')} *</label>
                <input type="text" name="location" placeholder="e.g., Dharavi, Mumbai" value={registerForm.location} onChange={handleRegisterChange} required className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent" />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="text-gray-700 block text-sm font-semibold mb-1">🌍 {t('preferred_language')}</label>
                  <select name="preferred_language" value={registerForm.preferred_language} onChange={handleRegisterChange} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent">
                    <option value="en">English</option>
                    <option value="mr">Marathi</option>
                    <option value="hi">Hindi</option>
                  </select>
                </div>
                <div>
                  <label className="text-gray-700 block text-sm font-semibold mb-1">💬 {t('telegram_chat_id')}</label>
                  <input type="text" name="telegram_chat_id" placeholder="Optional: Chat ID" value={registerForm.telegram_chat_id} onChange={handleRegisterChange} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent" />
                </div>
              </div>

              <button type="submit" disabled={loading} className="w-full px-4 py-3 bg-indigo-600 text-white rounded-lg font-semibold text-sm disabled:opacity-60 disabled:cursor-not-allowed hover:bg-indigo-700 transition">
                {loading ? t('registering') : t('register_mother')}
              </button>
            </form>
          </div>
        )}

        {/* Risk Assessment Tab */}
        {activeTab === 'risk-assessment' && (
          <div className="bg-white p-6 rounded-lg shadow max-w-[600px]">
            <h2 className="mb-4 text-gray-900">⚕️ {t('risk_assessment')}</h2>

            <form onSubmit={handleAssessRisk}>
              <div className="mb-4">
                <label className="text-gray-700 block text-sm font-semibold mb-1">{t('select_mother')} *</label>
                <select name="mother_id" value={assessmentForm.mother_id} onChange={handleAssessmentChange} required className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent">
                  <option value="">{t('choose_mother')}</option>
                  {mothers.map(mother => (
                    <option key={mother.id} value={mother.id}>{mother.name} ({mother.phone})</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="text-gray-700 block text-sm font-semibold mb-1">{t('systolic_bp')}</label>
                  <input type="number" name="systolic_bp" placeholder="120" value={assessmentForm.systolic_bp} onChange={handleAssessmentChange} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent" />
                </div>
                <div>
                  <label className="text-gray-700 block text-sm font-semibold mb-1">{t('diastolic_bp')}</label>
                  <input type="number" name="diastolic_bp" placeholder="80" value={assessmentForm.diastolic_bp} onChange={handleAssessmentChange} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent" />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="text-gray-700 block text-sm font-semibold mb-1">{t('heart_rate')}</label>
                  <input type="number" name="heart_rate" placeholder="80" value={assessmentForm.heart_rate} onChange={handleAssessmentChange} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent" />
                </div>
                <div>
                  <label className="text-gray-700 block text-sm font-semibold mb-1">{t('blood_glucose')}</label>
                  <input type="number" name="blood_glucose" placeholder="100" value={assessmentForm.blood_glucose} onChange={handleAssessmentChange} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent" />
                </div>
              </div>

              <div className="mb-4">
                <h4 className="text-gray-900 mb-3 font-semibold">{t('clinical_symptoms_optional')}</h4>
                <div className="grid [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))] gap-3 bg-gray-50 p-3 rounded-lg">
                  {[
                    { key: 'proteinuria', label: t('proteinuria') },
                    { key: 'edema', label: t('edema') },
                    { key: 'headache', label: t('headache') },
                    { key: 'vision_changes', label: t('vision_changes') },
                    { key: 'epigastric_pain', label: t('epigastric_pain') },
                    { key: 'vaginal_bleeding', label: t('vaginal_bleeding') }
                  ].map(symptom => (
                    <label key={symptom.key} className="flex items-center gap-2 cursor-pointer text-sm">
                      <input
                        type="checkbox"
                        checked={assessmentForm[symptom.key] === 1}
                        onChange={(e) => {
                          setAssessmentForm(prev => ({
                            ...prev,
                            [symptom.key]: e.target.checked ? 1 : 0
                          }))
                        }}
                        className="w-4 h-4 cursor-pointer"
                      />
                      <span>{symptom.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              <button type="submit" disabled={loading} className="w-full px-4 py-3 bg-indigo-600 text-white rounded-lg font-semibold text-sm disabled:opacity-60 disabled:cursor-not-allowed hover:bg-indigo-700 transition">
                {loading ? t('assessing') : t('assess_risk')}
              </button>
            </form>

            {riskResult && (
              <div className={`mt-5 p-4 rounded-lg border ${riskResult.risk_level === 'HIGH'
                ? 'bg-red-50 border-red-200 text-red-800'
                : riskResult.risk_level === 'MODERATE'
                  ? 'bg-yellow-50 border-yellow-200 text-yellow-800'
                  : 'bg-green-50 border-green-200 text-green-800'
                }`}>
                <h3 className="mb-3 font-bold">
                  {riskResult.risk_level === 'HIGH' ? '🔴' : riskResult.risk_level === 'MODERATE' ? '🟡' : '🟢'}
                  {' '}{t('risk_assessment_result')}
                </h3>
                <div className="space-y-2">
                  <p><strong>{t('risk_score')}:</strong> {(riskResult.risk_score * 100).toFixed(1)}%</p>
                  <p><strong>{t('risk_level')}:</strong> <span className="font-bold">{riskResult.risk_level}</span></p>
                  <p><strong>{t('risk_factors')}:</strong> {riskResult.risk_factors?.join(', ') || t('none')}</p>
                  {riskResult.telegram_sent && (
                    <p className="mt-3 p-2 bg-blue-100 rounded text-blue-800">
                      📱 <strong>Summary sent to mother via Telegram!</strong>
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
