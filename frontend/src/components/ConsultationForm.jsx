import React, { useState, useEffect } from 'react'
import { supabase } from '../services/auth.js'
import {
    Save, Loader, AlertCircle, CheckCircle, Calendar,
    Pill, Apple, Heart, Plus, Trash2, Clock, Activity,
    Thermometer, Droplet, Scale
} from 'lucide-react'
import VoiceInput from './VoiceInput'

export default function ConsultationForm({ motherId, doctorId, doctorName, onSave }) {
    const [loading, setLoading] = useState(false)
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState('')
    const [success, setSuccess] = useState('')

    // Form state - Health Status & Vitals
    const [healthStatus, setHealthStatus] = useState('')
    const [systolicBP, setSystolicBP] = useState('')
    const [diastolicBP, setDiastolicBP] = useState('')
    const [heartRate, setHeartRate] = useState('')
    const [bloodSugar, setBloodSugar] = useState('')
    const [hemoglobin, setHemoglobin] = useState('')
    const [weight, setWeight] = useState('')

    // Next Consultation
    const [nextConsultationDate, setNextConsultationDate] = useState('')
    const [nextConsultationTime, setNextConsultationTime] = useState('10:00')

    // Nutrition Plan
    const [nutritionPlan, setNutritionPlan] = useState('')
    const [trimester, setTrimester] = useState(1)

    // Medications list
    const [medications, setMedications] = useState([
        { medication: '', dosage: '', startDate: '', endDate: '', schedule: '' }
    ])

    // Previous consultations for reference
    const [previousConsultations, setPreviousConsultations] = useState([])
    const [previousVitals, setPreviousVitals] = useState(null)
    const [consultationHistory, setConsultationHistory] = useState([])
    const [previousNutritionPlans, setPreviousNutritionPlans] = useState([])
    const [allVitalsHistory, setAllVitalsHistory] = useState([])

    // Voice Data Handler
    // Voice Data Handler (Memoized to prevent child re-renders)
    const handleVoiceData = React.useCallback((data) => {
        if (!data) return;

        let filledCount = 0;
        let newHealthStatus = '';

        setSystolicBP(prev => { if (data.systolicBP) { filledCount++; return data.systolicBP; } return prev; });
        setDiastolicBP(prev => { if (data.diastolicBP) { filledCount++; return data.diastolicBP; } return prev; });
        setHeartRate(prev => { if (data.heartRate) { filledCount++; return data.heartRate; } return prev; });
        setBloodSugar(prev => { if (data.bloodSugar) { filledCount++; return data.bloodSugar; } return prev; });
        setHemoglobin(prev => { if (data.hemoglobin) { filledCount++; return data.hemoglobin; } return prev; });
        setWeight(prev => { if (data.weight) { filledCount++; return data.weight; } return prev; });

        if (data.healthStatus) {
            setHealthStatus(prev => prev ? prev + "\n" + data.healthStatus : data.healthStatus);
            filledCount++;
        }

        if (data.medications && data.medications.length > 0) {
            setMedications(prevMeds => {
                const cleanCurrent = prevMeds.filter(m => m.medication.trim() !== '');
                const newMeds = data.medications.map(m => ({
                    medication: m.medication || '',
                    dosage: m.dosage || '',
                    schedule: m.schedule || '',
                    startDate: '',
                    endDate: ''
                }));
                if (newMeds.length > 0) filledCount++;
                return [...cleanCurrent, ...newMeds];
            });
        }

        if (data.nextConsultation) {
            if (data.nextConsultation.date) { setNextConsultationDate(data.nextConsultation.date); filledCount++; }
            if (data.nextConsultation.time) { setNextConsultationTime(data.nextConsultation.time); filledCount++; }
        }

        if (filledCount > 0) {
            setSuccess(`✨ AI Auto-filled ${filledCount} fields from voice!`);
            setTimeout(() => setSuccess(''), 4000);
        }
    }, []) // Empty dependency array as setters are stable

    // Load previous data
    useEffect(() => {
        if (motherId) {
            loadPreviousData()
        }
    }, [motherId])

    const loadPreviousData = async () => {
        setLoading(true)
        try {
            // Load ALL previous health metrics (vitals)
            const { data: metricsData } = await supabase
                .from('health_metrics')
                .select('*')
                .eq('mother_id', motherId)
                .order('created_at', { ascending: false })
                .limit(20)

            if (metricsData && metricsData.length > 0) {
                setPreviousVitals(metricsData[0])
                setAllVitalsHistory(metricsData)
                // Pre-fill with previous values for reference
                if (metricsData[0].notes) setHealthStatus(metricsData[0].notes)
            }

            // Load ALL previous nutrition plans
            const { data: nutritionData } = await supabase
                .from('nutrition_plans')
                .select('*')
                .eq('mother_id', motherId)
                .order('created_at', { ascending: false })
                .limit(10)

            if (nutritionData && nutritionData.length > 0) {
                setPreviousNutritionPlans(nutritionData)
                setNutritionPlan(nutritionData[0].plan || '')
                setTrimester(nutritionData[0].trimester || 1)
            }

            // Load ALL previous prescriptions
            const { data: prescriptionData } = await supabase
                .from('prescriptions')
                .select('*')
                .eq('mother_id', motherId)
                .order('created_at', { ascending: false })
                .limit(20)

            if (prescriptionData && prescriptionData.length > 0) {
                setPreviousConsultations(prescriptionData)
            }

            // Load previous consultation history from health_timeline
            const { data: historyData } = await supabase
                .from('health_timeline')
                .select('*')
                .eq('mother_id', motherId)
                .eq('event_type', 'doctor_consultation')
                .order('event_date', { ascending: false })
                .limit(20)

            if (historyData && historyData.length > 0) {
                setConsultationHistory(historyData)
            }

            // Load upcoming appointment
            const { data: appointmentData } = await supabase
                .from('appointments')
                .select('*')
                .eq('mother_id', motherId)
                .gte('appointment_date', new Date().toISOString())
                .order('appointment_date', { ascending: true })
                .limit(1)

            if (appointmentData && appointmentData[0]) {
                const apptDate = new Date(appointmentData[0].appointment_date)
                setNextConsultationDate(apptDate.toISOString().split('T')[0])
                setNextConsultationTime(apptDate.toTimeString().slice(0, 5))
            }

        } catch (err) {
            console.error('Error loading previous data:', err)
        } finally {
            setLoading(false)
        }
    }

    const addMedication = () => {
        setMedications([...medications, { medication: '', dosage: '', startDate: '', endDate: '', schedule: '' }])
    }

    const removeMedication = (index) => {
        if (medications.length > 1) {
            setMedications(medications.filter((_, i) => i !== index))
        }
    }

    const updateMedication = (index, field, value) => {
        const updated = [...medications]
        updated[index][field] = value
        setMedications(updated)
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setSaving(true)
        setError('')
        setSuccess('')

        try {
            // 1. Save health metrics (vitals + health status) to health_metrics table
            const hasVitals = systolicBP || diastolicBP || heartRate || bloodSugar || hemoglobin || weight || healthStatus
            if (hasVitals) {
                const healthMetricsRecord = {
                    id: crypto.randomUUID(),
                    mother_id: motherId,
                    weight_kg: weight ? parseFloat(weight) : null,
                    blood_pressure_systolic: systolicBP ? parseInt(systolicBP) : null,
                    blood_pressure_diastolic: diastolicBP ? parseInt(diastolicBP) : null,
                    hemoglobin: hemoglobin ? parseFloat(hemoglobin) : null,
                    blood_sugar: bloodSugar ? parseFloat(bloodSugar) : null,
                    measured_at: new Date().toISOString(),
                    notes: healthStatus.trim() || null
                }

                const { error: metricsError } = await supabase
                    .from('health_metrics')
                    .insert(healthMetricsRecord)

                if (metricsError) throw new Error(`Health Metrics Error: ${metricsError.message}`)
            }

            // 2. Save prescriptions to prescriptions table
            const validMedications = medications.filter(m => m.medication.trim())
            if (validMedications.length > 0) {
                const prescriptionRecords = validMedications.map(med => ({
                    mother_id: motherId,
                    medication: med.medication.trim(),
                    dosage: med.dosage.trim() || null,
                    start_date: med.startDate || null,
                    end_date: med.endDate || null,
                    schedule: med.schedule ? { instructions: med.schedule } : null
                }))

                const { error: prescriptionError } = await supabase
                    .from('prescriptions')
                    .insert(prescriptionRecords)

                if (prescriptionError) throw new Error(`Prescription Error: ${prescriptionError.message}`)
            }

            // 3. Save nutrition plan to nutrition_plans table
            if (nutritionPlan.trim()) {
                const { error: nutritionError } = await supabase
                    .from('nutrition_plans')
                    .insert({
                        mother_id: motherId,
                        plan: nutritionPlan.trim(),
                        trimester: trimester,
                        language: 'en'
                    })

                if (nutritionError) throw new Error(`Nutrition Plan Error: ${nutritionError.message}`)
            }

            // 4. Save next consultation appointment with IST timezone
            if (nextConsultationDate) {
                // Create date string with IST timezone offset (+05:30)
                // This ensures the time is stored exactly as selected, not converted to UTC
                const appointmentDateTimeIST = `${nextConsultationDate}T${nextConsultationTime}:00+05:30`

                const { error: appointmentError } = await supabase
                    .from('appointments')
                    .insert({
                        mother_id: motherId,
                        facility: doctorName || 'Doctor Consultation',
                        appointment_date: appointmentDateTimeIST,
                        status: 'scheduled',
                        appointment_type: 'consultation',
                        notes: `Scheduled by Dr. ${doctorName || 'Unknown'}`
                    })

                if (appointmentError) throw new Error(`Appointment Error: ${appointmentError.message}`)
            }

            // 5. Save consultation summary to health_timeline for historical record
            const consultationSummary = {
                mother_id: motherId,
                event_date: new Date().toISOString().split('T')[0],
                event_type: 'doctor_consultation',
                blood_pressure: (systolicBP && diastolicBP) ? `${systolicBP}/${diastolicBP}` : null,
                hemoglobin: hemoglobin ? parseFloat(hemoglobin) : null,
                sugar_level: bloodSugar ? parseFloat(bloodSugar) : null,
                weight: weight ? parseFloat(weight) : null,
                summary: healthStatus.trim() || 'Consultation completed',
                event_data: {
                    doctor_name: doctorName,
                    vitals: {
                        systolic_bp: systolicBP ? parseInt(systolicBP) : null,
                        diastolic_bp: diastolicBP ? parseInt(diastolicBP) : null,
                        heart_rate: heartRate ? parseInt(heartRate) : null,
                        blood_sugar: bloodSugar ? parseFloat(bloodSugar) : null,
                        hemoglobin: hemoglobin ? parseFloat(hemoglobin) : null,
                        weight: weight ? parseFloat(weight) : null
                    },
                    medications: validMedications.map(m => m.medication),
                    nutrition_plan: nutritionPlan.trim() || null,
                    next_consultation: nextConsultationDate || null,
                    recorded_at: new Date().toISOString()
                },
                concerns: null
            }

            const { error: timelineError } = await supabase
                .from('health_timeline')
                .insert(consultationSummary)

            if (timelineError) {
                console.warn('Timeline record error (non-fatal):', timelineError.message)
            }

            setSuccess('Consultation details saved successfully!')

            // Reset form for new entry
            setSystolicBP('')
            setDiastolicBP('')
            setHeartRate('')
            setBloodSugar('')
            setHemoglobin('')
            setWeight('')
            setMedications([{ medication: '', dosage: '', startDate: '', endDate: '', schedule: '' }])

            // Reload previous data
            await loadPreviousData()

            if (onSave) onSave()

        } catch (err) {
            console.error('Error saving consultation:', err)
            setError(err.message || 'Failed to save consultation details')
        } finally {
            setSaving(false)
        }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-center">
                    <Loader className="w-8 h-8 animate-spin mx-auto text-blue-600 mb-3" />
                    <p className="text-gray-600">Loading consultation data...</p>
                </div>
            </div>
        )
    }

    return (
        <div className="h-full overflow-y-auto p-6 bg-gray-50 bg-[url('https://as1.ftcdn.net/v2/jpg/04/83/87/46/1000_F_483874697_M7F7G2Kk6x93B6d2e6m78X7.jpg')] bg-repeat opacity-95">
            {/* Sticky Heading with Voice Button */}
            <div className="flex justify-between items-center mb-6 sticky top-0 bg-white/95 backdrop-blur-sm z-20 p-4 rounded-xl shadow-sm border border-gray-200">
                <div>
                    <h2 className="text-xl font-bold text-gray-800">New Consultation</h2>
                    <p className="text-sm text-gray-500">Dr. {doctorName}</p>
                </div>

                {/* Voice Input Button */}
                <div className="flex flex-col items-center">
                    <VoiceInput onDataReceived={handleVoiceData} />
                    <span className="text-[10px] text-gray-500 font-medium mt-1 uppercase tracking-wide">Tap to Speak</span>
                </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6 max-w-4xl mx-auto pb-20">

                {/* Success/Error Messages */}
                {success && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3 animate-in fade-in slide-in-from-top-2">
                        <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
                        <p className="text-green-800 font-medium">{success}</p>
                    </div>
                )}

                {error && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3 animate-in fade-in slide-in-from-top-2">
                        <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
                        <p className="text-red-800">{error}</p>
                    </div>
                )}

                {/* Vital Signs Section */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                        <Activity className="w-5 h-5 text-red-500" />
                        Vital Signs
                    </h3>


                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        {/* Blood Pressure */}
                        <div className="col-span-2 md:col-span-1">
                            <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                                <Heart className="w-4 h-4 text-red-500" />
                                Blood Pressure (mmHg)
                            </label>
                            <div className="flex gap-2 items-center">
                                <input
                                    type="number"
                                    value={systolicBP}
                                    onChange={(e) => setSystolicBP(e.target.value)}
                                    placeholder="Systolic"
                                    min="60"
                                    max="250"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                                />
                                <span className="text-gray-500 font-bold">/</span>
                                <input
                                    type="number"
                                    value={diastolicBP}
                                    onChange={(e) => setDiastolicBP(e.target.value)}
                                    placeholder="Diastolic"
                                    min="40"
                                    max="150"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                                />
                            </div>
                        </div>

                        {/* Heart Rate */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                                <Activity className="w-4 h-4 text-pink-500" />
                                Heart Rate (bpm)
                            </label>
                            <input
                                type="number"
                                value={heartRate}
                                onChange={(e) => setHeartRate(e.target.value)}
                                placeholder="e.g., 72"
                                min="40"
                                max="200"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                            />
                        </div>

                        {/* Blood Sugar / Glucose */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                                <Droplet className="w-4 h-4 text-orange-500" />
                                Blood Sugar (mg/dL)
                            </label>
                            <input
                                type="number"
                                value={bloodSugar}
                                onChange={(e) => setBloodSugar(e.target.value)}
                                placeholder="e.g., 95"
                                min="20"
                                max="600"
                                step="0.1"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                            />
                        </div>

                        {/* Hemoglobin */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                                <Thermometer className="w-4 h-4 text-purple-500" />
                                Hemoglobin (g/dL)
                            </label>
                            <input
                                type="number"
                                value={hemoglobin}
                                onChange={(e) => setHemoglobin(e.target.value)}
                                placeholder="e.g., 12.5"
                                min="4"
                                max="20"
                                step="0.1"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                            />
                        </div>

                        {/* Weight */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                                <Scale className="w-4 h-4 text-blue-500" />
                                Weight (kg)
                            </label>
                            <input
                                type="number"
                                value={weight}
                                onChange={(e) => setWeight(e.target.value)}
                                placeholder="e.g., 65"
                                min="30"
                                max="200"
                                step="0.1"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                            />
                        </div>
                    </div>
                </div>

                {/* Health Status Section */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                        <Heart className="w-5 h-5 text-red-500" />
                        Health Status & Observations
                    </h3>
                    <textarea
                        value={healthStatus}
                        onChange={(e) => setHealthStatus(e.target.value)}
                        placeholder="Enter patient's current health status, observations, symptoms, concerns, and clinical notes..."
                        rows={4}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-gray-900"
                    />
                </div>

                {/* Next Consultation Section */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                        <Calendar className="w-5 h-5 text-blue-500" />
                        Next Consultation Schedule
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Date</label>
                            <input
                                type="date"
                                value={nextConsultationDate}
                                onChange={(e) => setNextConsultationDate(e.target.value)}
                                min={new Date().toISOString().split('T')[0]}
                                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Time</label>
                            <div className="relative">
                                <Clock className="absolute left-3 top-3.5 w-5 h-5 text-gray-400" />
                                <input
                                    type="time"
                                    value={nextConsultationTime}
                                    onChange={(e) => setNextConsultationTime(e.target.value)}
                                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Nutrition Plan Section */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                        <Apple className="w-5 h-5 text-green-500" />
                        Nutrition Plan
                    </h3>
                    <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-700 mb-2">Trimester</label>
                        <select
                            value={trimester}
                            onChange={(e) => setTrimester(Number(e.target.value))}
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                            <option value={1}>First Trimester (Week 1-12)</option>
                            <option value={2}>Second Trimester (Week 13-26)</option>
                            <option value={3}>Third Trimester (Week 27-40)</option>
                        </select>
                    </div>
                    <textarea
                        value={nutritionPlan}
                        onChange={(e) => setNutritionPlan(e.target.value)}
                        placeholder="Enter dietary recommendations, foods to include, foods to avoid, supplements..."
                        rows={5}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-gray-900"
                    />
                </div>

                {/* Medication Plan Section */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                            <Pill className="w-5 h-5 text-purple-500" />
                            Medication Plan
                        </h3>
                        <button
                            type="button"
                            onClick={addMedication}
                            className="bg-purple-100 hover:bg-purple-200 text-purple-700 px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-1 transition-colors"
                        >
                            <Plus className="w-4 h-4" />
                            Add Medication
                        </button>
                    </div>

                    <div className="space-y-4">
                        {medications.map((med, index) => (
                            <div key={index} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                                <div className="flex items-center justify-between mb-3">
                                    <span className="text-sm font-medium text-gray-700">Medication #{index + 1}</span>
                                    {medications.length > 1 && (
                                        <button
                                            type="button"
                                            onClick={() => removeMedication(index)}
                                            className="text-red-600 hover:text-red-700 p-1"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    )}
                                </div>
                                <div className="grid grid-cols-2 gap-3">
                                    <div className="col-span-2">
                                        <input
                                            type="text"
                                            value={med.medication}
                                            onChange={(e) => updateMedication(index, 'medication', e.target.value)}
                                            placeholder="Medication name (e.g., Folic Acid, Iron Supplement)"
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                                        />
                                    </div>
                                    <div>
                                        <input
                                            type="text"
                                            value={med.dosage}
                                            onChange={(e) => updateMedication(index, 'dosage', e.target.value)}
                                            placeholder="Dosage (e.g., 400mcg)"
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                                        />
                                    </div>
                                    <div>
                                        <input
                                            type="text"
                                            value={med.schedule}
                                            onChange={(e) => updateMedication(index, 'schedule', e.target.value)}
                                            placeholder="Schedule (e.g., Once daily)"
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs text-gray-500 mb-1">Start Date</label>
                                        <input
                                            type="date"
                                            value={med.startDate}
                                            onChange={(e) => updateMedication(index, 'startDate', e.target.value)}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs text-gray-500 mb-1">End Date</label>
                                        <input
                                            type="date"
                                            value={med.endDate}
                                            onChange={(e) => updateMedication(index, 'endDate', e.target.value)}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                                        />
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Previous Consultation History */}
                {consultationHistory.length > 0 && (
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                        <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                            <Calendar className="w-5 h-5 text-blue-500" />
                            Previous Consultation History
                        </h3>
                        <div className="space-y-4">
                            {consultationHistory.map((record, idx) => (
                                <div key={record.id || idx} className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-100">
                                    <div className="flex justify-between items-start mb-3">
                                        <div className="flex items-center gap-2">
                                            <span className="bg-blue-600 text-white text-xs px-2 py-1 rounded-full font-semibold">
                                                Consultation #{consultationHistory.length - idx}
                                            </span>
                                            <span className="text-sm font-medium text-gray-700">
                                                📅 {record.event_date ? new Date(record.event_date).toLocaleDateString('en-IN', {
                                                    day: 'numeric',
                                                    month: 'short',
                                                    year: 'numeric'
                                                }) : 'Date N/A'}
                                            </span>
                                        </div>
                                        {record.event_data?.doctor_name && (
                                            <span className="text-xs text-gray-500">Dr. {record.event_data.doctor_name}</span>
                                        )}
                                    </div>

                                    {/* Vitals Summary */}
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">
                                        {record.blood_pressure && (
                                            <div className="bg-white px-3 py-2 rounded text-xs">
                                                <span className="text-gray-500">BP:</span>
                                                <span className="font-semibold text-gray-800 ml-1">{record.blood_pressure} mmHg</span>
                                            </div>
                                        )}
                                        {record.hemoglobin && (
                                            <div className="bg-white px-3 py-2 rounded text-xs">
                                                <span className="text-gray-500">Hb:</span>
                                                <span className="font-semibold text-gray-800 ml-1">{record.hemoglobin} g/dL</span>
                                            </div>
                                        )}
                                        {record.sugar_level && (
                                            <div className="bg-white px-3 py-2 rounded text-xs">
                                                <span className="text-gray-500">Sugar:</span>
                                                <span className="font-semibold text-gray-800 ml-1">{record.sugar_level} mg/dL</span>
                                            </div>
                                        )}
                                        {record.weight && (
                                            <div className="bg-white px-3 py-2 rounded text-xs">
                                                <span className="text-gray-500">Weight:</span>
                                                <span className="font-semibold text-gray-800 ml-1">{record.weight} kg</span>
                                            </div>
                                        )}
                                    </div>

                                    {/* Summary/Notes */}
                                    {record.summary && (
                                        <div className="text-sm text-gray-700 bg-white p-2 rounded">
                                            <span className="font-medium">Notes:</span> {record.summary}
                                        </div>
                                    )}

                                    {/* Medications if available */}
                                    {record.event_data?.medications?.length > 0 && (
                                        <div className="mt-2 text-xs text-gray-600">
                                            <span className="font-medium">💊 Medications:</span> {record.event_data.medications.join(', ')}
                                        </div>
                                    )}

                                    {/* Nutrition Plan if available */}
                                    {record.event_data?.nutrition_plan && (
                                        <div className="mt-2 text-xs text-gray-600 bg-green-50 p-2 rounded border border-green-100">
                                            <span className="font-medium text-green-700">🍎 Nutrition Plan:</span>
                                            <p className="mt-1 text-gray-700">{record.event_data.nutrition_plan}</p>
                                        </div>
                                    )}

                                    {/* Next Consultation if recorded */}
                                    {record.event_data?.next_consultation && (
                                        <div className="mt-2 text-xs text-blue-600">
                                            <span className="font-medium">📅 Next Appointment:</span> {new Date(record.event_data.next_consultation).toLocaleDateString('en-IN', {
                                                day: 'numeric',
                                                month: 'short',
                                                year: 'numeric'
                                            })}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Previous Prescriptions Reference */}
                {previousConsultations.length > 0 && (
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                        <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                            <Pill className="w-5 h-5 text-purple-500" />
                            Previous Prescriptions
                        </h3>
                        <div className="space-y-2">
                            {previousConsultations.map((presc, idx) => (
                                <div key={presc.id || idx} className="bg-gray-50 p-3 rounded-lg text-sm flex justify-between items-center">
                                    <div>
                                        <span className="font-medium text-gray-900">{presc.medication}</span>
                                        {presc.dosage && <span className="text-gray-600 ml-2">- {presc.dosage}</span>}
                                    </div>
                                    <span className="text-xs text-gray-500 bg-gray-200 px-2 py-1 rounded">
                                        📅 {presc.created_at && new Date(presc.created_at).toLocaleDateString('en-IN', {
                                            day: 'numeric',
                                            month: 'short',
                                            year: 'numeric'
                                        })}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Previous Nutrition Plans History */}
                {previousNutritionPlans.length > 0 && (
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                        <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                            <Apple className="w-5 h-5 text-green-500" />
                            Previous Nutrition Plans
                        </h3>
                        <div className="space-y-3">
                            {previousNutritionPlans.map((plan, idx) => (
                                <div key={plan.id || idx} className="bg-gradient-to-r from-green-50 to-emerald-50 p-4 rounded-lg border border-green-100">
                                    <div className="flex justify-between items-start mb-2">
                                        <div className="flex items-center gap-2">
                                            <span className="bg-green-600 text-white text-xs px-2 py-1 rounded-full font-semibold">
                                                Trimester {plan.trimester || '?'}
                                            </span>
                                            <span className="text-xs text-gray-500 bg-green-100 px-2 py-1 rounded">
                                                📅 {plan.created_at && new Date(plan.created_at).toLocaleDateString('en-IN', {
                                                    day: 'numeric',
                                                    month: 'short',
                                                    year: 'numeric'
                                                })}
                                            </span>
                                        </div>
                                    </div>
                                    <p className="text-sm text-gray-700 whitespace-pre-wrap">
                                        {plan.plan}
                                    </p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Previous Vitals History */}
                {allVitalsHistory.length > 0 && (
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                        <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                            <Activity className="w-5 h-5 text-red-500" />
                            Complete Vitals History
                        </h3>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="bg-gray-50 border-b">
                                        <th className="px-3 py-2 text-left text-gray-600 font-semibold">Date</th>
                                        <th className="px-3 py-2 text-center text-gray-600 font-semibold">BP (mmHg)</th>
                                        <th className="px-3 py-2 text-center text-gray-600 font-semibold">Sugar (mg/dL)</th>
                                        <th className="px-3 py-2 text-center text-gray-600 font-semibold">Hb (g/dL)</th>
                                        <th className="px-3 py-2 text-center text-gray-600 font-semibold">Weight (kg)</th>
                                        <th className="px-3 py-2 text-left text-gray-600 font-semibold">Notes</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {allVitalsHistory.map((vital, idx) => (
                                        <tr key={vital.id || idx} className={`border-b ${idx === 0 ? 'bg-blue-50' : ''}`}>
                                            <td className="px-3 py-2 text-gray-700">
                                                <div className="flex items-center gap-1">
                                                    {idx === 0 && <span className="text-xs text-blue-600 font-semibold">(Latest)</span>}
                                                    📅 {vital.measured_at || vital.created_at ? new Date(vital.measured_at || vital.created_at).toLocaleDateString('en-IN', {
                                                        day: 'numeric',
                                                        month: 'short',
                                                        year: 'numeric'
                                                    }) : 'N/A'}
                                                </div>
                                            </td>
                                            <td className="px-3 py-2 text-center">
                                                {vital.blood_pressure_systolic && vital.blood_pressure_diastolic ? (
                                                    <span className="font-medium text-red-700">
                                                        {vital.blood_pressure_systolic}/{vital.blood_pressure_diastolic}
                                                    </span>
                                                ) : '-'}
                                            </td>
                                            <td className="px-3 py-2 text-center">
                                                {vital.blood_sugar ? (
                                                    <span className="font-medium text-orange-700">{vital.blood_sugar}</span>
                                                ) : '-'}
                                            </td>
                                            <td className="px-3 py-2 text-center">
                                                {vital.hemoglobin ? (
                                                    <span className={`font-medium ${vital.hemoglobin < 11 ? 'text-red-600' : 'text-green-700'}`}>
                                                        {vital.hemoglobin}
                                                    </span>
                                                ) : '-'}
                                            </td>
                                            <td className="px-3 py-2 text-center">
                                                {vital.weight_kg ? (
                                                    <span className="font-medium text-blue-700">{vital.weight_kg}</span>
                                                ) : '-'}
                                            </td>
                                            <td className="px-3 py-2 text-gray-600 max-w-xs truncate" title={vital.notes || ''}>
                                                {vital.notes ? vital.notes.substring(0, 50) + (vital.notes.length > 50 ? '...' : '') : '-'}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* Submit Button */}
                <button
                    type="submit"
                    disabled={saving}
                    className="w-full bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 disabled:from-gray-400 disabled:to-gray-500 text-white py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-3 transition-all transform hover:scale-[1.02] disabled:scale-100 shadow-lg"
                >
                    {saving ? (
                        <>
                            <Loader className="w-5 h-5 animate-spin" />
                            Saving Consultation Details...
                        </>
                    ) : (
                        <>
                            <Save className="w-5 h-5" />
                            Save Consultation Details
                        </>
                    )}
                </button>
            </form>
        </div>
    )
}
