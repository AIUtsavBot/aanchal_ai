import React, { useState, useEffect } from 'react';
import {
    Baby,
    User,
    Calendar,
    Clock,
    Scale,
    Heart,
    Check,
    AlertCircle,
    Loader,
    RefreshCw,
    ChevronDown,
    ArrowRight
} from 'lucide-react';
import { supabase } from '../services/auth.js';
import './DeliveryForm.css';

// Helper to get Supabase access token from localStorage
const getAccessToken = () => {
    const keys = Object.keys(localStorage).filter(k => k.startsWith('sb-') && k.endsWith('-auth-token'));
    if (keys.length > 0) {
        const stored = localStorage.getItem(keys[0]);
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                return parsed?.access_token || null;
            } catch {
                return null;
            }
        }
    }
    return null;
};

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function DeliveryForm({ doctorId, onSuccess }) {
    // List of pregnant mothers (not yet delivered)
    const [mothers, setMothers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // Selected mother
    const [selectedMother, setSelectedMother] = useState(null);

    // Form state
    const [formData, setFormData] = useState({
        deliveryDate: new Date().toISOString().split('T')[0],
        deliveryTime: new Date().toTimeString().slice(0, 5),
        deliveryType: 'normal',
        deliveryHospital: '',
        gestationalAgeWeeks: 40,
        // Baby details
        babyName: '',
        babyGender: 'male',
        birthWeightKg: '',
        birthLengthCm: '',
        birthHeadCircumferenceCm: '',
        apgarScore1min: '',
        apgarScore5min: '',
        birthComplications: []
    });

    const [submitting, setSubmitting] = useState(false);
    const [success, setSuccess] = useState(false);
    const [submitError, setSubmitError] = useState('');

    // Load pregnant mothers
    useEffect(() => {
        loadPregnantMothers();
    }, [doctorId]);

    const loadPregnantMothers = async () => {
        if (!doctorId) {
            setError('Doctor ID not available');
            setLoading(false);
            return;
        }

        setLoading(true);
        setError('');
        try {
            // Use Supabase directly to fetch mothers assigned to this doctor
            const { data, error: supabaseError } = await supabase
                .from('mothers')
                .select('*')
                .eq('doctor_id', doctorId);

            if (supabaseError) {
                throw new Error(supabaseError.message);
            }

            // Filter for pregnant mothers (not delivered yet / still in matruraksha)
            const pregnantMothers = (data || []).filter(m =>
                !m.delivery_status ||
                m.delivery_status === 'pregnant' ||
                m.active_system !== 'santanraksha'
            );
            setMothers(pregnantMothers);
        } catch (err) {
            console.error('Error loading mothers:', err);
            setError('Failed to load patient list');
        } finally {
            setLoading(false);
        }
    };

    // Load draft from storage on mount
    useEffect(() => {
        const draft = localStorage.getItem('delivery_form_draft');
        if (draft) {
            try {
                const parsed = JSON.parse(draft);
                // Only restore if it matches the current structure roughly
                if (parsed.babyName !== undefined) {
                    setFormData(prev => ({ ...prev, ...parsed }));
                    console.log("📝 Restored draft from local storage");
                }
            } catch (e) {
                console.error("Error loading draft", e);
            }
        }
    }, []);

    // Save draft on change
    useEffect(() => {
        // Debounce slightly to avoid excessive writes
        const timer = setTimeout(() => {
            if (formData.babyName || formData.birthWeightKg) { // Only save if some data entered
                localStorage.setItem('delivery_form_draft', JSON.stringify(formData));
            }
        }, 1000);
        return () => clearTimeout(timer);
    }, [formData]);

    const handleInputChange = (e) => {
        const { name, value, type, checked } = e.target;

        if (type === 'checkbox') {
            // Handle complications checkboxes
            setFormData(prev => ({
                ...prev,
                birthComplications: checked
                    ? [...prev.birthComplications, value]
                    : prev.birthComplications.filter(c => c !== value)
            }));
        } else {
            setFormData(prev => ({
                ...prev,
                [name]: value
            }));
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!selectedMother) {
            setSubmitError('Please select a mother first');
            return;
        }

        if (!formData.babyName.trim()) {
            setSubmitError('Please enter the baby\'s name');
            return;
        }

        if (!formData.birthWeightKg) {
            setSubmitError('Please enter the birth weight');
            return;
        }

        setSubmitting(true);
        setSubmitError('');
        setSuccess(false);

        try {
            // Combine date and time
            const deliveryDateTime = new Date(`${formData.deliveryDate}T${formData.deliveryTime}:00`);

            const requestBody = {
                mother_id: selectedMother.id,
                delivery_date: deliveryDateTime.toISOString(),
                delivery_type: formData.deliveryType,
                delivery_hospital: formData.deliveryHospital || null,
                delivery_complications: formData.birthComplications,
                gestational_age_weeks: parseInt(formData.gestationalAgeWeeks) || 40,
                child: {
                    name: formData.babyName,
                    gender: formData.babyGender,
                    birth_weight_kg: parseFloat(formData.birthWeightKg) || null,
                    birth_length_cm: parseFloat(formData.birthLengthCm) || null,
                    birth_head_circumference_cm: parseFloat(formData.birthHeadCircumferenceCm) || null,
                    apgar_score_1min: parseInt(formData.apgarScore1min) || null,
                    apgar_score_5min: parseInt(formData.apgarScore5min) || null,
                    birth_complications: formData.birthComplications
                }
            };

            const response = await fetch(`${API_URL}/api/delivery/complete`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${getAccessToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });

            const data = await response.json();

            if (response.ok && data.success) {
                setSuccess(true);
                // Reset form
                setFormData({
                    deliveryDate: new Date().toISOString().split('T')[0],
                    deliveryTime: new Date().toTimeString().slice(0, 5),
                    deliveryType: 'normal',
                    deliveryHospital: '',
                    gestationalAgeWeeks: 40,
                    babyName: '',
                    babyGender: 'male',
                    birthWeightKg: '',
                    birthLengthCm: '',
                    birthHeadCircumferenceCm: '',
                    apgarScore1min: '',
                    apgarScore5min: '',
                    birthComplications: []
                });

                // Clear local storage draft
                localStorage.removeItem('delivery_form_draft');

                // Optimistically remove mother from list (much faster than reload)
                setMothers(prev => prev.filter(m => m.id !== selectedMother.id));

                // Reload in background just in case
                // loadPregnantMothers();
                // Callback
                if (onSuccess) onSuccess(data);
            } else {
                throw new Error(data.detail || data.message || 'Failed to complete delivery');
            }
        } catch (err) {
            console.error('Delivery completion error:', err);
            setSubmitError(err.message || 'Failed to complete delivery. Please try again.');
        } finally {
            setSubmitting(false);
        }
    };

    const deliveryTypes = [
        { value: 'normal', label: 'Normal Vaginal Delivery' },
        { value: 'cesarean', label: 'Cesarean Section (C-Section)' },
        { value: 'assisted', label: 'Assisted Delivery' },
        { value: 'forceps', label: 'Forceps Delivery' },
        { value: 'vacuum', label: 'Vacuum Extraction' }
    ];

    const complications = [
        'Preterm birth',
        'Low birth weight',
        'Birth asphyxia',
        'Jaundice',
        'Respiratory distress',
        'Cord around neck',
        'Meconium aspiration',
        'Postpartum hemorrhage'
    ];

    return (
        <div className="delivery-form-container">
            <div className="delivery-form-header">
                <div className="header-icon">
                    <Baby className="w-8 h-8" />
                </div>
                <div>
                    <h2 className="header-title">Complete Delivery</h2>
                    <p className="header-subtitle">
                        Record delivery details to transition from MatruRaksha to SantanRaksha
                    </p>
                </div>
            </div>

            {/* Success Message */}
            {success && (
                <div className="success-message">
                    <Check className="w-5 h-5" />
                    <div>
                        <strong>Delivery completed successfully!</strong>
                        <p>Mother has been transitioned to SantanRaksha for postnatal care.</p>
                    </div>
                </div>
            )}

            {/* Error Message */}
            {submitError && (
                <div className="error-message">
                    <AlertCircle className="w-5 h-5" />
                    <span>{submitError}</span>
                </div>
            )}

            {/* Step 1: Select Mother */}
            <div className="form-section">
                <h3 className="section-title">
                    <span className="step-number">1</span>
                    Select Mother
                </h3>

                {loading ? (
                    <div className="loading-state">
                        <Loader className="w-6 h-6 animate-spin" />
                        <span>Loading patients...</span>
                    </div>
                ) : error ? (
                    <div className="error-state">
                        <AlertCircle className="w-5 h-5" />
                        <span>{error}</span>
                        <button onClick={loadPregnantMothers} className="retry-btn">
                            <RefreshCw className="w-4 h-4" /> Retry
                        </button>
                    </div>
                ) : mothers.length === 0 ? (
                    <div className="empty-state">
                        <User className="w-10 h-10" />
                        <p>No pregnant mothers found</p>
                        <span>All mothers have already delivered or none are assigned to you.</span>
                    </div>
                ) : (
                    <div className="mothers-grid">
                        {mothers.map(mother => (
                            <div
                                key={mother.id}
                                onClick={() => {
                                    setSelectedMother(mother);
                                    // Pre-fill baby's last name
                                    const lastName = mother.name?.split(' ').pop() || '';
                                    setFormData(prev => ({
                                        ...prev,
                                        babyName: `Baby ${lastName}`
                                    }));
                                }}
                                className={`mother-card ${selectedMother?.id === mother.id ? 'selected' : ''}`}
                            >
                                <div className="mother-avatar">
                                    {mother.name?.charAt(0) || 'M'}
                                </div>
                                <div className="mother-info">
                                    <div className="mother-name">{mother.name}</div>
                                    <div className="mother-details">
                                        Age: {mother.age} · {mother.location}
                                    </div>
                                    {mother.due_date && (
                                        <div className="due-date">
                                            Due: {new Date(mother.due_date).toLocaleDateString()}
                                        </div>
                                    )}
                                </div>
                                {selectedMother?.id === mother.id && (
                                    <Check className="w-5 h-5 text-green-600" />
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Step 2: Delivery Details */}
            {selectedMother && (
                <form onSubmit={handleSubmit} className="delivery-form">
                    <div className="form-section">
                        <h3 className="section-title">
                            <span className="step-number">2</span>
                            Delivery Details
                        </h3>

                        <div className="form-grid">
                            <div className="form-group">
                                <label>
                                    <Calendar className="w-4 h-4" />
                                    Delivery Date
                                </label>
                                <input
                                    type="date"
                                    name="deliveryDate"
                                    value={formData.deliveryDate}
                                    onChange={handleInputChange}
                                    required
                                />
                            </div>

                            <div className="form-group">
                                <label>
                                    <Clock className="w-4 h-4" />
                                    Delivery Time
                                </label>
                                <input
                                    type="time"
                                    name="deliveryTime"
                                    value={formData.deliveryTime}
                                    onChange={handleInputChange}
                                    required
                                />
                            </div>

                            <div className="form-group">
                                <label>
                                    <Heart className="w-4 h-4" />
                                    Delivery Type
                                </label>
                                <select
                                    name="deliveryType"
                                    value={formData.deliveryType}
                                    onChange={handleInputChange}
                                    required
                                >
                                    {deliveryTypes.map(type => (
                                        <option key={type.value} value={type.value}>
                                            {type.label}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className="form-group">
                                <label>Hospital/Facility</label>
                                <input
                                    type="text"
                                    name="deliveryHospital"
                                    value={formData.deliveryHospital}
                                    onChange={handleInputChange}
                                    placeholder="Enter hospital name"
                                />
                            </div>

                            <div className="form-group">
                                <label>Gestational Age (weeks)</label>
                                <input
                                    type="number"
                                    name="gestationalAgeWeeks"
                                    value={formData.gestationalAgeWeeks}
                                    onChange={handleInputChange}
                                    min="20"
                                    max="45"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Step 3: Baby Details */}
                    <div className="form-section">
                        <h3 className="section-title">
                            <span className="step-number">3</span>
                            Baby Details
                        </h3>

                        <div className="form-grid">
                            <div className="form-group full-width">
                                <label>
                                    <Baby className="w-4 h-4" />
                                    Baby's Name *
                                </label>
                                <input
                                    type="text"
                                    name="babyName"
                                    value={formData.babyName}
                                    onChange={handleInputChange}
                                    placeholder="Enter baby's name"
                                    required
                                />
                            </div>

                            <div className="form-group">
                                <label>Gender *</label>
                                <div className="gender-options">
                                    <label className={`gender-option ${formData.babyGender === 'male' ? 'selected' : ''}`}>
                                        <input
                                            type="radio"
                                            name="babyGender"
                                            value="male"
                                            checked={formData.babyGender === 'male'}
                                            onChange={handleInputChange}
                                        />
                                        <span>👶 Male</span>
                                    </label>
                                    <label className={`gender-option ${formData.babyGender === 'female' ? 'selected' : ''}`}>
                                        <input
                                            type="radio"
                                            name="babyGender"
                                            value="female"
                                            checked={formData.babyGender === 'female'}
                                            onChange={handleInputChange}
                                        />
                                        <span>👶 Female</span>
                                    </label>
                                </div>
                            </div>

                            <div className="form-group">
                                <label>
                                    <Scale className="w-4 h-4" />
                                    Birth Weight (kg) *
                                </label>
                                <input
                                    type="number"
                                    name="birthWeightKg"
                                    value={formData.birthWeightKg}
                                    onChange={handleInputChange}
                                    placeholder="e.g., 3.2"
                                    step="0.01"
                                    min="0.5"
                                    max="6"
                                    required
                                />
                            </div>

                            <div className="form-group">
                                <label>Birth Length (cm)</label>
                                <input
                                    type="number"
                                    name="birthLengthCm"
                                    value={formData.birthLengthCm}
                                    onChange={handleInputChange}
                                    placeholder="e.g., 50"
                                    step="0.1"
                                    min="30"
                                    max="70"
                                />
                            </div>

                            <div className="form-group">
                                <label>Head Circumference (cm)</label>
                                <input
                                    type="number"
                                    name="birthHeadCircumferenceCm"
                                    value={formData.birthHeadCircumferenceCm}
                                    onChange={handleInputChange}
                                    placeholder="e.g., 35"
                                    step="0.1"
                                    min="25"
                                    max="45"
                                />
                            </div>

                            <div className="form-group">
                                <label>APGAR Score (1 min)</label>
                                <input
                                    type="number"
                                    name="apgarScore1min"
                                    value={formData.apgarScore1min}
                                    onChange={handleInputChange}
                                    placeholder="0-10"
                                    min="0"
                                    max="10"
                                />
                            </div>

                            <div className="form-group">
                                <label>APGAR Score (5 min)</label>
                                <input
                                    type="number"
                                    name="apgarScore5min"
                                    value={formData.apgarScore5min}
                                    onChange={handleInputChange}
                                    placeholder="0-10"
                                    min="0"
                                    max="10"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Complications */}
                    <div className="form-section">
                        <h3 className="section-title">
                            <span className="step-number">4</span>
                            Complications (if any)
                        </h3>

                        <div className="complications-grid">
                            {complications.map(comp => (
                                <label key={comp} className="complication-option">
                                    <input
                                        type="checkbox"
                                        value={comp}
                                        checked={formData.birthComplications.includes(comp)}
                                        onChange={handleInputChange}
                                    />
                                    <span>{comp}</span>
                                </label>
                            ))}
                        </div>
                    </div>

                    {/* Submit Button */}
                    <div className="form-actions">
                        <button
                            type="submit"
                            disabled={submitting}
                            className="submit-btn"
                        >
                            {submitting ? (
                                <>
                                    <Loader className="w-5 h-5 animate-spin" />
                                    Processing...
                                </>
                            ) : (
                                <>
                                    Complete Delivery
                                    <ArrowRight className="w-5 h-5" />
                                </>
                            )}
                        </button>
                        <p className="submit-note">
                            This will transition {selectedMother.name} from MatruRaksha to SantanRaksha
                        </p>
                    </div>
                </form>
            )}
        </div>
    );
}
