// FILE: frontend/src/utils/helpers.js

/**
 * Format risk score to percentage
 */
export const formatRiskScore = (score) => {
  if (!score) return '0%'
  return `${(score * 100).toFixed(0)}%`
}

/**
 * Get risk status based on score
 */
export const getRiskStatus = (score) => {
  if (score >= 0.7) return 'High Risk'
  if (score >= 0.4) return 'Moderate Risk'
  return 'Low Risk'
}

/**
 * Get color class for risk status
 */
export const getRiskColor = (score) => {
  if (score >= 0.7) return 'bg-red-50 border-red-200 text-red-900'
  if (score >= 0.4) return 'bg-yellow-50 border-yellow-200 text-yellow-900'
  return 'bg-green-50 border-green-200 text-green-900'
}

/**
 * Get badge color class for risk status
 */
export const getRiskBadgeColor = (status) => {
  if (status === 'High Risk') return 'bg-red-500'
  if (status === 'Moderate Risk') return 'bg-yellow-500'
  return 'bg-green-500'
}

/**
 * Format date to readable format
 */
export const formatDate = (date) => {
  if (!date) return 'N/A'
  const d = new Date(date)
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

/**
 * Format date and time
 */
export const formatDateTime = (date) => {
  if (!date) return 'N/A'
  const d = new Date(date)
  return d.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * Validate phone number format
 */
export const validatePhone = (phone) => {
  const phoneRegex = /^[6-9]\d{9}$/
  return phoneRegex.test(phone.replace(/\D/g, ''))
}

/**
 * Validate email format
 */
export const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * Validate vital signs
 */
export const validateVitals = (vitals) => {
  const { bp_sys, bp_dia, sugar_level, hemoglobin } = vitals
  
  const errors = []
  
  if (bp_sys < 60 || bp_sys > 200) {
    errors.push('Systolic BP must be between 60-200 mmHg')
  }
  
  if (bp_dia < 40 || bp_dia > 130) {
    errors.push('Diastolic BP must be between 40-130 mmHg')
  }
  
  if (sugar_level < 40 || sugar_level > 400) {
    errors.push('Blood sugar must be between 40-400 mg/dL')
  }
  
  if (hemoglobin < 5 || hemoglobin > 20) {
    errors.push('Hemoglobin must be between 5-20 g/dL')
  }
  
  return errors
}

/**
 * Generate recommendation based on risk score
 */
export const generateRecommendation = (status) => {
  const recommendations = {
    'High Risk': 'URGENT: Immediate referral to district hospital. Specialist consultation within 24 hours. Consider admission for monitoring.',
    'Moderate Risk': 'Schedule follow-up visit within 1 week. Increase monitoring frequency. Coordinate with PHC/specialist.',
    'Low Risk': 'Continue routine antenatal care. Standard follow-up schedule. Home-based wellness monitoring.'
  }
  return recommendations[status] || 'Consult healthcare provider'
}

/**
 * Copy to clipboard
 */
export const copyToClipboard = (text) => {
  navigator.clipboard.writeText(text)
    .then(() => console.log('Copied to clipboard'))
    .catch(err => console.error('Failed to copy:', err))
}

/**
 * Get random ID
 */
export const getRandomId = () => {
  return 'id-' + Math.random().toString(36).substr(2, 9)
}

/**
 * Delay function for async operations
 */
export const delay = (ms) => {
  return new Promise(resolve => setTimeout(resolve, ms))
}