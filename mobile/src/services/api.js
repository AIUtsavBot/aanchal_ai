// Aanchal AI — API Service (React Native)
import axios from 'axios';
import { Platform } from 'react-native';
import { supabase } from './auth';

const BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

// In Web mode, Safari/Chrome block direct requests to Render due to CORS.
// We use our new local proxy server (local-proxy.js) to effortlessly bypass it.
const API_URL = Platform.OS === 'web' && BASE_URL.includes('onrender.com')
    ? 'http://localhost:3001'
    : BASE_URL;

const api = axios.create({
    baseURL: API_URL,
    headers: { 'Content-Type': 'application/json' },
    timeout: 30000,
});

// Attach Supabase access token
api.interceptors.request.use(async (config) => {
    try {
        const authService = require('./auth').default;
        if (authService) {
            const token = await authService.getToken();
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
        }
    } catch (e) {
        if (e.name !== 'AbortError') {
            console.warn('Token attach error:', e);
        }
    }
    return config;
});

// Retry logic
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const { config, response } = error;
        if (
            config &&
            (!config.__retryCount || config.__retryCount < MAX_RETRIES) &&
            (!response || response.status >= 500)
        ) {
            config.__retryCount = (config.__retryCount || 0) + 1;
            await new Promise((r) => setTimeout(r, RETRY_DELAY * config.__retryCount));
            return api(config);
        }
        return Promise.reject(error);
    }
);

// ==================== MOTHER API ====================
export const motherAPI = {
    async register(data) {
        const res = await api.post('/mothers/register', data);
        return res.data;
    },
    async getAll() {
        const res = await api.get('/mothers');
        return res.data;
    },
    async getById(id) {
        const res = await api.get(`/mothers/${id}`);
        return res.data;
    },
};

// ==================== AUTH API ====================
export const authAPI = {
    async createRegisterRequest(payload) {
        const res = await api.post('/auth/register-request', payload);
        return res.data;
    },
    async uploadCertification(email, file) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('email', email);
        const res = await api.post('/auth/upload-certification', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return res.data;
    },
    async listRegisterRequests() {
        const res = await api.get('/auth/register-requests');
        return res.data;
    },
    async decideRegisterRequest(id, approved, note) {
        const res = await api.post(`/auth/register-requests/${id}/decide`, { approved, note });
        return res.data;
    },
    async listPendingUsers() {
        const res = await api.get('/auth/pending-users');
        return res.data;
    },
    async assignRoleToPendingUser(userId, role) {
        const res = await api.post(`/auth/pending-users/${userId}/assign-role`, { role });
        return res.data;
    },
    async listRoleRequests() {
        const res = await api.get('/auth/role-requests');
        return res.data;
    },
    async approveRoleRequest(requestId, role) {
        const res = await api.post(`/auth/role-requests/${requestId}/approve`, { role });
        return res.data;
    },
    async rejectRoleRequest(requestId, reason) {
        const res = await api.post(`/auth/role-requests/${requestId}/reject`, { reason });
        return res.data;
    },
};

