// Shared Components
import React from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { typography, spacing, borderRadius } from '../theme';

// --- Loading Spinner ---
export const LoadingSpinner = ({ message = 'Loading...', size = 'large' }) => {
    const { theme } = useTheme();
    return (
        <View style={[styles.center, { backgroundColor: theme.background }]}>
            <ActivityIndicator size={size} color={theme.primary} />
            <Text style={[typography.small, { color: theme.textSecondary, marginTop: spacing.md }]}>
                {message}
            </Text>
        </View>
    );
};

// --- Risk Badge ---
export const RiskBadge = ({ level }) => {
    const { theme } = useTheme();
    const config = {
        HIGH: { bg: theme.errorLight, color: theme.error, label: 'High' },
        MODERATE: { bg: theme.warningLight, color: theme.warning, label: 'Moderate' },
        LOW: { bg: theme.successLight, color: theme.success, label: 'Low' },
    };
    const c = config[level?.toUpperCase()] || config.LOW;
    return (
        <View style={[styles.badge, { backgroundColor: c.bg }]}>
            <View style={[styles.badgeDot, { backgroundColor: c.color }]} />
            <Text style={[typography.captionBold, { color: c.color }]}>{c.label}</Text>
        </View>
    );
};

// --- Patient Card ---
export const PatientCard = ({ patient, onPress }) => {
    const { theme } = useTheme();
    return (
        <TouchableOpacity
            style={[styles.card, { backgroundColor: theme.surface, shadowColor: theme.cardShadow, borderColor: theme.border }]}
            onPress={onPress}
            activeOpacity={0.7}
        >
            <View style={styles.cardHeader}>
                <View style={[styles.avatar, { backgroundColor: theme.primaryLight + '30' }]}>
                    <Text style={[typography.h4, { color: theme.primary }]}>
                        {(patient?.name || patient?.full_name)?.[0] || '?'}
                    </Text>
                </View>
                <View style={{ flex: 1, marginLeft: spacing.md }}>
                    <Text style={[typography.bodyBold, { color: theme.text }]} numberOfLines={1}>
                        {patient?.name || patient?.full_name || 'Unknown'}
                    </Text>
                    <Text style={[typography.caption, { color: theme.textSecondary }]}>
                        {patient?.age ? `${patient.age} yrs` : ''} {patient?.location ? `• ${patient.location}` : ''}
                    </Text>
                </View>
                {patient?.risk_level && <RiskBadge level={patient.risk_level} />}
            </View>
            {patient?.phone && (
                <View style={styles.cardPhone}>
                    <Ionicons name="call-outline" size={14} color={theme.textTertiary} />
                    <Text style={[typography.caption, { color: theme.textTertiary, marginLeft: 4 }]}>
                        {patient.phone}
                    </Text>
                </View>
            )}
        </TouchableOpacity>
    );
};

