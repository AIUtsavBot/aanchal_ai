// Children List Screen
import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, RefreshControl } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../contexts/AuthContext';
import { supabase } from '../../services/auth';
import { useTheme } from '../../contexts/ThemeContext';
import { typography, spacing, borderRadius } from '../../theme';
import { EmptyState, LoadingSpinner } from '../../components/shared';

export default function ChildrenListScreen({ navigation }) {
    const { user } = useAuth();
    const { theme } = useTheme();
    const [children, setChildren] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [expandedChild, setExpandedChild] = useState(null);

    const loadData = async () => {
        try {
            if (!user?.id) return;

            // 1. Build mothers query
            let mothersQuery = supabase.from('mothers').select('id, name').eq('status', 'postnatal');

            if (user.role === 'ASHA_WORKER') {
                const { data: asha } = await supabase.from('asha_workers').select('id').eq('user_id', user.id).maybeSingle();
                if (asha) mothersQuery = mothersQuery.eq('asha_worker_id', asha.id);
            } else if (user.role === 'DOCTOR') {
                const { data: doc } = await supabase.from('doctors').select('id').eq('user_profile_id', user.id).maybeSingle();
                if (doc) mothersQuery = mothersQuery.eq('doctor_id', doc.id);
            }

            const { data: deliveredMothers, error: mError } = await mothersQuery;
            if (mError || !deliveredMothers) throw new Error('Failed to load mothers');

            const allChildren = [];
            const motherIds = deliveredMothers.map(m => m.id);

            if (motherIds.length > 0) {
                // Fetch all children associated with these mothers
                const { data: kids, error: kidsError } = await supabase.from('children').select('*').in('mother_id', motherIds);
                if (!kidsError && kids) {
                    kids.forEach(k => {
                        const m = deliveredMothers.find(mo => mo.id === k.mother_id);
                        allChildren.push({ ...k, motherName: m?.name || 'Unknown' });
                    });
                }
            }
            setChildren(allChildren);
        } catch (e) {
            console.error('ChildrenList loadData error:', e);
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
                    Children Registry ({children.length})
                </Text>
                {children.length > 0 ? children.map((c, i) => {
                    // Calculate age
                    let ageText = '';
                    const birthDate = c.birth_date || c.date_of_birth;
                    if (birthDate) {
                        const birth = new Date(birthDate);
                        const now = new Date();
                        const days = Math.floor((now - birth) / (1000 * 60 * 60 * 24));
                        if (days < 30) ageText = `${days} days old`;
                        else if (days < 365) ageText = `${Math.floor(days / 30)} months old`;
                        else ageText = `${Math.floor(days / 365)}y ${Math.floor((days % 365) / 30)}m old`;
                    }

                    return (
                        <TouchableOpacity
                            key={c.id || i}
                            style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border, flexDirection: 'column', alignItems: 'stretch' }]}
                            activeOpacity={0.7}
                            onPress={() => setExpandedChild(expandedChild === c.id ? null : c.id)}
                        >
                            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                                <View style={[styles.avatar, { backgroundColor: c.gender === 'male' ? '#DBEAFE' : '#FCE7F3' }]}>
                                    <Text style={{ fontSize: 20 }}>{c.gender === 'male' ? '👦' : '👧'}</Text>
                                </View>
                                <View style={{ flex: 1, marginLeft: spacing.md }}>
                                    <Text style={[typography.bodyBold, { color: theme.text }]}>{c.name || 'Baby'}</Text>
                                    <Text style={[typography.caption, { color: theme.textSecondary }]}>
                                        Mother: {c.motherName || 'N/A'}
                                    </Text>
                                    {birthDate && (
                                        <Text style={[typography.caption, { color: theme.textTertiary }]}>
                                            DOB: {new Date(birthDate).toLocaleDateString()} {ageText ? `(${ageText})` : ''}
                                        </Text>
                                    )}
                                </View>
                                <View style={{ alignItems: 'flex-end' }}>
                                    <View style={[styles.genderBadge, { backgroundColor: c.gender === 'male' ? '#DBEAFE' : '#FCE7F3' }]}>
                                        <Text style={{ fontSize: 16 }}>{c.gender === 'male' ? '♂' : '♀'}</Text>
                                    </View>
                                </View>
                            </View>

                            {/* Additional Details */}
                            <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginTop: 8, gap: 8 }}>
                                {c.birth_weight && (
                                    <View style={[styles.detailChip, { backgroundColor: theme.surfaceElevated }]}>
                                        <Text style={[typography.caption, { color: theme.textSecondary }]}>⚖️ {c.birth_weight} kg</Text>
                                    </View>
                                )}
                                {c.birth_type && (
                                    <View style={[styles.detailChip, { backgroundColor: theme.surfaceElevated }]}>
                                        <Text style={[typography.caption, { color: theme.textSecondary }]}>🏥 {c.birth_type}</Text>
                                    </View>
                                )}
                                {c.blood_group && (
                                    <View style={[styles.detailChip, { backgroundColor: theme.surfaceElevated }]}>
                                        <Text style={[typography.caption, { color: theme.textSecondary }]}>🩸 {c.blood_group}</Text>
                                    </View>
                                )}
                                {ageText && (
                                    <View style={[styles.detailChip, { backgroundColor: theme.primary + '15' }]}>
                                        <Text style={[typography.caption, { color: theme.primary, fontWeight: '600' }]}>📅 {ageText}</Text>
                                    </View>
                                )}
                            </View>

                            {expandedChild === c.id && (
                                <View style={[styles.optionsRow, { borderTopColor: theme.border }]}>
                                    <TouchableOpacity style={[styles.optionBtn, { backgroundColor: '#10B98115' }]} onPress={() => navigation.navigate('GrowthCharts', { childId: c.id })}>
                                        <Ionicons name="trending-up" size={18} color="#10B981" />
                                        <Text style={[styles.optionText, { color: '#10B981' }]}>Growth</Text>
                                    </TouchableOpacity>
                                    <TouchableOpacity style={[styles.optionBtn, { backgroundColor: '#3B82F615' }]} onPress={() => navigation.navigate('VaccinationCalendar', { childId: c.id })}>
                                        <Ionicons name="calendar-outline" size={18} color="#3B82F6" />
                                        <Text style={[styles.optionText, { color: '#3B82F6' }]}>Vaccines</Text>
                                    </TouchableOpacity>
                                    <TouchableOpacity style={[styles.optionBtn, { backgroundColor: '#F9731615' }]} onPress={() => navigation.navigate('MilestonesTracker', { childId: c.id })}>
                                        <Ionicons name="flag-outline" size={18} color="#F97316" />
                                        <Text style={[styles.optionText, { color: '#F97316' }]}>Milestones</Text>
                                    </TouchableOpacity>
                                    <TouchableOpacity style={[styles.optionBtn, { backgroundColor: '#0d948815' }]} onPress={() => navigation.navigate('AssessmentHistory', { childId: c.id, motherId: c.mother_id })}>
                                        <Ionicons name="clipboard-outline" size={18} color="#0d9488" />
                                        <Text style={[styles.optionText, { color: '#0d9488' }]}>Assessments</Text>
                                    </TouchableOpacity>
                                </View>
                            )}
                        </TouchableOpacity>
                    )
                }) : (
                    <EmptyState icon="happy-outline" title="No children registered" message="Children will appear after delivery records are created" />
                )}
            </View>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1 },
    content: { padding: spacing.screenPadding, paddingTop: spacing.xl, paddingBottom: 100 },
    card: {
        padding: spacing.base,
        borderRadius: borderRadius.lg, borderWidth: 1, marginBottom: spacing.md,
    },
    avatar: { width: 44, height: 44, borderRadius: 22, justifyContent: 'center', alignItems: 'center' },
    genderBadge: { width: 32, height: 32, borderRadius: 16, justifyContent: 'center', alignItems: 'center' },
    optionsRow: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', marginTop: spacing.base, paddingTop: spacing.base, borderTopWidth: 1, gap: 8 },
    optionBtn: { width: '47%', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 8, borderRadius: borderRadius.sm, gap: 4, marginBottom: 4 },
    optionText: { fontSize: 12, fontWeight: '600' },
    detailChip: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8 },
});
