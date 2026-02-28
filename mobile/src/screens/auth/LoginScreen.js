// Login Screen — matches website Login.jsx (purple theme, cold start warning, role-based redirect)
import React, { useState, useEffect } from 'react';
import {
    View, Text, TextInput, TouchableOpacity, ScrollView, StyleSheet, Alert, KeyboardAvoidingView, Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';
import { typography, spacing, borderRadius } from '../../theme';

export default function LoginScreen({ navigation }) {
    const { theme } = useTheme();
    const { signIn, signInWithGoogle } = useAuth();

    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async () => {
        if (!email.trim() || !password) {
            setError('Please fill in all fields');
            return;
        }
        setError('');
        setLoading(true);

        // Cold start warning
        const timeout = setTimeout(() => {
            setError('Connection is taking longer than usual. The server might be waking up (Cold Start). Please wait...');
        }, 5000);

        try {
            const result = await signIn(email.trim(), password);
            clearTimeout(timeout);
            // Role-based redirect is handled by AuthContext -> AppNavigator
        } catch (err) {
            clearTimeout(timeout);
            setError(err.message || 'Failed to sign in');
        } finally {
            setLoading(false);
        }
    };

    const handleGoogleSignIn = async () => {
        try {
            setLoading(true);
            await signInWithGoogle();
        } catch (err) {
            setError(err.message || 'Failed to sign in with Google');
            setLoading(false);
        }
    };

    return (
        <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
            <ScrollView
                contentContainerStyle={[styles.container]}
                style={{ backgroundColor: theme.backgroundGradientFrom || '#FDF2F8' }}
                keyboardShouldPersistTaps="handled"
            >
                {/* Header — matches website */}
                <View style={styles.header}>
                    <Text style={[styles.brandTitle, { color: theme.primary }]}>🤰 Aanchal AI</Text>
                    <Text style={[styles.welcomeTitle, { color: theme.text }]}>Welcome Back</Text>
                    <Text style={[styles.subtitle, { color: theme.textSecondary }]}>Sign in to your account</Text>
                </View>

                {/* Error */}
                {error !== '' && (
                    <View style={[styles.errorBox, { backgroundColor: theme.errorLight, borderColor: '#FECACA' }]}>
                        <Text style={[styles.errorText, { color: '#B91C1C' }]}>{error}</Text>
                    </View>
                )}

                {/* Form Card — matches website white card */}
                <View style={[styles.formCard, { backgroundColor: theme.surface }]}>
                    {/* Email */}
                    <View style={styles.field}>
                        <Text style={[styles.label, { color: theme.textSecondary }]}>Email Address</Text>
                        <TextInput
                            style={[styles.input, { color: theme.text, borderColor: theme.border }]}
                            placeholder="your@email.com"
                            placeholderTextColor={theme.placeholder}
                            value={email}
                            onChangeText={(v) => { setEmail(v); setError(''); }}
                            keyboardType="email-address"
                            autoCapitalize="none"
                            autoCorrect={false}
                        />
                    </View>

                    {/* Password */}
                    <View style={styles.field}>
                        <Text style={[styles.label, { color: theme.textSecondary }]}>Password</Text>
                        <TextInput
                            style={[styles.input, { color: theme.text, borderColor: theme.border }]}
                            placeholder="••••••••"
                            placeholderTextColor={theme.placeholder}
                            value={password}
                            onChangeText={(v) => { setPassword(v); setError(''); }}
                            secureTextEntry
                        />
                    </View>

                    {/* Forgot */}
                    <TouchableOpacity style={styles.forgotRow}>
                        <Text style={[styles.forgotText, { color: theme.primary }]}>Forgot your password?</Text>
                    </TouchableOpacity>

                    {/* Sign In Button — purple */}
                    <TouchableOpacity
                        style={[styles.primaryBtn, { backgroundColor: theme.primary, opacity: loading ? 0.5 : 1 }]}
                        onPress={handleSubmit}
                        disabled={loading}
                    >
                        <Text style={styles.primaryBtnText}>{loading ? 'Signing in...' : 'Sign In'}</Text>
                    </TouchableOpacity>

                    {/* Divider */}
                    <View style={styles.divider}>
                        <View style={[styles.dividerLine, { backgroundColor: theme.border }]} />
                        <Text style={[styles.dividerText, { color: theme.placeholder, backgroundColor: theme.surface }]}>
                            Or continue with
                        </Text>
                        <View style={[styles.dividerLine, { backgroundColor: theme.border }]} />
                    </View>

                    {/* Google Button */}
                    <TouchableOpacity
                        style={[styles.googleBtn, { borderColor: theme.border }]}
                        onPress={handleGoogleSignIn}
                        disabled={loading}
                    >
                        <Ionicons name="logo-google" size={18} color="#4285F4" />
                        <Text style={[styles.googleBtnText, { color: theme.textSecondary }]}>Sign in with Google</Text>
                    </TouchableOpacity>

                    {/* Sign Up Link */}
                    <View style={styles.signupRow}>
                        <Text style={[styles.signupText, { color: theme.textSecondary }]}>Don't have an account? </Text>
                        <TouchableOpacity onPress={() => navigation.navigate('Signup')}>
                            <Text style={[styles.signupLink, { color: theme.primary }]}>Sign up</Text>
                        </TouchableOpacity>
                    </View>
                </View>
            </ScrollView>
        </KeyboardAvoidingView>
    );
}

const styles = StyleSheet.create({
    container: { flexGrow: 1, justifyContent: 'center', paddingHorizontal: spacing.screenPadding, paddingVertical: 40 },
    header: { alignItems: 'center', marginBottom: 24 },
    brandTitle: { fontSize: 28, fontWeight: '700', marginBottom: 8 },
    welcomeTitle: { fontSize: 22, fontWeight: '700' },
    subtitle: { fontSize: 14, marginTop: 4 },
    errorBox: { borderWidth: 1, borderRadius: 10, padding: 12, marginBottom: 16 },
    errorText: { fontSize: 13 },
    formCard: {
        borderRadius: 14, padding: 24,
        shadowColor: '#000', shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.1, shadowRadius: 16, elevation: 6,
    },
    field: { marginBottom: 16 },
    label: { fontSize: 13, fontWeight: '500', marginBottom: 6 },
    input: {
        borderWidth: 1, borderRadius: 10, paddingHorizontal: 14, paddingVertical: 10,
        fontSize: 15,
    },
    forgotRow: { alignSelf: 'flex-start', marginBottom: 16 },
    forgotText: { fontSize: 13, fontWeight: '500' },
    primaryBtn: {
        paddingVertical: 14, borderRadius: 10, alignItems: 'center',
    },
    primaryBtnText: { color: '#fff', fontSize: 15, fontWeight: '600' },
    divider: { flexDirection: 'row', alignItems: 'center', marginVertical: 20 },
    dividerLine: { flex: 1, height: 1 },
    dividerText: { paddingHorizontal: 10, fontSize: 13 },
    googleBtn: {
        flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
        borderWidth: 1, borderRadius: 10, paddingVertical: 12, gap: 10,
        shadowColor: '#000', shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.04, shadowRadius: 2, elevation: 1,
    },
    googleBtnText: { fontSize: 14, fontWeight: '500' },
    signupRow: { flexDirection: 'row', justifyContent: 'center', marginTop: 16 },
    signupText: { fontSize: 13 },
    signupLink: { fontSize: 13, fontWeight: '600' },
});
