import React, { useState } from 'react'
import { AlertCircle, Phone, MapPin, CheckCircle } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { SYMPTOMS } from '../utils/constants'
import { showToast } from '../utils/FixedPatterns';

export default function Emergency() {
  const { t } = useTranslation()
  const [selectedSymptoms, setSelectedSymptoms] = useState([])
  const [motherName, setMotherName] = useState('')
  const [location, setLocation] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const handleSymptomToggle = (symptom) => {
    setSelectedSymptoms(prev =>
      prev.includes(symptom)
        ? prev.filter(s => s !== symptom)
        : [...prev, symptom]
    )
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (selectedSymptoms.length === 0 || !motherName || !location) {
      showToast('Please fill all required fields', 'error')
      return
    }
    setSubmitted(true)
    setTimeout(() => {
      setSubmitted(false)
      setSelectedSymptoms([])
      setMotherName('')
      setLocation('')
    }, 3000)
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <div className="bg-red-500/10 border border-red-500/25 p-6 rounded-xl backdrop-blur-sm mb-8">
        <div className="flex items-center gap-4">
          <AlertCircle className="w-8 h-8 text-red-600" />
          <div>
            <h1 className="text-2xl font-bold text-red-700">{t('emergency_response')}</h1>
            <p className="text-red-600/80">{t('emergency_support_line')}</p>
          </div>
        </div>
      </div>

      {submitted ? (
        <div className="bg-emerald-500/10 border border-emerald-500/25 p-8 rounded-xl text-center backdrop-blur-sm">
          <CheckCircle className="w-16 h-16 text-emerald-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-emerald-600 mb-2">{t('emergency_alert_sent')}</h2>
          <p className="text-emerald-600/80 mb-4">
            {t('ambulance_on_way')}
          </p>
          <p className="text-emerald-600/80">{t('family_contacts_alerted')}</p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="glass-card-strong p-8 rounded-2xl space-y-6">
          <div>
            <label className="block text-sm font-medium text-slate-600 mb-2">{t('mother_name')} *</label>
            <input
              type="text"
              value={motherName}
              onChange={(e) => setMotherName(e.target.value)}
              className="glass-input w-full rounded-xl"
              placeholder={t('enter_mother_name')}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-600 mb-2">{t('location')} *</label>
            <div className="flex items-center gap-2">
              <MapPin className="w-5 h-5 text-slate-400" />
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="glass-input flex-1 rounded-xl"
                placeholder={t('current_location')}
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-600 mb-4">{t('select_symptoms')} *</label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {SYMPTOMS.map(symptom => (
                <label key={symptom} className="flex items-center gap-2 cursor-pointer p-2 rounded-lg hover:bg-white/600 transition-colors">
                  <input
                    type="checkbox"
                    checked={selectedSymptoms.includes(symptom)}
                    onChange={() => handleSymptomToggle(symptom)}
                    className="w-4 h-4 accent-red-500"
                  />
                  <span className="text-slate-600">{t(symptom)}</span>
                </label>
              ))}
            </div>
          </div>

          <button
            type="submit"
            className="w-full bg-gradient-to-r from-red-600 to-red-500 text-slate-800 font-bold py-3 rounded-xl hover:from-red-500 hover:to-red-400 transition-all shadow-lg shadow-red-500/25"
          >
            🚨 {t('trigger_emergency_alert')}
          </button>

          <div className="bg-yellow-500/10 border border-yellow-500/20 p-4 rounded-xl backdrop-blur-sm">
            <p className="text-yellow-700/80 text-sm">
              <strong className="text-yellow-700">{t('emergency_contacts')}:</strong><br />
              {t('ambulance')}: 108 | {t('emergency')}: 112
            </p>
          </div>
        </form>
      )}
    </div>
  )
}
