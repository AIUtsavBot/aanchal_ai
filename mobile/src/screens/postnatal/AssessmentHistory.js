// Assessment History Screen - Shows previous postnatal assessments for a child/mother
import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, StyleSheet, RefreshControl } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { supabase } from '../../services/auth';
import { typography, spacing, borderRadius } from '../../theme';
import { EmptyState, LoadingSpinner } from '../../components/shared';

export default function AssessmentHistoryScreen({ route }) {
    const { childId, motherId } = route?.params || {};
    const { user } = useAuth();
    const { theme } = useTheme();
    const [assessments, setAssessments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [childInfo, setChildInfo] = useState(null);
    const [motherInfo, setMotherInfo] = useState(null);

    const loadData = async () => {
        try {
            // Load child info
            if (childId) {
                try {
                    const { data: child } = await supabase
                        .from('children')
                        .select('*')
                        .eq('id', childId)
                        .maybeSingle();
                    if (child) setChildInfo(child);
                } catch (e) {
                    console.warn('Child info query error:', e);
                }
            }

            // Load mother info - use select('*') to avoid column mismatch 400 errors
            if (motherId) {
                try {
                    const { data: mother, error: motherErr } = await supabase
                        .from('mothers')
                        .select('*')
                        .eq('id', motherId)
                        .maybeSingle();
                    if (motherErr) console.warn('Mother info query error:', motherErr);
                    if (mother) setMotherInfo(mother);
                } catch (e) {
                    console.warn('Mother info query failed:', e);
                }
            }

            const allAssessments = [];

            // ===== CHILD-SPECIFIC VIEW (opened from child card) =====
            if (childId) {
                // Strategy 1: Query by child_id directly
                try {
                    const { data: byChildId, error: err1 } = await supabase
                        .from('postnatal_assessments')
                        .select('*')
                        .eq('child_id', childId)
                        .order('assessment_date', { ascending: false });
                    if (!err1 && byChildId && byChildId.length > 0) {
                        allAssessments.push(...byChildId.map(a => ({ ...a, source: 'postnatal', target: 'child' })));
                    }
                } catch (e) {
                    console.warn('Child assessments by child_id error:', e);
                }

                // Strategy 2: If motherId is available, also get child_checkup assessments by mother_id + assessment_type
                // This covers cases where assessments were stored with mother_id but assessment_type='child_checkup'
                if (motherId) {
                    try {
                        const { data: byMotherType, error: err2 } = await supabase
                            .from('postnatal_assessments')
                            .select('*')
                            .eq('mother_id', motherId)
                            .eq('assessment_type', 'child_checkup')
                            .order('assessment_date', { ascending: false });
                        if (!err2 && byMotherType) {
                            // Deduplicate: only add if not already in allAssessments
                            const existingIds = new Set(allAssessments.map(a => a.id));
                            const newEntries = byMotherType.filter(a => !existingIds.has(a.id));
                            allAssessments.push(...newEntries.map(a => ({ ...a, source: 'postnatal', target: 'child' })));
                        }
                    } catch (e) {
                        console.warn('Child assessments by mother_id+type error:', e);
                    }
                }
            }

            // ===== MOTHER-SPECIFIC VIEW (opened from mother card, no childId) =====
            if (motherId && !childId) {
                // Mother postnatal assessments ONLY (exclude child_checkup)
                try {
                    const { data: motherAssessments, error: err3 } = await supabase
                        .from('postnatal_assessments')
                        .select('*')
                        .eq('mother_id', motherId)
                        .eq('assessment_type', 'mother_postnatal')
                        .order('assessment_date', { ascending: false });
                    if (!err3 && motherAssessments) {
                        allAssessments.push(...motherAssessments.map(a => ({
                            ...a,
                            source: 'postnatal',
                            target: 'mother'
                        })));
                    }
                } catch (e) {
                    console.warn('Mother assessments query error:', e);
                }

                // Risk assessments for mother
                try {
                    const { data: riskData, error: err4 } = await supabase
                        .from('risk_assessments')
                        .select('*')
                        .eq('mother_id', motherId)
                        .order('created_at', { ascending: false });
                    if (!err4 && riskData) {
                        allAssessments.push(...riskData.map(a => ({ ...a, source: 'risk', target: 'mother' })));
                    }
                } catch (e) {
                    console.warn('Risk assessments query error:', e);
                }
            }

            // Sort by date descending
            allAssessments.sort((a, b) => {
                const dateA = new Date(a.assessment_date || a.created_at);
                const dateB = new Date(b.assessment_date || b.created_at);
                return dateB - dateA;
            });

            setAssessments(allAssessments);
        } catch (err) {
            console.error('Error loading assessment history:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { loadData(); }, [childId, motherId]);

    const onRefresh = async () => { setRefreshing(true); await loadData(); setRefreshing(false); };

    const getAssessmentIcon = (assessment) => {
        if (assessment.source === 'risk') return 'warning-outline';
        if (assessment.target === 'child') return 'happy-outline';
        return 'heart-outline';
    };

    const getAssessmentColor = (assessment) => {
        const risk = assessment.overall_risk_level || assessment.risk_level;
        if (risk === 'HIGH' || risk === 'high') return '#EF4444';
        if (risk === 'MEDIUM' || risk === 'medium') return '#F97316';
        if (risk === 'LOW' || risk === 'low') return '#10B981';
        return theme.info;
    };

    const getAssessmentTitle = (assessment) => {
        if (assessment.source === 'risk') return 'Risk Assessment';
        if (assessment.assessment_type === 'child_checkup') return 'Child Health Check';
        if (assessment.assessment_type === 'mother_postnatal') return 'Mother Health Check';
        if (assessment.target === 'child') return 'Child Health Check';
        return 'Mother Health Check';
    };

    if (loading) return <LoadingSpinner />;

    const heading = childId ? 'Child Assessment History' : 'Mother Assessment History';

    return (
        <ScrollView
            style={[styles.container, { backgroundColor: theme.background }]}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.primary} />}
        >
            <View style={styles.content}>
                <Text style={[typography.h3, { color: theme.text, marginBottom: spacing.sm }]}>
                    {heading}
                </Text>

                {/* Info Banner */}
                <View style={[styles.infoBanner, { backgroundColor: theme.surfaceElevated, borderColor: theme.border }]}>
                    {childInfo && (
                        <View style={styles.infoRow}>
                            <Ionicons name="happy" size={16} color={theme.info} />
                            <Text style={[typography.bodyBold, { color: theme.text, marginLeft: 6 }]}>
                                {childInfo.name || 'Baby'}
                            </Text>
                            <Text style={[typography.caption, { color: theme.textTertiary, marginLeft: 8 }]}>
                                Born: {childInfo.birth_date ? new Date(childInfo.birth_date).toLocaleDateString() : '–'}
                            </Text>
                        </View>
                    )}
                    {motherInfo && (
                        <View style={[styles.infoRow, { marginTop: childInfo ? 6 : 0 }]}>
                            <Ionicons name="heart" size={16} color={theme.primary} />
                            <Text style={[typography.bodyBold, { color: theme.text, marginLeft: 6 }]}>
                                {motherInfo.name || motherInfo.full_name || 'Mother'}
                            </Text>
                        </View>
                    )}
                    {motherInfo && (
                        <View style={styles.detailsGrid}>
                            <View style={styles.detailCell}>
                                <Text style={[styles.detailLabel, { color: theme.textTertiary }]}>GRAVIDA</Text>
                                <Text style={[styles.detailValue, { color: theme.text }]}>{motherInfo.gravida != null ? `G${motherInfo.gravida}` : '–'}</Text>
                            </View>
                            <View style={styles.detailCell}>
                                <Text style={[styles.detailLabel, { color: theme.textTertiary }]}>PARITY</Text>
                                <Text style={[styles.detailValue, { color: theme.text }]}>{motherInfo.parity != null ? `P${motherInfo.parity}` : '–'}</Text>
                            </View>
                            <View style={styles.detailCell}>
                                <Text style={[styles.detailLabel, { color: theme.textTertiary }]}>BLOOD GROUP</Text>
                                <Text style={[styles.detailValue, { color: theme.text }]}>{motherInfo.blood_group || '–'}</Text>
                            </View>
                            <View style={styles.detailCell}>
                                <Text style={[styles.detailLabel, { color: theme.textTertiary }]}>STATUS</Text>
                                <Text style={[styles.detailValue, { color: motherInfo.delivery_status === 'delivered' ? '#10B981' : theme.primary }]}>
                                    {motherInfo.delivery_status || motherInfo.status || '–'}
                                </Text>
                            </View>
                        </View>
                    )}
                </View>

                {/* Assessment Count */}
                <Text style={[typography.smallBold, { color: theme.textSecondary, marginBottom: spacing.md }]}>
                    {assessments.length} assessment{assessments.length !== 1 ? 's' : ''} found
                </Text>

                {/* Assessment Cards */}
                {assessments.length > 0 ? assessments.map((a, idx) => {
                    const color = getAssessmentColor(a);
                    const date = a.assessment_date || a.created_at;
                    const risk = a.overall_risk_level || a.risk_level;

                    return (
                        <View key={`${a.source}-${a.id || idx}`} style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border, borderLeftColor: color, borderLeftWidth: 3 }]}>
                            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                                <View style={{ flexDirection: 'row', alignItems: 'center', flex: 1 }}>
                                    <Ionicons name={getAssessmentIcon(a)} size={18} color={color} />
                                    <Text style={[typography.bodyBold, { color: theme.text, marginLeft: 6 }]}>
                                        {getAssessmentTitle(a)}
                                    </Text>
                                </View>
                                {risk && (
                                    <View style={[styles.riskBadge, { backgroundColor: color + '20' }]}>
                                        <Text style={{ fontSize: 10, fontWeight: '700', color }}>{risk}</Text>
                                    </View>
                                )}
                            </View>

                            {/* Assessment Details */}
                            <View style={styles.vitalsGrid}>
                                {a.temperature && (
                                    <View style={styles.vitalItem}>
                                        <Text style={[typography.caption, { color: theme.textTertiary }]}>🌡️ Temp</Text>
                                        <Text style={[typography.bodyBold, { color: theme.text, fontSize: 13 }]}>{a.temperature}°C</Text>
                                    </View>
                                )}
                                {a.blood_pressure && (
                                    <View style={styles.vitalItem}>
                                        <Text style={[typography.caption, { color: theme.textTertiary }]}>🩺 BP</Text>
                                        <Text style={[typography.bodyBold, { color: theme.text, fontSize: 13 }]}>{a.blood_pressure}</Text>
                                    </View>
                                )}
                                {a.weight_kg && (
                                    <View style={styles.vitalItem}>
                                        <Text style={[typography.caption, { color: theme.textTertiary }]}>⚖️ Weight</Text>
                                        <Text style={[typography.bodyBold, { color: theme.text, fontSize: 13 }]}>{a.weight_kg} kg</Text>
                                    </View>
                                )}
                                {a.length_cm && (
                                    <View style={styles.vitalItem}>
                                        <Text style={[typography.caption, { color: theme.textTertiary }]}>📏 Length</Text>
                                        <Text style={[typography.bodyBold, { color: theme.text, fontSize: 13 }]}>{a.length_cm} cm</Text>
                                    </View>
                                )}
                                {a.head_circumference_cm && (
                                    <View style={styles.vitalItem}>
                                        <Text style={[typography.caption, { color: theme.textTertiary }]}>🧠 Head</Text>
                                        <Text style={[typography.bodyBold, { color: theme.text, fontSize: 13 }]}>{a.head_circumference_cm} cm</Text>
                                    </View>
                                )}
                                {a.breastfeeding_status && (
                                    <View style={styles.vitalItem}>
                                        <Text style={[typography.caption, { color: theme.textTertiary }]}>🍼 Feeding</Text>
                                        <Text style={[typography.bodyBold, { color: theme.text, fontSize: 13 }]}>{a.breastfeeding_status}</Text>
                                    </View>
                                )}
                                {a.hemoglobin && (
                                    <View style={styles.vitalItem}>
                                        <Text style={[typography.caption, { color: theme.textTertiary }]}>🩸 Hb</Text>
                                        <Text style={[typography.bodyBold, { color: theme.text, fontSize: 13 }]}>{a.hemoglobin} g/dL</Text>
                                    </View>
                                )}
                            </View>

                            {/* Notes */}
                            {(a.notes || a.details?.notes || a.description || a.complications) && (
                                <Text style={[typography.caption, { color: theme.textSecondary, marginTop: 6 }]} numberOfLines={3}>
                                    {a.notes || a.details?.notes || a.description || a.complications}
                                </Text>
                            )}

                            {/* Date */}
                            {date && (
                                <Text style={[typography.caption, { color: theme.textTertiary, marginTop: 8 }]}>
                                    📅 {new Date(date).toLocaleDateString()} at {new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </Text>
                            )}
                        </View>
                    );
                }) : (
                    <EmptyState
                        icon="clipboard-outline"
                        title="No Assessments Yet"
                        message={childId ? "No child health check records found." : "No mother health check records found."}
                    />
                )}
            </View>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1 },
    content: { padding: spacing.screenPadding, paddingTop: spacing.xl, paddingBottom: 100 },
    infoBanner: {
        padding: spacing.base, borderRadius: borderRadius.md, borderWidth: 1,
        marginBottom: spacing.md,
    },
    infoRow: {
        flexDirection: 'row', alignItems: 'center',
    },
    detailsGrid: {
        flexDirection: 'row', flexWrap: 'wrap', marginTop: 10, gap: 2,
    },
    detailCell: {
        width: '48%', paddingVertical: 6, paddingHorizontal: 8,
    },
    detailLabel: {
        fontSize: 10, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 2,
    },
    detailValue: {
        fontSize: 15, fontWeight: '700',
    },
    card: {
        padding: spacing.base, borderRadius: borderRadius.lg, borderWidth: 1,
        marginBottom: spacing.md,
    },
    riskBadge: {
        paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6,
    },
    vitalsGrid: {
        flexDirection: 'row', flexWrap: 'wrap', gap: 12,
    },
    vitalItem: {
        minWidth: 70,
    },
    detailRow: {
        flexDirection: 'row', alignItems: 'center', marginTop: 4,
    },
});