// --- Stat Card ---
export const StatCard = ({ icon, label, value, color, onPress }) => {
    const { theme } = useTheme();
    return (
        <TouchableOpacity
            style={[styles.statCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
            onPress={onPress}
            activeOpacity={onPress ? 0.7 : 1}
        >
            <View style={[styles.statIcon, { backgroundColor: (color || theme.primary) + '18' }]}>
                <Ionicons name={icon} size={22} color={color || theme.primary} />
            </View>
            <Text style={[typography.h3, { color: theme.text, marginTop: spacing.sm }]}>{value}</Text>
            <Text style={[typography.caption, { color: theme.textSecondary, marginTop: 2 }]}>{label}</Text>
        </TouchableOpacity>
    );
};

// --- Section Header ---
export const SectionHeader = ({ title, actionLabel, onAction }) => {
    const { theme } = useTheme();
    return (
        <View style={styles.sectionHeader}>
            <Text style={[typography.h4, { color: theme.text }]}>{title}</Text>
            {actionLabel && (
                <TouchableOpacity onPress={onAction}>
                    <Text style={[typography.smallBold, { color: theme.primary }]}>{actionLabel}</Text>
                </TouchableOpacity>
            )}
        </View>
    );
};

// --- Button ---
export const Button = ({ title, onPress, variant = 'primary', icon, loading, disabled, style }) => {
    const { theme } = useTheme();
    const isPrimary = variant === 'primary';
    const isDanger = variant === 'danger';
    const bgColor = isPrimary ? theme.primary : isDanger ? theme.error : 'transparent';
    const textColor = isPrimary || isDanger ? '#FFFFFF' : theme.primary;
    const borderColor = isPrimary || isDanger ? 'transparent' : theme.primary;

    return (
        <TouchableOpacity
            style={[
                styles.button,
                { backgroundColor: bgColor, borderColor, opacity: disabled ? 0.5 : 1 },
                style,
            ]}
            onPress={onPress}
            disabled={disabled || loading}
            activeOpacity={0.7}
        >
            {loading ? (
                <ActivityIndicator size="small" color={textColor} />
            ) : (
                <>
                    {icon && <Ionicons name={icon} size={18} color={textColor} style={{ marginRight: 6 }} />}
                    <Text style={[typography.button, { color: textColor }]}>{title}</Text>
                </>
            )}
        </TouchableOpacity>
    );
};

// --- Input ---
export const Input = ({ label, value, onChangeText, placeholder, keyboardType, secureTextEntry, multiline, error }) => {
    const { theme } = useTheme();
    return (
        <View style={{ marginBottom: spacing.base }}>
            {label && (
                <Text style={[typography.smallBold, { color: theme.text, marginBottom: spacing.xs }]}>
                    {label}
                </Text>
            )}
            <View
                style={[
                    styles.input,
                    {
                        backgroundColor: theme.surfaceElevated,
                        borderColor: error ? theme.error : theme.border,
                    },
                    multiline && { height: 100, textAlignVertical: 'top' },
                ]}
            >
                <Text
                    style={[typography.body, { color: theme.text, flex: 1 }]}
                // We use a TextInput component below, but styled Text placeholder for structure
                />
            </View>
            {error && <Text style={[typography.caption, { color: theme.error, marginTop: 2 }]}>{error}</Text>}
        </View>
    );
};

// --- Empty State ---
export const EmptyState = ({ icon = 'folder-open-outline', title, message }) => {
    const { theme } = useTheme();
    return (
        <View style={[styles.center, { paddingVertical: spacing.xxxl }]}>
            <Ionicons name={icon} size={48} color={theme.textTertiary} />
            <Text style={[typography.h4, { color: theme.textSecondary, marginTop: spacing.base }]}>{title}</Text>
            {message && (
                <Text style={[typography.small, { color: theme.textTertiary, marginTop: spacing.xs, textAlign: 'center' }]}>
                    {message}
                </Text>
            )}
        </View>
    );
};

const styles = StyleSheet.create({
    center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
    badge: {
        flexDirection: 'row', alignItems: 'center',
        paddingHorizontal: 10, paddingVertical: 4,
        borderRadius: borderRadius.full,
    },
    badgeDot: { width: 6, height: 6, borderRadius: 3, marginRight: 5 },
    card: {
        padding: spacing.cardPadding, borderRadius: borderRadius.lg,
        marginBottom: spacing.md, borderWidth: 1,
        shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.08, shadowRadius: 8,
        elevation: 2,
    },
    cardHeader: { flexDirection: 'row', alignItems: 'center' },
    avatar: {
        width: 42, height: 42, borderRadius: 21,
        justifyContent: 'center', alignItems: 'center',
    },
    cardPhone: { flexDirection: 'row', alignItems: 'center', marginTop: spacing.sm, marginLeft: 54 },
    statCard: {
        flex: 1, padding: spacing.base, borderRadius: borderRadius.lg,
        borderWidth: 1, marginHorizontal: spacing.xs,
        alignItems: 'center',
    },
    statIcon: {
        width: 42, height: 42, borderRadius: 21,
        justifyContent: 'center', alignItems: 'center',
    },
    sectionHeader: {
        flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
        paddingHorizontal: spacing.screenPadding, paddingVertical: spacing.md,
    },
    button: {
        flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
        paddingVertical: 14, paddingHorizontal: spacing.xl,
        borderRadius: borderRadius.md, borderWidth: 1.5,
    },
    input: {
        paddingHorizontal: spacing.base, paddingVertical: 12,
        borderRadius: borderRadius.md, borderWidth: 1,
        flexDirection: 'row', alignItems: 'center',
    },
});
