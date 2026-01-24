
/**
 * Application Constants
 */

export const API_ENDPOINTS = {
  MOTHERS: '/mothers',
  RISK: '/risk',
  CARE: '/care',
  NUTRITION: '/nutrition',
  MEDICATION: '/medication',
  EMERGENCY: '/emergency',
  ASHA: '/asha',
  TELEGRAM: '/telegram',
  DASHBOARD: '/dashboard'
}

export const LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'mr', name: 'Marathi (मराठी)' },
  { code: 'hi', name: 'Hindi (हिन्दी)' }
]

export const GRAVIDA_OPTIONS = [
  { value: '1', label: 'Gravida 1 (First pregnancy)' },
  { value: '2', label: 'Gravida 2' },
  { value: '3', label: 'Gravida 3+' }
]

export const PARITY_OPTIONS = [
  { value: '0', label: 'Parity 0' },
  { value: '1', label: 'Parity 1' },
  { value: '2', label: 'Parity 2+' }
]

export const RISK_TAGS = {
  PREECLAMPSIA: 'Preeclampsia',
  GDM: 'Gestational Diabetes',
  ANEMIA: 'Anemia',
  PRETERM_BIRTH: 'Preterm Birth Risk',
  IUGR: 'Intrauterine Growth Restriction'
}

export const SYMPTOMS = [
  'severe_bleeding',
  'unconsciousness',
  'seizures',
  'severe_headache',
  'abdominal_pain',
  'vision_changes',
  'dizziness',
  'mild_pain'
]

export const PRIORITY_LEVELS = ['Low', 'Medium', 'High']

export const APPOINTMENT_STATUS = [
  'pending',
  'confirmed',
  'completed',
  'cancelled'
]

export const TRIM_MONTHS = {
  1: 'First Trimester (1-3 months)',
  2: 'Second Trimester (4-6 months)',
  3: 'Third Trimester (7-9 months)'
}

export const BMI_CATEGORIES = {
  UNDERWEIGHT: { range: '< 18.5', category: 'Underweight' },
  NORMAL: { range: '18.5 - 24.9', category: 'Normal Weight' },
  OVERWEIGHT: { range: '25 - 29.9', category: 'Overweight' },
  OBESE: { range: '≥ 30', category: 'Obese' }
}

export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network error. Please check your internet connection.',
  SERVER_ERROR: 'Server error. Please try again later.',
  VALIDATION_ERROR: 'Please fill all required fields correctly.',
  NOT_FOUND: 'Resource not found.',
  UNAUTHORIZED: 'You are not authorized to perform this action.',
  UNKNOWN_ERROR: 'An unexpected error occurred. Please try again.'
}

export const SUCCESS_MESSAGES = {
  REGISTERED: 'Mother registered successfully!',
  RISK_ASSESSED: 'Risk assessment completed.',
  APPOINTMENT_SCHEDULED: 'Appointment scheduled successfully.',
  TELEGRAM_SENT: 'Message sent via Telegram.'
}

export const TELEGRAM_BOT_NAME = import.meta.env.VITE_TELEGRAM_BOT_NAME || 'MaatruRaksha_AI_bot'

export const NUTRITION_TEMPLATES = {
  VEG: {
    en: 'Whole grains, lentils, leafy greens, dairy, citrus fruits',
    mr: 'भाकरी, चणा, हिरवी भाजी, दूध, नारुळी',
    hi: 'अनाज, दाल, सब्जियां, दूध, नींबू'
  },
  NON_VEG: {
    en: 'Eggs, fish, chicken, lentils, vegetables, fruits',
    mr: 'अंडी, मासे, चिकन, दाल, भाजी, फळे',
    hi: 'अंडे, मछली, चिकन, दाल, सब्जियां, फल'
  }
}

export const FEATURES = {
  RISK_PREDICTION: 'Real-time Risk Prediction',
  CARE_COORDINATION: 'Automated Care Coordination',
  NUTRITION_GUIDANCE: 'Personalized Nutrition Plans',
  MEDICATION_TRACKING: 'Medication Adherence',
  EMERGENCY_RESPONSE: '24/7 Emergency Response',
  ASHA_SUPPORT: 'ASHA Worker Support',
  MULTILINGUAL: 'Multilingual Support',
  TELEGRAM_INTEGRATION: 'Telegram Notifications'
}