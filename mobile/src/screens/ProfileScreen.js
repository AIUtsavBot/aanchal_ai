// Profile Screen
import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Alert, Switch, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import { typography, spacing, borderRadius } from '../theme';
import i18n from '../i18n';

export default function ProfileScreen() {
    const { t } = useTranslation();
    const { theme, isDark, toggleTheme } = useTheme();
    const { user, signOut } = useAuth();
    const [lang, setLang] = useState(i18n.language);

    const changeLanguage = (code) => {
        i18n.changeLanguage(code);
        setLang(code);
    };

    const handleSignOut = () => {
        if (Platform.OS === 'web') {
            // Alert.alert doesn't work on web - use window.confirm instead
            const confirmed = window.confirm('Are you sure you want to sign out?');
            if (confirmed) signOut();
        } else {
            Alert.alert(t('logout'), 'Are you sure you want to sign out?', [
                { text: t('cancel'), style: 'cancel' },
                { text: t('logout'), style: 'destructive', onPress: signOut },
            ]);
        }
    };

    const roleLabel = {
        ADMIN: 'Administrator',
        DOCTOR: 'Doctor',
        ASHA_WORKER: 'ASHA Worker',
    };

    return (
        <ScrollView style={[styles.container, { backgroundColor: theme.background }]}>
            {/* Header */}
            <View style={[styles.header, { backgroundColor: theme.primary }]}>
                <View style={styles.avatarCircle}>
                    <Text style={styles.avatarText}>
                        {user?.fullName?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || '?'}
                    </Text>
                </View>
                <Text style={styles.name}>{user?.fullName || 'User'}</Text>
                <Text style={styles.email}>{user?.email || ''}</Text>
                {user?.role && (
                    <View style={styles.roleBadge}>
                        <Text style={styles.roleText}>{roleLabel[user.role] || user.role}</Text>
                    </View>
                )}
            </View>

            <View style={styles.content}>
                {/* Account Info */}
                <Text style={[typography.h4, { color: theme.text, marginBottom: spacing.md }]}>Account</Text>
                {[
                    { icon: 'person-outline', label: 'Name', value: user?.fullName || '—' },
                    { icon: 'mail-outline', label: 'Email', value: user?.email || '—' },
                    { icon: 'call-outline', label: 'Phone', value: user?.phone || '—' },
                    { icon: 'location-outline', label: 'Area', value: user?.assignedArea || '—' },
                ].map((item, i) => (
                    <View key={i} style={[styles.infoRow, { borderBottomColor: theme.divider }]}>
                        <Ionicons name={item.icon} size={20} color={theme.textTertiary} />
                        <Text style={[typography.small, { color: theme.textSecondary, marginLeft: spacing.md, width: 60 }]}>{item.label}</Text>
                        <Text style={[typography.small, { color: theme.text, flex: 1 }]}>{item.value}</Text>
                    </View>
                ))}

                {/* Settings */}
                <Text style={[typography.h4, { color: theme.text, marginTop: spacing.xxl, marginBottom: spacing.md }]}>Settings</Text>

                {/* Dark Mode */}
                <View style={[styles.settingRow, { borderBottomColor: theme.divider }]}>
                    <Ionicons name={isDark ? 'moon' : 'sunny-outline'} size={20} color={theme.textTertiary} />
                    <Text style={[typography.body, { color: theme.text, flex: 1, marginLeft: spacing.md }]}>Dark Mode</Text>
                    <Switch
                        value={isDark}
                        onValueChange={toggleTheme}
                        trackColor={{ false: theme.border, true: theme.primary }}
                        thumbColor="#fff"
                    />
                </View>

                {/* Language */}
                <Text style={[typography.smallBold, { color: theme.text, marginTop: spacing.lg, marginBottom: spacing.sm }]}>
                    {t('language')}
                </Text>
                <View style={styles.langRow}>
                    {[
                        { code: 'en', label: 'English', flag: '🇬🇧' },
                        { code: 'hi', label: 'हिन्दी', flag: '🇮🇳' },
                        { code: 'mr', label: 'मराठी', flag: '🇮🇳' },
                    ].map((l) => (
                        <TouchableOpacity
                            key={l.code}
                            style={[styles.langBtn, { borderColor: lang === l.code ? theme.primary : theme.border }, lang === l.code && { backgroundColor: theme.primary + '10' }]}
                            onPress={() => changeLanguage(l.code)}
                        >
                            <Text style={{ fontSize: 18 }}>{l.flag}</Text>
                            <Text style={[typography.captionBold, { color: lang === l.code ? theme.primary : theme.text, marginTop: 2 }]}>
                                {l.label}
                            </Text>
                        </TouchableOpacity>
                    ))}
                </View>

                {/* Sign Out */}
                <TouchableOpacity style={[styles.signOutBtn, { borderColor: theme.error }]} onPress={handleSignOut}>
                    <Ionicons name="log-out-outline" size={20} color={theme.error} />
                    <Text style={[typography.buttonSmall, { color: theme.error, marginLeft: spacing.sm }]}>{t('logout')}</Text>
                </TouchableOpacity>

                <Text style={[typography.caption, { color: theme.textTertiary, textAlign: 'center', marginTop: spacing.xl }]}>
                    Aanchal AI v1.2.0{'\n'}Powered by Google Gemini 2.0 Flash
                </Text>
            </View>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1 },
    header: { paddingTop: 54, paddingBottom: 24, alignItems: 'center' },
    avatarCircle: { width: 72, height: 72, borderRadius: 36, backgroundColor: 'rgba(255,255,255,0.25)', justifyContent: 'center', alignItems: 'center' },
    avatarText: { fontSize: 28, fontWeight: '700', color: '#fff' },
    name: { color: '#fff', fontSize: 20, fontWeight: '700', marginTop: 10 },
    email: { color: 'rgba(255,255,255,0.8)', fontSize: 14, marginTop: 2 },
    roleBadge: { backgroundColor: 'rgba(255,255,255,0.2)', paddingHorizontal: 14, paddingVertical: 4, borderRadius: 12, marginTop: 8 },
    roleText: { color: '#fff', fontWeight: '600', fontSize: 12 },
    content: { padding: spacing.screenPadding, paddingBottom: 100 },
    infoRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 12, borderBottomWidth: 1 },
    settingRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 12, borderBottomWidth: 1 },
    langRow: { flexDirection: 'row', gap: 10 },
    langBtn: { flex: 1, alignItems: 'center', paddingVertical: 12, borderRadius: borderRadius.md, borderWidth: 1.5 },
    signOutBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 14, borderRadius: borderRadius.md, borderWidth: 1.5, marginTop: spacing.xxl },
});