// ==================== CERTIFICATE API ====================
export const certificateAPI = {
    async verifyDoctorCertificate(formData) {
        const res = await api.post('/api/v1/certificates/verify', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return res;
    },
    async parseCertificate(formData) {
        const res = await api.post('/api/v1/certificates/parse', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return res;
    },
    async parseIDDocument(formData) {
        const res = await api.post('/api/v1/certificates/id-document/parse', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return res;
    },
    async validateAshaID(formData) {
        const res = await api.post('/api/v1/certificates/id-document/validate-asha', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return res;
    },
};

// ==================== RISK API ====================
export const riskAPI = {
    async assess(data) {
        const res = await api.post('/risk/assess', data);
        return res.data;
    },
    async getAll() {
        const res = await api.get('/risk/assessments');
        return res.data;
    },
    async getByMotherId(motherId) {
        const res = await api.get(`/risk/assessments/${motherId}`);
        return res.data;
    },
};

// ==================== ANALYTICS API ====================
export const analyticsAPI = {
    async getDashboard() {
        const res = await api.get('/analytics/dashboard');
        return res.data;
    },
    async getRiskDistribution() {
        const res = await api.get('/analytics/risk-distribution');
        return res.data;
    },
};

// ==================== APPOINTMENT API ====================
export const appointmentAPI = {
    async create(data) {
        const res = await api.post('/appointments', data);
        return res.data;
    },
};

// ==================== VISIT API ====================
export const visitAPI = {
    async record(data) {
        const res = await api.post('/visits', data);
        return res.data;
    },
};

// ==================== AI AGENT ====================
export async function queryAgent({ motherId, query, useContext = true, language = 'en' }) {
    const res = await api.post('/agent/query', {
        mother_id: motherId,
        query,
        use_context: useContext,
        language,
    });
    return res.data;
}

// ==================== ADMIN API ====================
export const adminAPI = {
    async getStats() {
        const res = await api.get('/api/admin/stats');
        return res.data;
    },
    async getMetrics() {
        const res = await api.get('/api/admin/metrics');
        return res.data;
    },
    async getFullData() {
        const res = await api.get('/api/admin/full');
        return res.data;
    },
    async getSantanRakshaStats() {
        const res = await api.get('/api/admin/santanraksha-stats');
        return res.data;
    },
    async getDoctors() {
        const res = await api.get('/admin/doctors');
        return res.data;
    },
    async getMotherStats() {
        const res = await api.get('/admin/mothers/stats');
        return res.data;
    },
    async getChildrenStats() {
        const res = await api.get('/admin/children/stats');
        return res.data;
    },
    async getAllMothers() {
        const res = await api.get('/admin/mothers');
        return res.data;
    },
    async getAllChildren() {
        const res = await api.get('/admin/children');
        return res.data;
    },
    async getUserStats() {
        const res = await api.get('/admin/users/stats');
        return res.data;
    },
};

// ==================== POSTNATAL API ====================
export const postnatalAPI = {
    async getMothersByStatus(status) {
        const res = await api.get(`/postnatal/mothers?status=${status}`);
        return res.data;
    },
    async getAssessments(motherId) {
        const res = await api.get(`/postnatal/assessments/${motherId}`);
        return res.data;
    },
    async createAssessment(data) {
        const res = await api.post('/postnatal/assessments', data);
        return res.data;
    },
};

// ==================== SANTANRAKSHA API ====================
export const santanrakshaAPI = {
    async getChildren(motherId) {
        const res = await api.get(`/santanraksha/children?mother_id=${motherId}`);
        return res.data;
    },
    async registerChild(data) {
        const res = await api.post('/santanraksha/children/register', data);
        return res.data;
    },
    async getGrowthRecords(childId) {
        const res = await api.get(`/santanraksha/growth/${childId}`);
        return res.data;
    },
    async recordGrowth(data) {
        const res = await api.post('/santanraksha/growth/record', data);
        return res.data;
    },
    async getVaccinationSchedule(childId) {
        const res = await api.get(`/santanraksha/vaccination/schedule/${childId}`);
        return res.data;
    },
    async markVaccinationDone(data) {
        const res = await api.post('/santanraksha/vaccination/mark-done', data);
        return res.data;
    },
    async getMilestones(childId) {
        const res = await api.get(`/santanraksha/milestones/${childId}`);
        return res.data;
    },
    async recordMilestone(data) {
        const res = await api.post('/santanraksha/milestones/record', data);
        return res.data;
    },
    async getPediatricAssessment(childId) {
        const res = await api.get(`/santanraksha/assessment/${childId}`);
        return res.data;
    },
};

// ==================== DELIVERY API ====================
export const deliveryAPI = {
    async recordDelivery(data) {
        const res = await api.post('/delivery/record', data);
        return res.data;
    },
    async getDeliveryStatus(motherId) {
        const res = await api.get(`/delivery/status/${motherId}`);
        return res.data;
    },
};

// ==================== CONSULTATION API ====================
export const consultationAPI = {
    async create(data) {
        const res = await api.post('/enhanced/consultation', data);
        return res.data;
    },
    async getHistory(motherId) {
        const res = await api.get(`/enhanced/consultations/${motherId}`);
        return res.data;
    },
};

export { api };
export default api;
