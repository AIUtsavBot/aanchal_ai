import React, { useState } from 'react'
import { AlertCircle, Phone, MapPin, CheckCircle } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { SYMPTOMS } from '../utils/constants'

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
      alert('Please fill all required fields')
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
      <div className="bg-red-100 border border-red-400 p-6 rounded-lg mb-8">
        <div className="flex items-center gap-4">
          <AlertCircle className="w-8 h-8 text-red-600" />
          <div>
            <h1 className="text-2xl font-bold text-red-900">{t('emergency_response')}</h1>
            <p className="text-red-700">{t('emergency_support_line')}</p>
          </div>
        </div>
      </div>

      {submitted ? (
        <div className="bg-green-100 border border-green-400 p-8 rounded-lg text-center">
          <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-green-900 mb-2">{t('emergency_alert_sent')}</h2>
          <p className="text-green-700 mb-4">
            {t('ambulance_on_way')}
          </p>
          <p className="text-green-700">{t('family_contacts_alerted')}</p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="bg-white p-8 rounded-lg shadow-lg space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">{t('mother_name')} *</label>
            <input
              type="text"
              value={motherName}
              onChange={(e) => setMotherName(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
              placeholder={t('enter_mother_name')}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">{t('location')} *</label>
            <div className="flex items-center gap-2">
              <MapPin className="w-5 h-5 text-gray-500" />
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                placeholder={t('current_location')}
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-4">{t('select_symptoms')} *</label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {SYMPTOMS.map(symptom => (
                <label key={symptom} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedSymptoms.includes(symptom)}
                    onChange={() => handleSymptomToggle(symptom)}
                    className="w-4 h-4"
                  />
                  <span className="text-gray-700">{t(symptom)}</span>
                </label>
              ))}
            </div>
          </div>

          <button
            type="submit"
            className="w-full bg-red-600 text-white font-bold py-3 rounded-lg hover:bg-red-700 transition"
          >
            🚨 {t('trigger_emergency_alert')}
          </button>

          <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
            <p className="text-yellow-800 text-sm">
              <strong>{t('emergency_contacts')}:</strong><br />
              {t('ambulance')}: 108 | {t('emergency')}: 112
            </p>
          </div>
        </form>
      )}
    </div>
  )
}
