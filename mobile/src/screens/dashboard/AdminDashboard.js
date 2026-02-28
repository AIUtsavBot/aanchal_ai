// Admin Dashboard Screen
import React, { useState, useEffect, useCallback } from 'react';
import {
    View, Text, ScrollView, TouchableOpacity, RefreshControl, StyleSheet, FlatList,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../contexts/ThemeContext';
import { typography, spacing, borderRadius } from '../../theme';
import { adminAPI, authAPI } from '../../services/api';
import { StatCard, PatientCard, EmptyState, LoadingSpinner, SectionHeader } from '../../components/shared';

export default function AdminDashboardScreen({ navigation }) {
    const { t } = useTranslation();
    const { theme } = useTheme();
    const [tab, setTab] = useState('overview'); // overview | analytics | mothers | children | users
    const [stats, setStats] = useState(null);
    const [metrics, setMetrics] = useState(null);
    const [mothers, setMothers] = useState([]);
    const [children, setChildren] = useState([]);
    const [refreshing, setRefreshing] = useState(false);
    const [loading, setLoading] = useState(true);

    const loadData = useCallback(async () => {
        try {
            const [motherStats, childStats, userStats] = await Promise.all([
                adminAPI.getMotherStats().catch(() => ({})),
                adminAPI.getChildrenStats().catch(() => ({})),
                adminAPI.getUserStats().catch(() => ({})),
            ]);
            setStats({ ...motherStats, ...childStats, ...userStats });
        } catch (e) {
            console.error('Load admin data error:', e);
        } finally {
            setLoading(false);
        }
    }, []);

    const loadMothers = async () => {
        try { setMothers(await adminAPI.getAllMothers()); } catch { }
    };

    const loadChildren = async () => {
        try { setChildren(await adminAPI.getAllChildren()); } catch { }
    };

    const loadMetrics = async () => {
        try {
            const res = await adminAPI.getMetrics();
            if (res?.metrics) setMetrics(res.metrics);
        } catch { }
    };

    useEffect(() => { loadData(); }, []);

    useEffect(() => {
        if (tab === 'mothers' && !mothers.length) loadMothers();
        if (tab === 'children' && !children.length) loadChildren();
        if (tab === 'analytics' && !metrics) loadMetrics();
    }, [tab]);

    const onRefresh = async () => {
        setRefreshing(true);
        await loadData();
        if (tab === 'mothers') await loadMothers();
        if (tab === 'children') await loadChildren();
        if (tab === 'analytics') await loadMetrics();
        setRefreshing(false);
    };

    if (loading) return <LoadingSpinner />;

    const tabs = [
        { key: 'overview', label: 'Overview', icon: 'grid-outline' },
        { key: 'analytics', label: 'Analytics', icon: 'analytics-outline' },
        { key: 'mothers', label: t('mothers'), icon: 'heart-outline' },
        { key: 'children', label: t('children'), icon: 'happy-outline' },
        { key: 'users', label: 'Users', icon: 'people-outline' },
    ];

    return (
        <View style={[styles.container, { backgroundColor: theme.background }]}>
            {/* Header */}
            <View style={[styles.header, { backgroundColor: theme.primary }]}>
                <Text style={styles.headerTitle}>{t('admin_dashboard')}</Text>
                <TouchableOpacity onPress={() => navigation.navigate('AdminApprovals')}>
                    <View style={styles.approvalBadge}>
                        <Ionicons name="checkmark-circle-outline" size={22} color="#fff" />
                        <Text style={styles.approvalText}>{t('approvals')}</Text>
                    </View>
                </TouchableOpacity>
            </View>

            {/* Tab Bar */}
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={[styles.tabBar, { backgroundColor: theme.surface }]}>
                {tabs.map((tb) => (
                    <TouchableOpacity
                        key={tb.key}
                        style={[styles.tab, tab === tb.key && { borderBottomColor: theme.primary, borderBottomWidth: 2 }]}
                        onPress={() => setTab(tb.key)}
                    >
                        <Ionicons name={tb.icon} size={18} color={tab === tb.key ? theme.primary : theme.textTertiary} />
                        <Text style={[typography.smallBold, { color: tab === tb.key ? theme.primary : theme.textTertiary, marginLeft: 4 }]}>
                            {tb.label}
                        </Text>
                    </TouchableOpacity>
                ))}
            </ScrollView>

            <ScrollView
                refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.primary} />}
                contentContainerStyle={styles.content}
            >
                {tab === 'overview' && (
                    <>
                        <View style={styles.statsRow}>
                            <StatCard icon="heart" label={t('total_mothers')} value={stats?.total_mothers || 0} color={theme.primary} />
                            <StatCard icon="warning" label={t('high_risk')} value={stats?.high_risk || 0} color={theme.error} />
                        </View>
                        <View style={styles.statsRow}>
                            <StatCard icon="happy" label={t('children')} value={stats?.total_children || 0} color={theme.info} />
                            <StatCard icon="people" label="Users" value={stats?.total_users || 0} color={theme.accent} />
                        </View>
                    </>
                )}

                {tab === 'mothers' && (
                    mothers.length > 0
                        ? mothers.map((m, i) => <PatientCard key={m.id || i} patient={m} />)
                        : <EmptyState icon="heart-outline" title={t('no_data')} message="No mothers registered yet" />
                )}

                {tab === 'children' && (
                    children.length > 0
                        ? children.map((c, i) => (
                            <View key={c.id || i} style={[styles.childCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                                <Ionicons name="happy-outline" size={24} color={theme.primary} />
                                <View style={{ marginLeft: spacing.md, flex: 1 }}>
                                    <Text style={[typography.bodyBold, { color: theme.text }]}>{c.name || 'Child'}</Text>
                                    <Text style={[typography.caption, { color: theme.textSecondary }]}>
                                        {c.date_of_birth ? `DOB: ${c.date_of_birth}` : ''}
                                    </Text>
                                </View>
                            </View>
                        ))
                        : <EmptyState icon="happy-outline" title={t('no_data')} message="No children registered yet" />
                )}

                {tab === 'users' && (
                    <View>
                        <View style={[styles.userRow, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                            <Ionicons name="medkit" size={24} color={theme.primary} />
                            <Text style={[typography.body, { color: theme.text, flex: 1, marginLeft: spacing.md }]}>Doctors</Text>
                            <Text style={[typography.h4, { color: theme.primary }]}>{stats?.doctors || 0}</Text>
                        </View>
                        <View style={[styles.userRow, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                            <Ionicons name="people" size={24} color={theme.accent} />
                            <Text style={[typography.body, { color: theme.text, flex: 1, marginLeft: spacing.md }]}>ASHA Workers</Text>
                            <Text style={[typography.h4, { color: theme.accent }]}>{stats?.asha_workers || 0}</Text>
                        </View>
                    </View>
                )}

                {tab === 'analytics' && (
                    <View>
                        <SectionHeader title="📈 AI Token Usage" />
                        <View style={styles.statsRow}>
                            <StatCard icon="flash" label="Total Tokens" value={metrics?.token_usage_estimated?.toLocaleString() || '—'} color={theme.primary} />
                            <StatCard icon="card" label="Est. Cost (USD)" value={metrics?.cost_usd_estimated != null ? `$${metrics.cost_usd_estimated}` : '—'} color={theme.accent} />
                        </View>
                        <View style={styles.statsRow}>
                            <StatCard icon="cube" label="AI Calls" value={metrics?.ai_calls_total?.toLocaleString() || '—'} color={theme.info} />
                        </View>

                        <SectionHeader title="🗣️ Risk Topics Word Cloud" />
                        <View style={[styles.wordCloud, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                            {Array.isArray(metrics?.word_cloud) && metrics.word_cloud.length > 0 ? (
                                metrics.word_cloud.map((w, idx) => {
                                    const maxVal = Math.max(...metrics.word_cloud.map(x => x.value));
                                    const size = Math.max(12, Math.min(28, (w.value / maxVal) * 28));
                                    return (
                                        <Text
                                            key={`${w.text}-${idx}`}
                                            style={{
                                                fontSize: size,
                                                fontWeight: size > 18 ? '700' : '400',
                                                color: theme.primary,
                                                opacity: 0.5 + (w.value / maxVal) * 0.5,
                                                margin: 4,
                                            }}
                                        >
                                            {w.text}
                                        </Text>
                                    );
                                })
                            ) : (
                                <Text style={[typography.body, { color: theme.textTertiary }]}>No word data available</Text>
                            )}
                        </View>
                    </View>
                )}
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1 },
    header: {
        paddingTop: 54, paddingBottom: 16, paddingHorizontal: spacing.screenPadding,
        flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    },
    headerTitle: { color: '#fff', fontSize: 22, fontWeight: '700' },
    approvalBadge: { flexDirection: 'row', alignItems: 'center', backgroundColor: 'rgba(255,255,255,0.2)', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20, gap: 4 },
    approvalText: { color: '#fff', fontSize: 13, fontWeight: '600' },
    tabBar: { maxHeight: 50, borderBottomWidth: 1, borderBottomColor: '#eee' },
    tab: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingVertical: 12 },
    content: { padding: spacing.screenPadding, paddingBottom: 100 },
    statsRow: { flexDirection: 'row', marginBottom: spacing.md },
    childCard: {
        flexDirection: 'row', alignItems: 'center', padding: spacing.base,
        borderRadius: borderRadius.lg, borderWidth: 1, marginBottom: spacing.md,
    },
    userRow: {
        flexDirection: 'row', alignItems: 'center', padding: spacing.base,
        borderRadius: borderRadius.lg, borderWidth: 1, marginBottom: spacing.md,
    },
    wordCloud: {
        flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'center',
        padding: spacing.base, borderRadius: borderRadius.lg, borderWidth: 1, marginBottom: spacing.md,
        minHeight: 150,
    },
});
