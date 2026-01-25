import React, { useState } from 'react';
import { X, Baby, Calendar, Hospital, Save, Heart } from 'lucide-react';

export const DeliveryCompletionModal = ({ mother, onClose, onComplete }) => {
    const [formData, setFormData] = useState({
        delivery_date: new Date().toISOString().split('T')[0],
        delivery_type: 'normal',
        delivery_hospital: '',
        gestational_age_weeks: 40,
        child_name: '',
        child_gender: 'male',
        birth_weight_kg: '',
        birth_length_cm: '',
        apgar_score_1min: '',
        apgar_score_5min: ''
    });
    const [loading, setLoading] = useState(false);
    const [congratulations, setCongratulations] = useState('');
    const [showCongrats, setShowCongrats] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async () => {
        setLoading(true);
        setError('');

        try {
            // Build request payload
            const payload = {
                mother_id: mother.id,
                delivery_date: new Date(formData.delivery_date).toISOString(),
                delivery_type: formData.delivery_type,
                delivery_hospital: formData.delivery_hospital || null,
                gestational_age_weeks: parseInt(formData.gestational_age_weeks) || null,
                delivery_complications: []
            };

            // Add child data if name is provided
            if (formData.child_name && formData.child_name.trim()) {
                payload.child = {
                    name: formData.child_name.trim(),
                    gender: formData.child_gender,
                    birth_weight_kg: parseFloat(formData.birth_weight_kg) || null,
                    birth_length_cm: parseFloat(formData.birth_length_cm) || null,
                    apgar_score_1min: parseInt(formData.apgar_score_1min) || null,
                    apgar_score_5min: parseInt(formData.apgar_score_5min) || null
                };
            }

            const response = await fetch('/api/delivery/complete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (response.ok && result.success) {
                setCongratulations(result.message);
                setShowCongrats(true);

                // Close modal after 6 seconds and redirect/refresh
                setTimeout(() => {
                    onComplete && onComplete();
                    // Optionally redirect to SantanRaksha dashboard
                    if (window.location.pathname.includes('asha') || window.location.pathname.includes('matru')) {
                        window.location.href = '/postnatal';
                    } else {
                        window.location.reload();
                    }
                }, 6000);
            } else {
                setError(result.detail || result.message || 'Failed to complete delivery');
                setLoading(false);
            }
        } catch (err) {
            console.error('Delivery completion error:', err);
            setError(`Failed to complete delivery: ${err.message}`);
            setLoading(false);
        }
    };

    // Congratulations screen
    if (showCongrats) {
        return (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                <div className="bg-white rounded-2xl p-8 max-w-lg mx-auto text-center shadow-2xl animate-fadeIn">
                    <div className="text-7xl mb-6 animate-bounce">🎉</div>
                    <h2 className="text-3xl font-bold mb-4 text-green-700">
                        <Heart className="inline w-8 h-8 mr-2 text-red-500" />
                        Congratulations!
                    </h2>
                    <div className="text-gray-700 whitespace-pre-line mb-8 text-left bg-green-50 p-6 rounded-lg leading-relaxed">
                        {congratulations}
                    </div>
                    <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                        <p>Redirecting to SantanRaksha dashboard...</p>
                    </div>
                </div>
            </div>
        );
    }

    // Main form
    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
            <div className="bg-white rounded-xl p-6 max-w-2xl w-full mx-auto my-8 shadow-xl">
                {/* Header */}
                <div className="flex justify-between items-center mb-6 border-b pb-4">
                    <div>
                        <h2 className="text-2xl font-bold text-gray-800">
                            Complete Delivery 🎉
                        </h2>
                        <p className="text-sm text-gray-600 mt-1">
                            Mother: <span className="font-semibold">{mother.name}</span>
                        </p>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600 transition"
                        disabled={loading}
                    >
                        <X className="w-6 h-6" />
                    </button>
                </div>

                {error && (
                    <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                        ⚠️ {error}
                    </div>
                )}

                <div className="space-y-5 max-h-[60vh] overflow-y-auto pr-2">
                    {/* Delivery Information Section */}
                    <div className="bg-blue-50 p-4 rounded-lg">
                        <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                            <Hospital className="w-5 h-5 text-blue-600" />
                            Delivery Information
                        </h3>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium mb-1 text-gray-700">
                                    <Calendar className="inline w-4 h-4 mr-1" />
                                    Delivery Date *
                                </label>
                                <input
                                    type="date"
                                    value={formData.delivery_date}
                                    onChange={e => setFormData({ ...formData, delivery_date: e.target.value })}
                                    max={new Date().toISOString().split('T')[0]}
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1 text-gray-700">
                                    Delivery Type *
                                </label>
                                <select
                                    value={formData.delivery_type}
                                    onChange={e => setFormData({ ...formData, delivery_type: e.target.value })}
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    required
                                >
                                    <option value="normal">Normal Delivery</option>
                                    <option value="cesarean">Cesarean Section (C-Section)</option>
                                    <option value="assisted">Assisted Delivery (Forceps/Vacuum)</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1 text-gray-700">
                                    Hospital/Facility
                                </label>
                                <input
                                    type="text"
                                    value={formData.delivery_hospital}
                                    onChange={e => setFormData({ ...formData, delivery_hospital: e.target.value })}
                                    placeholder="Hospital name (optional)"
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1 text-gray-700">
                                    Gestational Age (weeks)
                                </label>
                                <input
                                    type="number"
                                    value={formData.gestational_age_weeks}
                                    onChange={e => setFormData({ ...formData, gestational_age_weeks: e.target.value })}
                                    min="20"
                                    max="45"
                                    placeholder="40"
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Child Information Section */}
                    <div className="bg-pink-50 p-4 rounded-lg">
                        <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                            <Baby className="w-5 h-5 text-pink-600" />
                            Child Information (Optional - can add later)
                        </h3>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="md:col-span-2">
                                <label className="block text-sm font-medium mb-1 text-gray-700">
                                    Child Name
                                </label>
                                <input
                                    type="text"
                                    value={formData.child_name}
                                    onChange={e => setFormData({ ...formData, child_name: e.target.value })}
                                    placeholder="Baby's name"
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1 text-gray-700">
                                    Gender
                                </label>
                                <select
                                    value={formData.child_gender}
                                    onChange={e => setFormData({ ...formData, child_gender: e.target.value })}
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                                >
                                    <option value="male">Boy</option>
                                    <option value="female">Girl</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1 text-gray-700">
                                    Birth Weight (kg)
                                </label>
                                <input
                                    type="number"
                                    step="0.01"
                                    value={formData.birth_weight_kg}
                                    onChange={e => setFormData({ ...formData, birth_weight_kg: e.target.value })}
                                    placeholder="3.2"
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1 text-gray-700">
                                    Birth Length (cm)
                                </label>
                                <input
                                    type="number"
                                    step="0.1"
                                    value={formData.birth_length_cm}
                                    onChange={e => setFormData({ ...formData, birth_length_cm: e.target.value })}
                                    placeholder="50"
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1 text-gray-700">
                                    APGAR Score (1 min)
                                </label>
                                <input
                                    type="number"
                                    min="0"
                                    max="10"
                                    value={formData.apgar_score_1min}
                                    onChange={e => setFormData({ ...formData, apgar_score_1min: e.target.value })}
                                    placeholder="0-10"
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1 text-gray-700">
                                    APGAR Score (5 min)
                                </label>
                                <input
                                    type="number"
                                    min="0"
                                    max="10"
                                    value={formData.apgar_score_5min}
                                    onChange={e => setFormData({ ...formData, apgar_score_5min: e.target.value })}
                                    placeholder="0-10"
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3 mt-6 pt-4 border-t">
                    <button
                        onClick={onClose}
                        className="flex-1 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition font-medium text-gray-700"
                        disabled={loading}
                    >
                        <X className="inline w-4 h-4 mr-2" />
                        Cancel
                    </button>
                    <button
                        onClick={handleSubmit}
                        className="flex-1 px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium shadow-lg disabled:bg-gray-400 disabled:cursor-not-allowed"
                        disabled={loading}
                    >
                        {loading ? (
                            <>
                                <div className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                                Processing...
                            </>
                        ) : (
                            <>
                                <Save className="inline w-4 h-4 mr-2" />
                                Complete Delivery
                            </>
                        )}
                    </button>
                </div>

                <p className="text-xs text-gray-500 mt-3 text-center">
                    * Required fields | Child information can be added later if needed
                </p>
            </div>
        </div>
    );
};
