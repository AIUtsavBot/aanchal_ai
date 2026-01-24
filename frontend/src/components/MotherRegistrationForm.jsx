import React, { useState } from 'react'
import { UserPlus, Phone, MapPin, Calendar, Heart, Activity, Loader, CheckCircle, AlertCircle } from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function MotherRegistrationForm({ onSuccess, assignerId, assignerRole }) {
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [success, setSuccess] = useState('')

    const [formData, setFormData] = useState({
        name: '',
        phone: '',
        age: '',
        gravida: '',
        parity: '',
        bmi: '',
        location: '',
        preferred_language: 'en',
        telegram_chat_id: '',
        due_date: ''
    })

    const handleChange = (e) => {
        const { name, value } = e.target
        setFormData(prev => ({ ...prev, [name]: value }))
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError('')
        setSuccess('')

        // Validation
        if (!formData.name || !formData.phone || !formData.age || !formData.gravida || !formData.parity || !formData.location) {
            setError('Please fill all required fields')
            setLoading(false)
            return
        }

        try {
            const payload = {
                name: formData.name.trim(),
                phone: formData.phone.trim(),
                age: parseInt(formData.age, 10),
                gravida: parseInt(formData.gravida, 10),
                parity: parseInt(formData.parity, 10),
                bmi: formData.bmi ? parseFloat(formData.bmi) : 0,
                location: formData.location.trim(),
                preferred_language: formData.preferred_language || 'en',
                telegram_chat_id: formData.telegram_chat_id || null,
                due_date: formData.due_date || null
            }

            const response = await fetch(`${API_URL}/mothers/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.detail || 'Registration failed')
            }

            const result = await response.json()
            setSuccess(`✅ Successfully registered: ${formData.name}`)

            // Reset form
            setFormData({
                name: '',
                phone: '',
                age: '',
                gravida: '',
                parity: '',
                bmi: '',
                location: '',
                preferred_language: 'en',
                telegram_chat_id: '',
                due_date: ''
            })

            // Call parent callback if provided
            if (onSuccess) {
                onSuccess(result.data)
            }
        } catch (err) {
            console.error('Registration error:', err)
            setError(err.message || 'Failed to register mother')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="bg-white rounded-xl shadow-lg p-6 max-w-2xl mx-auto">
            <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                <UserPlus className="w-6 h-6 text-pink-600" />
                Register New Mother
            </h2>

            {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-800">
                    <AlertCircle className="w-5 h-5" />
                    {error}
                </div>
            )}

            {success && (
                <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2 text-green-800">
                    <CheckCircle className="w-5 h-5" />
                    {success}
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
                {/* Personal Information */}
                <div className="bg-gray-50 p-4 rounded-lg space-y-4">
                    <h3 className="text-sm font-bold text-gray-600 uppercase flex items-center gap-2">
                        <Heart className="w-4 h-4 text-pink-500" />
                        Personal Information
                    </h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-1">
                                Full Name <span className="text-red-500">*</span>
                            </label>
                            <input
                                type="text"
                                name="name"
                                value={formData.name}
                                onChange={handleChange}
                                placeholder="Enter full name"
                                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-1">
                                Phone Number <span className="text-red-500">*</span>
                            </label>
                            <div className="relative">
                                <Phone className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                                <input
                                    type="tel"
                                    name="phone"
                                    value={formData.phone}
                                    onChange={handleChange}
                                    placeholder="10-digit phone number"
                                    className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                                    required
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-1">
                                Age <span className="text-red-500">*</span>
                            </label>
                            <input
                                type="number"
                                name="age"
                                value={formData.age}
                                onChange={handleChange}
                                placeholder="Age in years"
                                min="15"
                                max="60"
                                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-1">
                                Location <span className="text-red-500">*</span>
                            </label>
                            <div className="relative">
                                <MapPin className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                                <input
                                    type="text"
                                    name="location"
                                    value={formData.location}
                                    onChange={handleChange}
                                    placeholder="Village/City name"
                                    className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                                    required
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Medical Information */}
                <div className="bg-blue-50 p-4 rounded-lg space-y-4">
                    <h3 className="text-sm font-bold text-gray-600 uppercase flex items-center gap-2">
                        <Activity className="w-4 h-4 text-blue-500" />
                        Medical Information
                    </h3>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-1">
                                Gravida <span className="text-red-500">*</span>
                                <span className="font-normal text-gray-500 ml-1">(Pregnancies)</span>
                            </label>
                            <input
                                type="number"
                                name="gravida"
                                value={formData.gravida}
                                onChange={handleChange}
                                placeholder="0"
                                min="0"
                                max="20"
                                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-1">
                                Parity <span className="text-red-500">*</span>
                                <span className="font-normal text-gray-500 ml-1">(Births)</span>
                            </label>
                            <input
                                type="number"
                                name="parity"
                                value={formData.parity}
                                onChange={handleChange}
                                placeholder="0"
                                min="0"
                                max="20"
                                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-1">
                                BMI
                                <span className="font-normal text-gray-500 ml-1">(Optional)</span>
                            </label>
                            <input
                                type="number"
                                name="bmi"
                                value={formData.bmi}
                                onChange={handleChange}
                                placeholder="e.g., 22.5"
                                step="0.1"
                                min="10"
                                max="60"
                                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-1">
                                Expected Due Date
                                <span className="font-normal text-gray-500 ml-1">(Optional)</span>
                            </label>
                            <div className="relative">
                                <Calendar className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                                <input
                                    type="date"
                                    name="due_date"
                                    value={formData.due_date}
                                    onChange={handleChange}
                                    className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-1">
                                Preferred Language
                            </label>
                            <select
                                name="preferred_language"
                                value={formData.preferred_language}
                                onChange={handleChange}
                                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            >
                                <option value="en">English</option>
                                <option value="hi">Hindi</option>
                                <option value="mr">Marathi</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* Telegram Integration */}
                <div className="bg-purple-50 p-4 rounded-lg space-y-4">
                    <h3 className="text-sm font-bold text-gray-600 uppercase flex items-center gap-2">
                        📱 Telegram Integration
                    </h3>

                    <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-1">
                            Telegram Chat ID
                            <span className="font-normal text-gray-500 ml-1">(Get from /start in Telegram bot)</span>
                        </label>
                        <input
                            type="text"
                            name="telegram_chat_id"
                            value={formData.telegram_chat_id}
                            onChange={handleChange}
                            placeholder="e.g., 123456789"
                            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        />
                        <p className="text-xs text-gray-500 mt-1">
                            💡 Ask the mother to send /start to the MatruRaksha bot on Telegram and get their Chat ID
                        </p>
                    </div>
                </div>

                {/* Submit Button */}
                <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-4 bg-gradient-to-r from-pink-600 to-rose-600 text-white rounded-lg font-bold text-lg hover:from-pink-700 hover:to-rose-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg transition-all transform hover:scale-[1.02]"
                >
                    {loading ? (
                        <>
                            <Loader className="w-5 h-5 animate-spin" />
                            Registering...
                        </>
                    ) : (
                        <>
                            <UserPlus className="w-5 h-5" />
                            Register Mother
                        </>
                    )}
                </button>
            </form>
        </div>
    )
}
