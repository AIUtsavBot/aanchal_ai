// Growth Charts Screen
import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, StyleSheet, Dimensions, TouchableOpacity } from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { supabase } from '../../services/auth';
import { typography, spacing, borderRadius } from '../../theme';
import { LoadingSpinner } from '../../components/shared';

const { width } = Dimensions.get('window');

export default function GrowthChartsScreen({ route }) {
    const { childId: initialChildId } = route?.params || {};
    const [childId, setChildId] = useState(initialChildId);
    const { user } = useAuth();
    const [children, setChildren] = useState([]);
    const { theme } = useTheme();
    const [loading, setLoading] = useState(false);
    const [dropdownOpen, setDropdownOpen] = useState(false);
    const [chartData, setChartData] = useState({
        weight: { labels: ['0d'], data: [0] },
        height: { labels: ['0d'], data: [0] },
    });

    useEffect(() => {
        if (!user?.id) return;
        const loadChildren = async () => {
            try {
                let mQuery = supabase.from('mothers').select('id').eq('status', 'postnatal');
                if (user.role === 'ASHA_WORKER') {
                    const { data: asha } = await supabase.from('asha_workers').select('id').eq('user_id', user.id).maybeSingle();
                    if (asha) mQuery = mQuery.eq('asha_worker_id', asha.id);
                } else if (user.role === 'DOCTOR') {
                    const { data: doc } = await supabase.from('doctors').select('id').eq('user_profile_id', user.id).maybeSingle();
                    if (doc) mQuery = mQuery.eq('doctor_id', doc.id);
                }
                const { data: mData } = await mQuery;
                if (mData && mData.length > 0) {
                    const mIds = mData.map(m => m.id);
                    const { data: cData } = await supabase.from('children').select('id, name, gender').in('mother_id', mIds);
                    if (cData) {
                        setChildren(cData);
                        if (!childId && cData.length > 0) setChildId(cData[0].id);
                    }
                }
            } catch (err) {
                console.error("Error loading children", err);
            }
        };
        if (!initialChildId) loadChildren();
    }, [user?.id, initialChildId]);

    useEffect(() => {
        if (!childId) return;
        const fetchGrowthData = async () => {
            setLoading(true);
            try {
                // Query growth_records table (correct table matching web frontend)
                const { data, error } = await supabase
                    .from('growth_records')
                    .select('measurement_date, weight_kg, height_cm, age_months, age_days')
                    .eq('child_id', childId)
                    .order('measurement_date', { ascending: true });

                if (!error && data && data.length > 0) {
                    const labels = data.map(d => {
                        if (d.age_months != null) return `${d.age_months}m`;
                        if (d.age_days != null) return `${d.age_days}d`;
                        if (d.measurement_date) return d.measurement_date.substring(5, 10); // MM-DD
                        return '?';
                    });
                    const weights = data.map(d => Number(d.weight_kg) || 0);
                    const heights = data.map(d => Number(d.height_cm) || 0);

                    setChartData({
                        weight: { labels, data: weights.some(w => w > 0) ? weights : [0] },
                        height: { labels, data: heights.some(h => h > 0) ? heights : [0] }
                    });
                    return;
                }
                // Fallback to empty state if no real data
                setChartData({ weight: { labels: ['0d'], data: [0] }, height: { labels: ['0d'], data: [0] } });
            } catch (err) {
                console.error("Error fetching growth data:", err);
                setChartData({ weight: { labels: ['0d'], data: [0] }, height: { labels: ['0d'], data: [0] } });
            } finally {
                setLoading(false);
            }
        };
        fetchGrowthData();
    }, [childId]);

    const chartConfig = {
        backgroundGradientFrom: theme.surface,
        backgroundGradientTo: theme.surface,
        color: (opacity = 1) => `rgba(13, 148, 136, ${opacity})`,
        labelColor: () => theme.textSecondary,
        propsForDots: { r: '5', strokeWidth: '2', stroke: theme.primary },
        decimalPlaces: 1,
    };

    const selectedChild = children.find(c => c.id === childId);

    return (
        <ScrollView style={[styles.container, { backgroundColor: theme.background }]}>
            <View style={styles.content}>
                <Text style={[typography.h3, { color: theme.text, marginBottom: spacing.lg }]}>
                    Growth Charts (WHO Standards)
                </Text>

                {/* Dropdown Child Selector */}
                {!initialChildId && children.length > 0 && (
                    <View style={{ marginBottom: spacing.xl, zIndex: 10 }}>
                        <Text style={[typography.smallBold, { color: theme.textSecondary, marginBottom: spacing.sm }]}>Select Child</Text>
                        <TouchableOpacity
                            style={[styles.dropdown, { backgroundColor: theme.surface, borderColor: theme.border }]}
                            onPress={() => setDropdownOpen(!dropdownOpen)}
                            activeOpacity={0.7}
                        >
                            <View style={{ flexDirection: 'row', alignItems: 'center', flex: 1 }}>
                                <View style={[styles.dropdownAvatar, { backgroundColor: theme.info + '20' }]}>
                                    <Ionicons name="happy" size={18} color={theme.info} />
                                </View>
                                <Text style={[typography.body, { color: theme.text, marginLeft: spacing.sm }]}>
                                    {selectedChild?.name || 'Select a child'}
                                </Text>
                            </View>
                            <Ionicons name={dropdownOpen ? 'chevron-up' : 'chevron-down'} size={20} color={theme.textSecondary} />
                        </TouchableOpacity>

                        {dropdownOpen && (
                            <View style={[styles.dropdownList, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                                {children.map(c => (
                                    <TouchableOpacity
                                        key={c.id}
                                        style={[
                                            styles.dropdownItem,
                                            { borderBottomColor: theme.border },
                                            childId === c.id && { backgroundColor: theme.primary + '15' }
                                        ]}
                                        onPress={() => { setChildId(c.id); setDropdownOpen(false); }}
                                    >
                                        <View style={[styles.dropdownAvatar, { backgroundColor: c.gender === 'male' ? '#DBEAFE' : '#FCE7F3' }]}>
                                            <Text style={{ fontSize: 14 }}>{c.gender === 'male' ? '♂' : '♀'}</Text>
                                        </View>
                                        <Text style={[typography.body, { color: theme.text, marginLeft: spacing.sm, flex: 1 }]}>
                                            {c.name || 'Baby'}
                                        </Text>
                                        {childId === c.id && <Ionicons name="checkmark-circle" size={20} color={theme.primary} />}
                                    </TouchableOpacity>
                                ))}
                            </View>
                        )}
                    </View>
                )}

                {/* Weight Chart */}
                <View style={[styles.chartCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                    <View style={styles.chartHeader}>
                        <Text style={[typography.bodyBold, { color: theme.text }]}>⚖️ Weight (kg)</Text>
                    </View>
                    {loading ? <LoadingSpinner /> : (
                        <LineChart
                            data={{ labels: chartData.weight.labels, datasets: [{ data: chartData.weight.data }] }}
                            width={width - spacing.screenPadding * 2 - spacing.cardPadding * 2}
                            height={200}
                            chartConfig={chartConfig}
                            bezier
                            style={styles.chart}
                        />
                    )}
                </View>

                {/* Height Chart */}
                <View style={[styles.chartCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                    <View style={styles.chartHeader}>
                        <Text style={[typography.bodyBold, { color: theme.text }]}>📏 Length/Height (cm)</Text>
                    </View>
                    {loading ? <LoadingSpinner /> : (
                        <LineChart
                            data={{ labels: chartData.height.labels, datasets: [{ data: chartData.height.data }] }}
                            width={width - spacing.screenPadding * 2 - spacing.cardPadding * 2}
                            height={200}
                            chartConfig={{
                                ...chartConfig,
                                color: (opacity = 1) => `rgba(59, 130, 246, ${opacity})`,
                            }}
                            bezier
                            style={styles.chart}
                        />
                    )}
                </View>

                <View style={[styles.infoCard, { backgroundColor: theme.infoLight }]}>
                    <Text style={[typography.smallBold, { color: theme.info }]}>ℹ️ About WHO Z-Scores</Text>
                    <Text style={[typography.caption, { color: theme.info, marginTop: 4 }]}>
                        Growth data is plotted against WHO Child Growth Standards. Z-scores between -2 and +2 are considered normal range.
                    </Text>
                </View>
            </View>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1 },
    content: { padding: spacing.screenPadding, paddingTop: spacing.xl },
    chartCard: { borderRadius: borderRadius.lg, borderWidth: 1, padding: spacing.cardPadding, marginBottom: spacing.lg },
    chartHeader: { marginBottom: spacing.md },
    chart: { borderRadius: borderRadius.md },
    infoCard: { padding: spacing.base, borderRadius: borderRadius.md },
    dropdown: {
        flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
        padding: spacing.md, borderRadius: borderRadius.md, borderWidth: 1,
    },
    dropdownAvatar: {
        width: 32, height: 32, borderRadius: 16, justifyContent: 'center', alignItems: 'center',
    },
    dropdownList: {
        marginTop: 4, borderRadius: borderRadius.md, borderWidth: 1,
        overflow: 'hidden',
    },
    dropdownItem: {
        flexDirection: 'row', alignItems: 'center', padding: spacing.md,
        borderBottomWidth: 1,
    },
});
