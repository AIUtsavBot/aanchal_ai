// ASHA Worker Interface
import React, { useState, useEffect, useCallback } from 'react';
import {
    View, Text, ScrollView, TouchableOpacity, StyleSheet, RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../contexts/ThemeContext';
import { useView } from '../../contexts/ViewContext';
import { useAuth } from '../../contexts/AuthContext';
import { supabase } from '../../services/auth';
import { typography, spacing, borderRadius } from '../../theme';
import { motherAPI } from '../../services/api';
import { PatientCard, StatCard, EmptyState, LoadingSpinner } from '../../components/shared';

export default function ASHAInterfaceScreen({ navigation }) {
    const { t } = useTranslation();
    const { theme } = useTheme();
    const { currentView, setCurrentView } = useView();
    const { user } = useAuth();
    const [mothers, setMothers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    const loadData = useCallback(async () => {
        try {
            if (!user?.id) return;
            const { data: ashaData, error: ashaError } = await supabase
                .from('asha_workers')
                .select('*')
                .eq('user_profile_id', user.id)
                .limit(1);

            const ashaInfo = ashaData?.[0];

            if (ashaError || !ashaInfo) {
                console.error('ASHA load error:', ashaError || 'No ASHA record found');
                return;
            }

            const { data: mothersData, error: mothersError } = await supabase
                .from('mothers')
                .select('*')
                .eq('asha_worker_id', ashaInfo.id);

            if (!mothersError && mothersData) {
                setMothers(mothersData);
            }
        } catch (e) {
            console.warn('ASHA loadData error:', e);
        } finally { setLoading(false); }
    }, [user?.id]);

    useEffect(() => { loadData(); }, []);

    const onRefresh = async () => { setRefreshing(true); await loadData(); setRefreshing(false); };

    if (loading) return <LoadingSpinner />;

    const highRisk = mothers.filter((m) => m.risk_level === 'HIGH').length;
    const delivered = mothers.filter((m) => m.status === 'postnatal').length;

    return (
        <View style={[styles.container, { backgroundColor: theme.background }]}>
            <View style={[styles.header, { backgroundColor: theme.primary }]}>
                <Text style={styles.headerTitle}>{t('asha_dashboard')}</Text>
                {/* View Toggle */}
                <View style={styles.toggle}>
                    {['matruraksha', 'santanraksha'].map((v) => (
                        <TouchableOpacity
                            key={v}
                            style={[styles.toggleBtn, currentView === v && styles.toggleActive]}
                            onPress={() => setCurrentView(v)}
                        >
                            <Text style={[styles.toggleText, currentView === v && styles.toggleTextActive]}>
                                {v === 'matruraksha' ? '🤰' : '👶'} {t(v)}
                            </Text>
                        </TouchableOpacity>
                    ))}
                </View>
            </View>

            <ScrollView
                refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.primary} />}
                contentContainerStyle={styles.content}
            >
                {/* Stats */}
                <View style={styles.statsRow}>
                    <StatCard icon="heart" label={t('total_mothers')} value={mothers.length} color={theme.primary} />
                    <StatCard icon="warning" label={t('high_risk')} value={highRisk} color={theme.error} />
                </View>

                {/* Quick Actions */}
                <Text style={[typography.h4, { color: theme.text, marginBottom: spacing.md }]}>Quick Actions</Text>
                <View style={styles.actionsGrid}>
                    {[
                        { icon: 'calendar-outline', label: t('vaccination_calendar'), screen: 'VaccinationCalendar', color: theme.info },
                        { icon: 'trending-up-outline', label: t('growth_charts'), screen: 'GrowthCharts', color: theme.success },
                        { icon: 'fitness-outline', label: t('milestones'), screen: 'MilestonesTracker', color: theme.accent },
                        { icon: 'clipboard-outline', label: t('assessments'), screen: 'PostnatalAssessments', color: theme.primary },
                    ].map((a, i) => (
                        <TouchableOpacity
                            key={i}
                            style={[styles.actionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
                            onPress={() => navigation.navigate(a.screen)}
                            activeOpacity={0.7}
                        >
                            <View style={[styles.actionIcon, { backgroundColor: a.color + '15' }]}>
                                <Ionicons name={a.icon} size={24} color={a.color} />
                            </View>
                            <Text style={[typography.captionBold, { color: theme.text, marginTop: spacing.sm, textAlign: 'center' }]}>
                                {a.label}
                            </Text>
                        </TouchableOpacity>
                    ))}
                </View>

                {/* Mothers List */}
                <Text style={[typography.h4, { color: theme.text, marginTop: spacing.xl, marginBottom: spacing.md }]}>
                    Assigned Mothers
                </Text>
                {mothers.length > 0
                    ? mothers.map((m, i) => <PatientCard key={m.id || i} patient={m} />)
                    : <EmptyState icon="people-outline" title={t('no_assigned_mothers')} />
                }
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1 },
    header: { paddingTop: 54, paddingBottom: 16, paddingHorizontal: spacing.screenPadding },
    headerTitle: { color: '#fff', fontSize: 22, fontWeight: '700' },
    toggle: {
        flexDirection: 'row', marginTop: spacing.md,
        backgroundColor: 'rgba(255,255,255,0.2)', borderRadius: 12, padding: 3,
    },
    toggleBtn: { flex: 1, paddingVertical: 8, alignItems: 'center', borderRadius: 10 },
    toggleActive: { backgroundColor: '#fff' },
    toggleText: { color: 'rgba(255,255,255,0.9)', fontWeight: '600', fontSize: 13 },
    toggleTextActive: { color: '#0D9488' },
    content: { padding: spacing.screenPadding, paddingBottom: 100 },
    statsRow: { flexDirection: 'row', marginBottom: spacing.xl },
    actionsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
    actionCard: {
        width: '47%', padding: spacing.base, borderRadius: borderRadius.lg,
        alignItems: 'center', borderWidth: 1,
    },
    actionIcon: { width: 48, height: 48, borderRadius: 24, justifyContent: 'center', alignItems: 'center' },
});
