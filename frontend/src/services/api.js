// FILE: frontend/src/services/api.js
import axios from 'axios'
import { supabase } from './auth'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Attach Supabase access token for protected backend routes
api.interceptors.request.use(
  async (config) => {
    try {
      // Try to get token from localStorage first (faster, no async wait)
      const keys = Object.keys(localStorage).filter(k => k.startsWith('sb-') && k.endsWith('-auth-token'))
      if (keys.length > 0) {
        const stored = localStorage.getItem(keys[0])
        if (stored) {
          const parsed = JSON.parse(stored)
          const token = parsed?.access_token
          if (token) {
            config.headers = config.headers || {}
            config.headers['Authorization'] = `Bearer ${token}`
            return config
          }
        }
      }

      // Fallback: try getSession with short timeout
      const sessionPromise = supabase.auth.getSession()
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Session timeout')), 2000)
      )

      const { data: { session } } = await Promise.race([sessionPromise, timeoutPromise])
      const token = session?.access_token
      if (token) {
        config.headers = config.headers || {}
        config.headers['Authorization'] = `Bearer ${token}`
      }
    } catch (err) {
      console.warn('Auth interceptor:', err.message)
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Rate limiting / Retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1s

// Error handling interceptor with RETRY logic
api.interceptors.response.use(
  response => response,
  async error => {
    const { config, response } = error;

    // Check if we should retry (idempotent methods or specifically allowed)
    // Retry on Network Errors or 5xx Server Errors
    const shouldRetry = config && !config._retry && (
      !response || // Network error
      (response.status >= 500 && response.status < 600) // Server error
    );

    if (shouldRetry) {
      config._retry = true;
      config._retryCount = (config._retryCount || 0) + 1;

      if (config._retryCount <= MAX_RETRIES) {
        // Exponential backoff
        const delay = RETRY_DELAY * Math.pow(2, config._retryCount - 1);
        console.warn(`Attempt ${config._retryCount} failed. Retrying in ${delay}ms...`);

        await new Promise(resolve => setTimeout(resolve, delay));
        return api(config);
      }
    }

    // Global Error Logging / Toast could go here
    console.error('API Error:', error.response?.data || error.message);
    console.error('Status:', response?.status);

    return Promise.reject(error);
  }
)

// ==================== MOTHER API ====================
export const motherAPI = {
  // Register a new mother
  register: async (data) => {
    try {
      // Ensure proper data types
      const payload = {
        name: String(data.name).trim(),
        phone: String(data.phone).trim(),
        age: parseInt(data.age, 10),
        gravida: parseInt(data.gravida, 10),
        parity: parseInt(data.parity, 10),
        bmi: parseFloat(data.bmi),
        location: String(data.location).trim(),
        preferred_language: String(data.preferred_language).trim() || 'en',
        telegram_chat_id: data.telegram_chat_id ? String(data.telegram_chat_id).trim() : null
      }

      console.log('Registering mother with payload:', payload)
      const response = await api.post('/mothers/register', payload)
      return response
    } catch (error) {
      console.error('Registration error:', error.response?.data || error.message)
      throw error
    }
  },

  // Get all mothers
  getAll: async () => {
    try {
      const response = await api.get('/mothers')
      return response
    } catch (error) {
      console.error('Get mothers error:', error.response?.data || error.message)
      throw error
    }
  },

  // Get mother by ID
  getById: async (id) => {
    try {
      const response = await api.get(`/mothers/${id}`)
      return response
    } catch (error) {
      console.error('Get mother error:', error.response?.data || error.message)
      throw error
    }
  }
}

export const authAPI = {
  createRegisterRequest: async (payload) => {
    const res = await api.post('/auth/register-request', payload)
    return res
  },
  uploadCertification: async (email, file) => {
    const form = new FormData()
    form.append('email', email)
    form.append('file', file)
    const res = await api.post('/auth/upload-cert', form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return res
  },
  listRegisterRequests: async () => {
    const res = await api.get('/auth/register-requests')
    return res
  },
  decideRegisterRequest: async (id, approved, note) => {
    const res = await api.post(`/auth/register-requests/${id}/decision`, { approved, note })
    return res
  },
  // Pending OAuth users (users with NULL role)
  listPendingUsers: async () => {
    const res = await api.get('/auth/pending-users')
    return res
  },
  assignRoleToPendingUser: async (userId, role) => {
    const res = await api.post(`/auth/pending-users/${userId}/assign-role`, { role })
    return res
  },
  rejectPendingUser: async (userId) => {
    const res = await api.delete(`/auth/pending-users/${userId}`)
    return res
  },
  // New role-based registration requests (from AuthCallback)
  listRoleRequests: async () => {
    // Maps to backend list_register_requests
    const res = await api.get('/auth/register-requests')
    return res
  },
  approveRoleRequest: async (requestId, role) => {
    // Maps to backend decide_register_request with approved=true
    // Note: 'role' param is ignored by backend (it uses requested_role), 
    // but we can pass it if backend logic changes.
    const res = await api.post(`/auth/register-requests/${requestId}/decision`, {
      approved: true,
      note: "Approved via Admin Dashboard"
    })
    return res
  },
  rejectRoleRequest: async (requestId, reason) => {
    // Maps to backend decide_register_request with approved=false
    const res = await api.post(`/auth/register-requests/${requestId}/decision`, {
      approved: false,
      note: reason
    })
    return res
  }
}

// ==================== CERTIFICATE VERIFICATION API ====================
export const certificateAPI = {
  // Verify doctor certificate (multilingual - any language)
  verifyDoctorCertificate: async (file) => {
    const form = new FormData()
    form.append('file', file)
    const res = await api.post('/api/v1/certificates/verify', form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return res
  },

  // Parse certificate only (no verification)
  parseCertificate: async (file) => {
    const form = new FormData()
    form.append('file', file)
    const res = await api.post('/api/v1/certificates/parse', form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return res
  },

  // Parse ID document (PAN/Aadhaar/DL - any language)
  parseIDDocument: async (file) => {
    const form = new FormData()
    form.append('file', file)
    const res = await api.post('/api/v1/certificates/id-document/parse', form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return res
  },

  // Validate ASHA worker ID (includes hidden age validation)
  validateAshaID: async (file) => {
    const form = new FormData()
    form.append('file', file)
    const res = await api.post('/api/v1/certificates/id-document/validate-asha', form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return res
  },

  // Get NMC lookup guidance
  getNMCLookup: async (registrationNumber, doctorName = null) => {
    const params = new URLSearchParams()
    params.append('registration_number', registrationNumber)
    if (doctorName) params.append('doctor_name', doctorName)
    const res = await api.get(`/api/v1/certificates/nmc-lookup?${params}`)
    return res
  }
}

export { api }

// ==================== RISK ASSESSMENT API ====================
export const riskAPI = {
  // Assess risk for a mother
  assess: async (data) => {
    try {
      // Ensure proper data types
      const payload = {
        mother_id: String(data.mother_id).trim(),
        systolic_bp: data.systolic_bp ? parseInt(data.systolic_bp, 10) : null,
        diastolic_bp: data.diastolic_bp ? parseInt(data.diastolic_bp, 10) : null,
        heart_rate: data.heart_rate ? parseInt(data.heart_rate, 10) : null,
        blood_glucose: data.blood_glucose ? parseFloat(data.blood_glucose) : null,
        hemoglobin: data.hemoglobin ? parseFloat(data.hemoglobin) : null,
        proteinuria: parseInt(data.proteinuria, 10) || 0,
        edema: parseInt(data.edema, 10) || 0,
        headache: parseInt(data.headache, 10) || 0,
        vision_changes: parseInt(data.vision_changes, 10) || 0,
        epigastric_pain: parseInt(data.epigastric_pain, 10) || 0,
        vaginal_bleeding: parseInt(data.vaginal_bleeding, 10) || 0,
        notes: data.notes ? String(data.notes).trim() : null
      }

      console.log('Assessing risk with payload:', payload)
      const response = await api.post('/risk/assess', payload)
      return response
    } catch (error) {
      console.error('Risk assessment error:', error.response?.data || error.message)
      throw error
    }
  },

  // Get all risk assessments
  getAll: async () => {
    try {
      const response = await api.get('/risk/all')
      return response
    } catch (error) {
      console.error('Get assessments error:', error.response?.data || error.message)
      throw error
    }
  },

  // Get risk for specific mother
  getByMotherId: async (motherId) => {
    try {
      const response = await api.get(`/risk/mother/${motherId}`)
      return response
    } catch (error) {
      console.error('Get risk error:', error.response?.data || error.message)
      throw error
    }
  }
}

// ==================== ANALYTICS API ====================
export const analyticsAPI = {
  // Get dashboard analytics
  getDashboard: async () => {
    try {
      const response = await api.get('/analytics/dashboard')
      return response
    } catch (error) {
      console.error('Analytics error:', error.response?.data || error.message)
      throw error
    }
  },

  // Get risk distribution
  getRiskDistribution: async () => {
    try {
      const response = await api.get('/analytics/risk-distribution')
      return response
    } catch (error) {
      console.error('Risk distribution error:', error.response?.data || error.message)
      throw error
    }
  }
}

// ==================== APPOINTMENT API ====================
export const appointmentAPI = {
  // Create appointment
  create: async (data) => {
    try {
      const payload = {
        mother_id: String(data.mother_id).trim(),
        facility: String(data.facility).trim(),
        appointment_date: String(data.appointment_date).trim(),
        appointment_time: String(data.appointment_time).trim(),
        purpose: data.purpose ? String(data.purpose).trim() : null,
        notes: data.notes ? String(data.notes).trim() : null
      }

      const response = await api.post('/appointments/create', payload)
      return response
    } catch (error) {
      console.error('Create appointment error:', error.response?.data || error.message)
      throw error
    }
  }
}

// ==================== VISIT API ====================
export const visitAPI = {
  // Record visit
  record: async (data) => {
    try {
      const payload = {
        mother_id: String(data.mother_id).trim(),
        visit_date: data.visit_date || new Date().toISOString(),
        systolic_bp: data.systolic_bp ? parseInt(data.systolic_bp, 10) : null,
        diastolic_bp: data.diastolic_bp ? parseInt(data.diastolic_bp, 10) : null,
        heart_rate: data.heart_rate ? parseInt(data.heart_rate, 10) : null,
        blood_glucose: data.blood_glucose ? parseFloat(data.blood_glucose) : null,
        hemoglobin: data.hemoglobin ? parseFloat(data.hemoglobin) : null,
        weight: data.weight ? parseFloat(data.weight) : null,
        notes: data.notes ? String(data.notes).trim() : null
      }

      const response = await api.post('/visits/record', payload)
      return response
    } catch (error) {
      console.error('Record visit error:', error.response?.data || error.message)
      throw error
    }
  }
}

export async function queryAgent({ motherId, query, useContext = true, language = 'en' }) {
  try {
    const payload = {
      mother_id: motherId,
      query,
      use_context: useContext,
      language,
    };
    const { data } = await api.post('/api/v1/agent/query', payload);
    return data;
  } catch (error) {
    console.error('Error querying agent:', error);
    throw error;
  }
}

// ==================== ADMIN API ====================
export const adminAPI = {
  // Get all doctors with their assigned mothers count
  getDoctors: async () => {
    const res = await api.get('/api/admin/doctors')
    return res
  },

  // Get all ASHA workers with their assigned mothers count
  getAshaWorkers: async () => {
    const res = await api.get('/api/admin/asha-workers')
    return res
  },

  // Get all mothers with assignments
  getMothers: async () => {
    const res = await api.get('/api/admin/mothers')
    return res
  },

  // Update doctor info
  updateDoctor: async (id, data) => {
    const res = await api.put(`/api/admin/doctors/${id}`, data)
    return res
  },

  // Delete doctor
  deleteDoctor: async (id) => {
    const res = await api.delete(`/api/admin/doctors/${id}`)
    return res
  },

  // Update ASHA worker info
  updateAshaWorker: async (id, data) => {
    const res = await api.put(`/api/admin/asha-workers/${id}`, data)
    return res
  },

  // Delete ASHA worker
  deleteAshaWorker: async (id) => {
    const res = await api.delete(`/api/admin/asha-workers/${id}`)
    return res
  },

  // Assign mother to ASHA worker
  assignMotherToAsha: async (motherId, ashaId) => {
    const res = await api.post(`/api/admin/mothers/${motherId}/assign-asha`, { asha_worker_id: ashaId })
    return res
  },

  // Assign mother to doctor
  assignMotherToDoctor: async (motherId, doctorId) => {
    const res = await api.post(`/api/admin/mothers/${motherId}/assign-doctor`, { doctor_id: doctorId })
    return res
  },

  // Send email alert to assigned doctor and ASHA worker
  sendAlert: async (motherId, alertType = 'emergency') => {
    const res = await api.post(`/api/admin/mothers/${motherId}/send-alert`, { alert_type: alertType })
    return res
  },

  // Get dashboard stats
  getStats: async () => {
    const res = await api.get('/api/admin/stats')
    return res
  },

  // Get all admin data in one call (OPTIMIZED)
  getFull: async () => {
    const res = await api.get('/api/admin/full')
    return res
  },

  // ==================== SantanRaksha (Children) ====================

  // Get all children with mother info
  getChildren: async () => {
    const res = await api.get('/api/admin/children')
    return res
  },

  // Get SantanRaksha statistics
  getSantanRakshaStats: async () => {
    const res = await api.get('/api/admin/santanraksha-stats')
    return res
  },

  // Update child info
  updateChild: async (id, data) => {
    const res = await api.put(`/api/admin/children/${id}`, data)
    return res
  },

  // Delete child
  deleteChild: async (id) => {
    const res = await api.delete(`/api/admin/children/${id}`)
    return res
  }
}


// ==================== NEW: POSTNATAL CARE API ====================

export const postnatalAPI = {
  /**
   * Get list of postnatal mothers
   * @param {number} ashaWorkerId - Filter by ASHA worker
   * @param {number} doctorId - Filter by doctor
   * @param {number} limit - Results per page (default: 50)
   * @param {number} offset - Pagination offset (default: 0)
   */
  getMothers: async (ashaWorkerId = null, doctorId = null, limit = 50, offset = 0) => {
    const params = new URLSearchParams();
    if (ashaWorkerId) params.append('asha_worker_id', ashaWorkerId);
    if (doctorId) params.append('doctor_id', doctorId);
    params.append('limit', limit);
    params.append('offset', offset);

    const response = await api.get(`/api/postnatal/mothers?${params}`);
    return response.data;
  },

  /**
   * Get list of children
   * @param {string} motherId - Filter by mother
   * @param {number} ashaWorkerId - Filter by ASHA worker
   * @param {number} doctorId - Filter by doctor
   */
  getChildren: async (motherId = null, ashaWorkerId = null, doctorId = null) => {
    const params = new URLSearchParams();
    if (motherId) params.append('mother_id', motherId);
    if (ashaWorkerId) params.append('asha_worker_id', ashaWorkerId);
    if (doctorId) params.append('doctor_id', doctorId);

    const response = await api.get(`/api/postnatal/children?${params}`);
    return response.data;
  },

  /**
   * Register a new child
   * @param {object} childData - Child registration data
   */
  registerChild: async (childData) => {
    const response = await api.post('/api/postnatal/children', childData);
    return response.data;
  },

  /**
   * Create a mother postnatal assessment
   * @param {object} assessmentData - Assessment data
   */
  createMotherAssessment: async (assessmentData) => {
    const response = await api.post('/api/postnatal/assessments/mother', assessmentData);
    return response.data;
  },

  /**
   * Create a child health assessment
   * @param {object} assessmentData - Assessment data
   */
  createChildAssessment: async (assessmentData) => {
    const response = await api.post('/api/postnatal/assessments/child', assessmentData);
    return response.data;
  },

  /**
   * Get assessment history for a mother/child
   * @param {string} motherId - Mother ID
   * @param {string} childId - Optional child ID
   * @param {number} limit - Number of assessments
   */
  getAssessmentHistory: async (motherId, childId = null, limit = 50) => {
    if (childId) {
      const response = await api.get(`/api/postnatal/children/${childId}/assessments?limit=${limit}`);
      return response.data;
    } else {
      // Fallback for mother - assuming an endpoint exists or using generic
      // We need to implement GET /api/postnatal/mothers/{id}/assessments if not exists
      // For now, let's try the generic path if it was working for mothers, or fallback
      const response = await api.get(`/api/postnatal/mothers/${motherId}/assessments?limit=${limit}`);
      return response.data;
    }
  },

  /**
   * Get vaccinations for a child
   * @param {string} childId 
   */
  getVaccinations: async (childId, limit = 50) => {
    const response = await api.get(`/api/postnatal/children/${childId}/vaccinations?limit=${limit}`);
    return response.data;
  },

  /**
   * Record a vaccination
   * @param {object} data
   */
  recordVaccination: async (data) => {
    const response = await api.post('/api/postnatal/vaccinations', data);
    return response.data;
  },

  /**
   * Get growth records for a child
   * @param {string} childId 
   */
  getGrowthRecords: async (childId, limit = 20) => {
    const response = await api.get(`/api/postnatal/children/${childId}/growth?limit=${limit}`);
    return response.data;
  },

  /**
   * Record a growth measurement
   * @param {object} data
   */
  recordGrowth: async (data) => {
    const response = await api.post('/api/postnatal/growth', data);
    return response.data;
  }
};

// ==================== EXPORTS ====================


export default api

