// Signup Screen — matches website Signup.jsx (document upload, name validation, role-based)
import React, { useState, useEffect } from 'react';
import {
    View, Text, TextInput, TouchableOpacity, ScrollView, StyleSheet, Alert,
    KeyboardAvoidingView, Platform, ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as DocumentPicker from 'expo-document-picker';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';
import { authAPI, certificateAPI } from '../../services/api';
import { typography, spacing, borderRadius } from '../../theme';

export default function SignupScreen({ navigation }) {
    const { theme } = useTheme();
    const { signInWithGoogle, user, isAuthenticated } = useAuth();

    const isProfileCompletion = isAuthenticated && !user?.role;

    const [formData, setFormData] = useState({
        fullName: user?.fullName || '',
        email: user?.email || '',
        password: '',
        confirmPassword: '',
        role: 'ASHA_WORKER',
        phone: '',
        assignedArea: '',
    });
    const [idFile, setIdFile] = useState(null);
    const [degreeFile, setDegreeFile] = useState(null);
    const [idValidation, setIdValidation] = useState(null);
    const [certValidation, setCertValidation] = useState(null);
    const [nameMatch, setNameMatch] = useState(null);
    const [validatingId, setValidatingId] = useState(false);
    const [validatingCert, setValidatingCert] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [countdown, setCountdown] = useState(5);

    // Auto redirect after success
    useEffect(() => {
        if (success) {
            const timer = setInterval(() => {
                setCountdown((p) => {
                    if (p <= 1) { clearInterval(timer); navigation.navigate('Login'); return 0; }
                    return p - 1;
                });
            }, 1000);
            return () => clearInterval(timer);
        }
    }, [success]);

    // Redirect if already has role
    useEffect(() => {
        if (isAuthenticated && user?.role) {
            // Navigate handled by AppNavigator
        }
    }, [isAuthenticated, user]);

    const handleChange = (key, value) => {
        setFormData((p) => ({ ...p, [key]: value }));
        setError('');
        // Re-check name match
        if (key === 'fullName') {
            if (formData.role === 'ASHA_WORKER' && idValidation?.info?.full_name) {
                checkNameMatch(value, idValidation.info.full_name);
            } else if (formData.role === 'DOCTOR' && certValidation?.info?.doctor_name) {
                checkNameMatch(value, certValidation.info.doctor_name);
            }
        }
    };

    const checkNameMatch = (formName, docName) => {
        if (!formName || !docName) { setNameMatch(null); return; }
        const a = formName.toLowerCase().replace(/[^a-z\s]/g, '').trim();
        const b = docName.toLowerCase().replace(/[^a-z\s]/g, '').trim();
        const isMatch = a === b || b.includes(a) || a.includes(b);
        setNameMatch({
            match: isMatch, formName, docName,
            message: isMatch ? '✅ Name matches ID document' : `⚠️ Name mismatch: Form says "${formName}" but ID shows "${docName}".`,
        });
    };

    // ASHA worker ID upload
    const handleIdUpload = async () => {
        try {
            const result = await DocumentPicker.getDocumentAsync({
                type: ['application/pdf', 'image/*'],
            });
            if (result.canceled) return;
            const file = result.assets[0];
            setIdFile(file);
            setIdValidation(null);
            setValidatingId(true);
            setError('');

            try {
                const formDataUpload = new FormData();
                formDataUpload.append('file', { uri: file.uri, name: file.name, type: file.mimeType });
                const res = await certificateAPI.validateAshaID(formDataUpload);
                if (res?.data?.success && res?.data?.eligible) {
                    const docName = res.data.id_info?.full_name || '';
                    setIdValidation({ valid: true, info: res.data.id_info, message: `✅ ID verified: ${docName}` });
                    checkNameMatch(formData.fullName, docName);
                } else {
                    setIdValidation({ valid: false, message: res?.data?.error || 'ID validation failed' });
                }
            } catch (err) {
                const errMsg = err.response?.data?.detail || err.message || 'Failed to validate ID';
                if (errMsg.includes('429') || errMsg.includes('RESOURCE_EXHAUSTED') || errMsg.includes('Quota')) {
                    setIdValidation({ valid: true, info: null, message: '⚠️ Auto-verification unavailable. Admin will verify manually.' });
                    setError('');
                } else {
                    setIdValidation({ valid: false, message: errMsg });
                }
            } finally { setValidatingId(false); }
        } catch { }
    };

    // Doctor cert upload
    const handleCertUpload = async () => {
        try {
            const result = await DocumentPicker.getDocumentAsync({
                type: ['application/pdf', 'image/*'],
            });
            if (result.canceled) return;
            const file = result.assets[0];
            setDegreeFile(file);
            setCertValidation(null);
            setValidatingCert(true);

            try {
                const formDataUpload = new FormData();
                formDataUpload.append('file', { uri: file.uri, name: file.name, type: file.mimeType });
                const res = await certificateAPI.parseCertificate(formDataUpload);
                if (res?.data?.parsed_data) {
                    const docName = res.data.parsed_data.doctor_name || '';
                    if (docName && docName !== 'Unknown') {
                        setCertValidation({ valid: true, info: res.data.parsed_data, message: `✅ Certificate parsed: ${docName}` });
                        checkNameMatch(formData.fullName, docName);
                    } else {
                        setCertValidation({ valid: false, message: "Could not extract name from certificate." });
                    }
                }
            } catch {
                setCertValidation({ valid: true, info: null, message: '⚠️ Could not auto-read certificate (Manual review required)' });
            } finally { setValidatingCert(false); }
        } catch { }
    };

    const handleSubmit = async () => {
        setError('');
        // Validation
        if (!isProfileCompletion && formData.password !== formData.confirmPassword) {
            setError('Passwords do not match'); return;
        }
        if (!isProfileCompletion && formData.password.length < 8) {
            setError('Password must be at least 8 characters'); return;
        }
        if (formData.role === 'ASHA_WORKER') {
            if (!idFile) { setError('Please upload your ID document (PAN/Aadhaar/Driving License)'); return; }
            if (!idValidation?.valid) { setError('ID document validation failed.'); return; }
            if (nameMatch && !nameMatch.match) {
                setError(`Name mismatch: "${formData.fullName}" doesn't match ID name "${nameMatch.docName}".`); return;
            }
        }
        if (formData.role === 'DOCTOR' && !degreeFile) {
            setError('Please upload your degree certification'); return;
        }

        setLoading(true);
        try {
            let degreeUrl = null, uploadedIdDocUrl = null;

            if (formData.role === 'ASHA_WORKER' && idFile) {
                try {
                    const formDataUp = new FormData();
                    formDataUp.append('file', { uri: idFile.uri, name: idFile.name, type: idFile.mimeType });
                    const idUpload = await authAPI.uploadCertification(formData.email, formDataUp);
                    uploadedIdDocUrl = idUpload?.data?.public_url || null;
                } catch { }
            }
            if (formData.role === 'DOCTOR' && degreeFile) {
                const formDataUp = new FormData();
                formDataUp.append('file', { uri: degreeFile.uri, name: degreeFile.name, type: degreeFile.mimeType });
                const up = await authAPI.uploadCertification(formData.email, formDataUp);
                degreeUrl = up?.data?.public_url || null;
            }

            const payload = {
                email: formData.email, password: isProfileCompletion ? null : formData.password,
                full_name: formData.fullName, role: formData.role,
                phone: formData.phone, assigned_area: formData.assignedArea,
                degree_cert_url: degreeUrl,
                id_info: formData.role === 'ASHA_WORKER' && idValidation?.info ? {
                    ...idValidation.info, name_verified: nameMatch?.match || false,
                    form_name: formData.fullName, document_name: idValidation?.info?.full_name,
                } : null,
                document_metadata: formData.role === 'DOCTOR' && certValidation?.info ? {
                    ...certValidation.info, name_verified: nameMatch?.match || false,
                    form_name: formData.fullName, document_name: certValidation?.info?.doctor_name,
                } : null,
                id_doc_url: uploadedIdDocUrl,
            };

            const res = await authAPI.createRegisterRequest(payload);
            if (res?.data?.success) { setSuccess(true); return; }
            throw new Error('Failed to submit registration request');
        } catch (err) {
            setError(err.message || 'Failed to sign up');
        } finally { setLoading(false); }
    };

    // Success view
    if (success) {
        return (
            <View style={[styles.container, { backgroundColor: theme.backgroundGradientFrom, justifyContent: 'center', alignItems: 'center' }]}>
                <View style={[styles.formCard, { backgroundColor: theme.surface, alignItems: 'center' }]}>
                    <Text style={{ fontSize: 48, color: theme.success }}>✓</Text>
                    <Text style={[styles.welcomeTitle, { color: theme.text, marginTop: 12 }]}>Registration Successful!</Text>
                    <Text style={[styles.subtitle, { color: theme.textSecondary, marginTop: 8, textAlign: 'center' }]}>
                        Please check your email to verify your account.
                    </Text>
                    <Text style={[styles.subtitle, { color: theme.textTertiary, marginTop: 12 }]}>
                        Redirecting to login in {countdown} seconds...
                    </Text>
                </View>
            </View>
        );
    }

    return (
        <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
            <ScrollView
                style={{ backgroundColor: theme.backgroundGradientFrom || '#FDF2F8' }}
                contentContainerStyle={styles.container}
                keyboardShouldPersistTaps="handled"
            >
                {/* Header */}
                <View style={styles.header}>
                    <Text style={[styles.brandTitle, { color: theme.primary }]}>🤰 Aanchal AI</Text>
                    <Text style={[styles.welcomeTitle, { color: theme.text }]}>
                        {isProfileCompletion ? 'Complete Your Profile' : 'Create Account'}
                    </Text>
                    <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
                        {isProfileCompletion ? 'Please provide additional details to verify your role' : 'Join the Aanchal AI healthcare system'}
                    </Text>
                </View>

                {error !== '' && (
                    <View style={[styles.errorBox, { backgroundColor: theme.errorLight, borderColor: '#FECACA' }]}>
                        <Text style={{ color: '#B91C1C', fontSize: 13 }}>{error}</Text>
                    </View>
                )}

                <View style={[styles.formCard, { backgroundColor: theme.surface }]}>
                    {/* Full Name */}
                    <Field label="Full Name *" value={formData.fullName} onChange={(v) => handleChange('fullName', v)} placeholder="Dr. John Doe" theme={theme} />
                    {/* Name match indicator */}
                    {nameMatch && (idValidation?.valid || certValidation?.valid) && (
                        <View style={[styles.matchBox, { backgroundColor: nameMatch.match ? '#F0FDF4' : '#FFFBEB', borderColor: nameMatch.match ? '#BBF7D0' : '#FDE68A' }]}>
                            <Text style={{ color: nameMatch.match ? '#166534' : '#92400E', fontSize: 12 }}>{nameMatch.message}</Text>
                        </View>
                    )}

                    {/* Email */}
                    <Field label="Email Address *" value={formData.email} onChange={(v) => handleChange('email', v)} placeholder="your@email.com" keyboard="email-address" theme={theme} />

                    {/* Role */}
                    <View style={styles.field}>
                        <Text style={[styles.label, { color: theme.textSecondary }]}>Role *</Text>
                        <View style={styles.roleRow}>
                            {['ASHA_WORKER', 'DOCTOR'].map((r) => (
                                <TouchableOpacity
                                    key={r}
                                    style={[styles.roleBtn, formData.role === r && { backgroundColor: theme.primary, borderColor: theme.primary }]}
                                    onPress={() => handleChange('role', r)}
                                >
                                    <Text style={[styles.roleBtnText, { color: formData.role === r ? '#fff' : theme.text }]}>
                                        {r === 'ASHA_WORKER' ? 'ASHA Worker' : 'Doctor'}
                                    </Text>
                                </TouchableOpacity>
                            ))}
                        </View>
                        <Text style={[styles.hint, { color: theme.textTertiary }]}>Select your role in the healthcare system</Text>
                    </View>

                    {/* ASHA Worker ID */}
                    {formData.role === 'ASHA_WORKER' && (
                        <View style={styles.field}>
                            <Text style={[styles.label, { color: theme.textSecondary }]}>ID Document * (PAN / Aadhaar / DL)</Text>
                            <TouchableOpacity style={[styles.uploadBtn, { borderColor: theme.border }]} onPress={handleIdUpload}>
                                <Ionicons name="cloud-upload-outline" size={20} color={theme.primary} />
                                <Text style={[styles.uploadText, { color: theme.textSecondary }]}>
                                    {idFile ? idFile.name : 'Choose File'}
                                </Text>
                            </TouchableOpacity>
                            {validatingId && (
                                <View style={styles.validatingRow}>
                                    <ActivityIndicator size="small" color={theme.info} />
                                    <Text style={{ color: theme.info, fontSize: 12, marginLeft: 6 }}>Validating ID document...</Text>
                                </View>
                            )}
                            {idValidation && (
                                <Text style={{ color: idValidation.valid ? theme.success : theme.error, fontSize: 12, marginTop: 6 }}>
                                    {idValidation.message}
                                </Text>
                            )}
                            <Text style={[styles.hint, { color: theme.textTertiary }]}>Upload your government ID for verification</Text>
                        </View>
                    )}

                    {/* Doctor degree */}
                    {formData.role === 'DOCTOR' && (
                        <View style={styles.field}>
                            <Text style={[styles.label, { color: theme.textSecondary }]}>Degree Certification *</Text>
                            <TouchableOpacity style={[styles.uploadBtn, { borderColor: theme.border }]} onPress={handleCertUpload}>
                                <Ionicons name="cloud-upload-outline" size={20} color={theme.primary} />
                                <Text style={[styles.uploadText, { color: theme.textSecondary }]}>
                                    {degreeFile ? degreeFile.name : 'Choose File'}
                                </Text>
                            </TouchableOpacity>
                            {validatingCert && (
                                <View style={styles.validatingRow}>
                                    <ActivityIndicator size="small" color={theme.info} />
                                    <Text style={{ color: theme.info, fontSize: 12, marginLeft: 6 }}>Analyzing certificate...</Text>
                                </View>
                            )}
                            {certValidation && (
                                <Text style={{ color: certValidation.valid ? theme.success : theme.textSecondary, fontSize: 12, marginTop: 6 }}>
                                    {certValidation.message}
                                </Text>
                            )}
                            <Text style={[styles.hint, { color: theme.textTertiary }]}>Upload PDF or image of your medical degree</Text>
                        </View>
                    )}

                    {/* Phone & Area side by side */}
                    <Field label="Phone Number" value={formData.phone} onChange={(v) => handleChange('phone', v)} placeholder="+91 9876543210" keyboard="phone-pad" theme={theme} />
                    <Field label="Assigned Area" value={formData.assignedArea} onChange={(v) => handleChange('assignedArea', v)} placeholder="e.g., Pune, Mumbai" theme={theme} />

                    {/* Passwords */}
                    {!isProfileCompletion && (
                        <>
                            <Field label="Password *" value={formData.password} onChange={(v) => handleChange('password', v)} placeholder="••••••••" secure theme={theme} hint="Minimum 8 characters" />
                            <Field label="Confirm Password *" value={formData.confirmPassword} onChange={(v) => handleChange('confirmPassword', v)} placeholder="••••••••" secure theme={theme} />
                        </>
                    )}

                    {/* Submit */}
                    <TouchableOpacity
                        style={[styles.primaryBtn, { backgroundColor: theme.primary, opacity: loading ? 0.5 : 1 }]}
                        onPress={handleSubmit}
                        disabled={loading}
                    >
                        <Text style={styles.primaryBtnText}>
                            {loading ? 'Submitting request...' : 'Submit Registration Request'}
                        </Text>
                    </TouchableOpacity>

                    {!isProfileCompletion && (
                        <>
                            <View style={styles.divider}>
                                <View style={[styles.dividerLine, { backgroundColor: theme.border }]} />
                                <Text style={[styles.dividerText, { color: theme.placeholder, backgroundColor: theme.surface }]}>Or continue with</Text>
                                <View style={[styles.dividerLine, { backgroundColor: theme.border }]} />
                            </View>

                            <TouchableOpacity style={[styles.googleBtn, { borderColor: theme.border }]} onPress={handleGoogleSignIn} disabled={loading}>
                                <Ionicons name="logo-google" size={18} color="#4285F4" />
                                <Text style={[styles.googleBtnText, { color: theme.textSecondary }]}>Sign up with Google</Text>
                            </TouchableOpacity>

                            <View style={styles.signupRow}>
                                <Text style={{ color: theme.textSecondary, fontSize: 13 }}>Already have an account? </Text>
                                <TouchableOpacity onPress={() => navigation.navigate('Login')}>
                                    <Text style={{ color: theme.primary, fontSize: 13, fontWeight: '600' }}>Log in</Text>
                                </TouchableOpacity>
                            </View>
                        </>
                    )}
                </View>
            </ScrollView>
        </KeyboardAvoidingView>
    );
}

// Reusable Field component
function Field({ label, value, onChange, placeholder, keyboard, secure, theme, hint }) {
    return (
        <View style={styles.field}>
            <Text style={[styles.label, { color: theme.textSecondary }]}>{label}</Text>
            <TextInput
                style={[styles.input, { color: theme.text, borderColor: theme.border }]}
                placeholder={placeholder}
                placeholderTextColor={theme.placeholder}
                value={value}
                onChangeText={onChange}
                keyboardType={keyboard || 'default'}
                secureTextEntry={secure}
                autoCapitalize={keyboard === 'email-address' ? 'none' : 'words'}
            />
            {hint && <Text style={[styles.hint, { color: theme.textTertiary }]}>{hint}</Text>}
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flexGrow: 1, paddingHorizontal: spacing.screenPadding, paddingVertical: 40 },
    header: { alignItems: 'center', marginBottom: 24 },
    brandTitle: { fontSize: 28, fontWeight: '700', marginBottom: 8 },
    welcomeTitle: { fontSize: 22, fontWeight: '700' },
    subtitle: { fontSize: 14, marginTop: 4 },
    errorBox: { borderWidth: 1, borderRadius: 10, padding: 12, marginBottom: 16 },
    formCard: {
        borderRadius: 14, padding: 24,
        shadowColor: '#000', shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.1, shadowRadius: 16, elevation: 6,
    },
    field: { marginBottom: 14 },
    label: { fontSize: 13, fontWeight: '500', marginBottom: 6 },
    input: { borderWidth: 1, borderRadius: 10, paddingHorizontal: 14, paddingVertical: 10, fontSize: 15 },
    hint: { fontSize: 11, marginTop: 4 },
    roleRow: { flexDirection: 'row', gap: 10 },
    roleBtn: { flex: 1, paddingVertical: 10, borderRadius: 10, borderWidth: 1.5, borderColor: '#D1D5DB', alignItems: 'center' },
    roleBtnText: { fontWeight: '600', fontSize: 14 },
    uploadBtn: {
        flexDirection: 'row', alignItems: 'center', gap: 8,
        borderWidth: 1, borderStyle: 'dashed', borderRadius: 10,
        paddingVertical: 12, paddingHorizontal: 14,
    },
    uploadText: { fontSize: 14 },
    validatingRow: { flexDirection: 'row', alignItems: 'center', marginTop: 8 },
    matchBox: { borderWidth: 1, borderRadius: 8, padding: 8, marginBottom: 14 },
    primaryBtn: { paddingVertical: 14, borderRadius: 10, alignItems: 'center', marginTop: 8 },
    primaryBtnText: { color: '#fff', fontSize: 15, fontWeight: '600' },
    divider: { flexDirection: 'row', alignItems: 'center', marginVertical: 20 },
    dividerLine: { flex: 1, height: 1 },
    dividerText: { paddingHorizontal: 10, fontSize: 13 },
    googleBtn: {
        flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
        borderWidth: 1, borderRadius: 10, paddingVertical: 12, gap: 10,
    },
    googleBtnText: { fontSize: 14, fontWeight: '500' },
    signupRow: { flexDirection: 'row', justifyContent: 'center', marginTop: 16 },
});
