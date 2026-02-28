// Mother Registry Screen - Shows all registered mothers (like ChildrenList)
import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, RefreshControl } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../contexts/AuthContext';
import { supabase } from '../../services/auth';
import { useTheme } from '../../contexts/ThemeContext';
import { typography, spacing, borderRadius } from '../../theme';
import { EmptyState, LoadingSpinner } from '../../components/shared';

export default function MothersListScreen({ navigation }) {
    const { user } = useAuth();
    const { theme } = useTheme();
    const [mothers, setMothers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [expandedMother, setExpandedMother] = useState(null);

    const loadData = async (retryCount = 0) => {
        try {
            if (!user?.id) return;

            // Delay on first load to avoid GoTrue lock conflicts
            if (retryCount === 0) await new Promise(r => setTimeout(r, 300));

            let query = supabase.from('mothers').select('*').eq('status', 'postnatal');

            // Filter by role-specific ID
            if (user.role === 'ASHA_WORKER') {
                const { data: asha, error: ashaErr } = await supabase.from('asha_workers').select('id').eq('user_profile_id', user.id).limit(1);
                if (ashaErr) {
                    if (retryCount < 3 && (ashaErr.message?.includes('AbortError') || ashaErr.message?.includes('Lock broken'))) {
                        await new Promise(r => setTimeout(r, 1000));
                        return loadData(retryCount + 1);
                    }
                    console.error('ASHA lookup error:', ashaErr);
                    return;
                }
                if (asha && asha.length > 0) {
                    query = query.eq('asha_worker_id', asha[0].id);
                } else {
                    console.warn('No ASHA worker record for user:', user.id);
                }
            } else if (user.role === 'DOCTOR') {
                const { data: docs, error: docErr } = await supabase.from('doctors').select('id').eq('user_profile_id', user.id).limit(1);
                if (docErr) {
                    if (retryCount < 3 && (docErr.message?.includes('AbortError') || docErr.message?.includes('Lock broken'))) {
                        await new Promise(r => setTimeout(r, 1000));
                        return loadData(retryCount + 1);
                    }
                    console.error('Doctor lookup error:', docErr);
                    return;
                }
                const doc = docs?.[0];
                if (doc) {
                    query = query.eq('doctor_id', doc.id);
                } else {
                    console.warn('No doctor record for user:', user.id);
                }
            }
            // ADMIN role: no filter, sees all mothers

            const { data, error } = await query.order('name');
            if (error) {
                if (retryCount < 3 && (error.message?.includes('AbortError') || error.message?.includes('Lock broken'))) {
                    await new Promise(r => setTimeout(r, 1000));
                    return loadData(retryCount + 1);
                }
                console.error('Mothers query error:', error);
            }
            if (data) setMothers(data);
        } catch (e) {
            if (retryCount < 3 && (e.message?.includes('AbortError') || e.name === 'AbortError')) {
                await new Promise(r => setTimeout(r, 1000));
                return loadData(retryCount + 1);
            }
            console.error('MothersList loadData error:', e);
        } finally { setLoading(false); }
    };

    useEffect(() => { loadData(); }, []);
    const onRefresh = async () => { setRefreshing(true); await loadData(); setRefreshing(false); };

    if (loading) return <LoadingSpinner />;

    return (
        <ScrollView
            style={[styles.container, { backgroundColor: theme.background }]}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.primary} />}
        >
            <View style={styles.content}>
                <Text style={[typography.h3, { color: theme.text, marginBottom: spacing.base }]}>
                    Mother Registry ({mothers.length})
                </Text>
                {mothers.length > 0 ? mothers.map((m) => (
                    <TouchableOpacity
                        key={m.id}
                        style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}
                        activeOpacity={0.7}
                        onPress={() => setExpandedMother(expandedMother === m.id ? null : m.id)}
                    >
                        {/* Top Row */}
                        <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                            <View style={[styles.avatar, { backgroundColor: '#FCE7F3' }]}>
                                <Text style={{ fontSize: 20 }}>👩</Text>
                            </View>
                            <View style={{ flex: 1, marginLeft: spacing.md }}>
                                <Text style={[typography.bodyBold, { color: theme.text }]}>{m.name || m.full_name || 'Mother'}</Text>
                                <Text style={[typography.caption, { color: theme.textSecondary }]}>
                                    Status: {m.status || '–'}
                                </Text>
                            </View>
                            <View style={{ alignItems: 'flex-end' }}>
                                <View style={[styles.statusBadge, { backgroundColor: m.status === 'postnatal' ? '#10B98120' : '#3B82F620' }]}>
                                    <Text style={{ fontSize: 10, fontWeight: '700', color: m.status === 'postnatal' ? '#10B981' : '#3B82F6' }}>
                                        {m.status === 'postnatal' ? '✓ Delivered' : m.status || 'Active'}
                                    </Text>
                                </View>
                            </View>
                        </View>

                        {/* Detail Chips */}
                        <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginTop: 8, gap: 8 }}>
                            <View style={[styles.detailChip, { backgroundColor: theme.surfaceElevated }]}>
                                <Text style={[typography.caption, { color: theme.textSecondary }]}>
                                    Gravida: {m.gravida != null ? `G${m.gravida}` : '–'}
                                </Text>
                            </View>
                            <View style={[styles.detailChip, { backgroundColor: theme.surfaceElevated }]}>
                                <Text style={[typography.caption, { color: theme.textSecondary }]}>
                                    Parity: {m.parity != null ? `P${m.parity}` : '–'}
                                </Text>
                            </View>
                            <View style={[styles.detailChip, { backgroundColor: theme.surfaceElevated }]}>
                                <Text style={[typography.caption, { color: theme.textSecondary }]}>
                                    🩸 {m.blood_group || '–'}
                                </Text>
                            </View>
                            {m.phone && (
                                <View style={[styles.detailChip, { backgroundColor: theme.primary + '15' }]}>
                                    <Text style={[typography.caption, { color: theme.primary, fontWeight: '600' }]}>📞 {m.phone}</Text>
                                </View>
                            )}
                        </View>

                        {/* Expanded Actions */}
                        {expandedMother === m.id && (
                            <View style={[styles.optionsRow, { borderTopColor: theme.border }]}>
                                <TouchableOpacity
                                    style={[styles.optionBtn, { backgroundColor: '#8B5CF615' }]}
                                    onPress={() => navigation.navigate('AssessmentHistory', { motherId: m.id })}
                                >
                                    <Ionicons name="clipboard-outline" size={18} color="#8B5CF6" />
                                    <Text style={[styles.optionText, { color: '#8B5CF6' }]}>Assessments</Text>
                                </TouchableOpacity>
                                <TouchableOpacity
                                    style={[styles.optionBtn, { backgroundColor: '#3B82F615' }]}
                                    onPress={() => navigation.navigate('PostnatalAssessments', { motherId: m.id })}
                                >
                                    <Ionicons name="add-circle-outline" size={18} color="#3B82F6" />
                                    <Text style={[styles.optionText, { color: '#3B82F6' }]}>New Assessment</Text>
                                </TouchableOpacity>
                            </View>
                        )}
                    </TouchableOpacity>
                )) : (
                    <EmptyState icon="heart-outline" title="No Mothers Registered" message="Registered mothers will appear here." />
                )}
            </View>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1 },
    content: { padding: spacing.screenPadding, paddingTop: spacing.xl, paddingBottom: 100 },
    card: {
        padding: spacing.base, borderRadius: borderRadius.lg,
        borderWidth: 1, marginBottom: spacing.md,
    },
    avatar: { width: 44, height: 44, borderRadius: 22, justifyContent: 'center', alignItems: 'center' },
    statusBadge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 6 },
    detailChip: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8 },
    optionsRow: {
        flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between',
        marginTop: spacing.base, paddingTop: spacing.base, borderTopWidth: 1, gap: 8,
    },
    optionBtn: {
        width: '47%', flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
        paddingVertical: 8, borderRadius: borderRadius.sm, gap: 4, marginBottom: 4,
    },
    optionText: { fontSize: 12, fontWeight: '600' },
});
