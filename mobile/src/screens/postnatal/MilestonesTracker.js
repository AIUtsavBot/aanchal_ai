import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Modal, FlatList } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { supabase } from '../../services/auth';
import { typography, spacing, borderRadius } from '../../theme';

const milestoneGroups = [
    {
        age: '0–1 Month', category_map: 'gross_motor', milestones: [
            { text: 'Moves arms and legs', icon: 'body-outline', category: 'Motor' },
            { text: 'Responds to sounds', icon: 'ear-outline', category: 'Sensory' },
            { text: 'Looks at faces', icon: 'happy-outline', category: 'Social' },
        ]
    },
    {
        age: '2 Months', milestones: [
            { text: 'Lifts head briefly', icon: 'body-outline', category: 'Motor' },
            { text: 'Social smile', icon: 'happy-outline', category: 'Social' },
            { text: 'Follows objects', icon: 'eye-outline', category: 'Sensory' },
        ]
    },
    {
        age: '4 Months', milestones: [
            { text: 'Holds head steady', icon: 'body-outline', category: 'Motor' },
            { text: 'Reaches for objects', icon: 'hand-left-outline', category: 'Motor' },
            { text: 'Coos and babbles', icon: 'chatbubble-outline', category: 'Language' },
            { text: 'Laughs', icon: 'happy-outline', category: 'Social' },
        ]
    },
    {
        age: '6 Months', milestones: [
            { text: 'Sits with support', icon: 'body-outline', category: 'Motor' },
            { text: 'Transfers objects', icon: 'hand-left-outline', category: 'Motor' },
            { text: 'Responds to name', icon: 'ear-outline', category: 'Language' },
            { text: 'Stranger anxiety', icon: 'happy-outline', category: 'Social' },
        ]
    },
    {
        age: '9 Months', milestones: [
            { text: 'Sits without support', icon: 'body-outline', category: 'Motor' },
            { text: 'Crawls', icon: 'walk-outline', category: 'Motor' },
            { text: 'Pincer grasp developing', icon: 'hand-left-outline', category: 'Motor' },
            { text: 'Says mama/dada', icon: 'chatbubble-outline', category: 'Language' },
        ]
    },
    {
        age: '12 Months', milestones: [
            { text: 'Stands alone', icon: 'body-outline', category: 'Motor' },
            { text: 'Walks with support', icon: 'walk-outline', category: 'Motor' },
            { text: '1-2 words', icon: 'chatbubble-outline', category: 'Language' },
            { text: 'Object permanence', icon: 'bulb-outline', category: 'Cognitive' },
        ]
    },
    {
        age: '18 Months', milestones: [
            { text: 'Walks independently', icon: 'walk-outline', category: 'Motor' },
            { text: 'Scribbles', icon: 'pencil-outline', category: 'Motor' },
            { text: '15-20 words', icon: 'chatbubble-outline', category: 'Language' },
            { text: 'Parallel play', icon: 'people-outline', category: 'Social' },
        ]
    },
    {
        age: '24 Months', milestones: [
            { text: 'Runs', icon: 'walk-outline', category: 'Motor' },
            { text: 'Kicks ball', icon: 'football-outline', category: 'Motor' },
            { text: '2-word sentences', icon: 'chatbubble-outline', category: 'Language' },
            { text: 'Follows 2-step commands', icon: 'bulb-outline', category: 'Cognitive' },
        ]
    },
];

const CATEGORY_MAP = {
    'Motor': 'gross_motor',
    'Language': 'language',
    'Cognitive': 'cognitive',
    'Social': 'social_emotional',
    'Sensory': 'cognitive',
};

export default function MilestonesTrackerScreen({ route }) {
    const { childId: initialChildId } = route?.params || {};
    const [childId, setChildId] = useState(initialChildId);
    const { user } = useAuth();
    const [children, setChildren] = useState([]);
    const { theme } = useTheme();
    const [achieved, setAchieved] = useState({});
    const [loading, setLoading] = useState(false);
    const [dropdownOpen, setDropdownOpen] = useState(false);

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
                    const { data: cData } = await supabase.from('children').select('id, name, birth_date, gender').in('mother_id', mIds);
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
        const fetchMilestones = async () => {
            setLoading(true);
            try {
                const { data, error } = await supabase
                    .from('milestones')
                    .select('milestone_name, is_achieved')
                    .eq('child_id', childId)
                    .eq('is_achieved', true);

                if (!error && data) {
                    const mapped = {};
                    data.forEach(mRecord => {
                        milestoneGroups.forEach((group, gi) => {
                            group.milestones.forEach((m, mi) => {
                                if (m.text === mRecord.milestone_name) {
                                    mapped[`${gi}-${mi}`] = true;
                                }
                            });
                        });
                    });
                    setAchieved(mapped);
                }
            } catch (err) {
                console.error("Error fetching milestones:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchMilestones();
    }, [childId]);

    const toggle = async (groupIdx, mIdx) => {
        if (!childId) return;
        const key = `${groupIdx}-${mIdx}`;
        const milestone = milestoneGroups[groupIdx].milestones[mIdx];
        const isCurrentlyDone = achieved[key];

        // Optimistic update
        setAchieved((prev) => ({ ...prev, [key]: !isCurrentlyDone }));

        try {
            if (!isCurrentlyDone) {
                // Calculate age
                const childData = children.find(c => c.id === childId);
                let age_months = 0, age_days = 0;
                if (childData?.birth_date) {
                    const birth = new Date(childData.birth_date);
                    const now = new Date();
                    age_days = Math.floor((now - birth) / (1000 * 60 * 60 * 24));
                    age_months = Math.floor(age_days / 30);
                }
                const dbCategory = CATEGORY_MAP[milestone.category] || 'gross_motor';

                await supabase.from('milestones').insert({
                    child_id: childId,
                    milestone_name: milestone.text,
                    category: dbCategory,
                    expected_age_months: age_months,
                    is_achieved: true,
                    achieved_date: new Date().toISOString().split('T')[0],
                    achieved_age_months: age_months,
                    achieved_age_days: age_days,
                    observation_method: 'parent_report',
                    notes: '',
                });
            } else {
                // Find and update record to not achieved
                const { data: records } = await supabase
                    .from('milestones')
                    .select('id')
                    .eq('child_id', childId)
                    .eq('milestone_name', milestone.text)
                    .eq('is_achieved', true)
                    .limit(1);

                if (records && records.length > 0) {
                    await supabase
                        .from('milestones')
                        .update({ is_achieved: false, achieved_date: null, achieved_age_months: null, achieved_age_days: null })
                        .eq('id', records[0].id);
                }
            }
        } catch (err) {
            console.error("Error saving milestone:", err);
            // Revert
            setAchieved((prev) => ({ ...prev, [key]: isCurrentlyDone }));
        }
    };

    const selectedChild = children.find(c => c.id === childId);

    return (
        <ScrollView style={[styles.container, { backgroundColor: theme.background }]}>
            <View style={styles.content}>
                <Text style={[typography.h3, { color: theme.text, marginBottom: spacing.sm }]}>
                    Developmental Milestones
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

                <Text style={[typography.small, { color: theme.textSecondary, marginBottom: spacing.xl }]}>
                    RBSK 4Ds Screening — Track developmental progress
                </Text>

                {milestoneGroups.map((g, gi) => {
                    const count = g.milestones.filter((_, mi) => achieved[`${gi}-${mi}`]).length;
                    return (
                        <View key={gi} style={{ marginBottom: spacing.xl }}>
                            <View style={styles.groupHeader}>
                                <Text style={[typography.bodyBold, { color: theme.text }]}>📅 {g.age}</Text>
                                <View style={[styles.progressBadge, { backgroundColor: count === g.milestones.length ? theme.successLight : theme.surfaceElevated }]}>
                                    <Text style={[typography.captionBold, { color: count === g.milestones.length ? theme.success : theme.textSecondary }]}>
                                        {count}/{g.milestones.length}
                                    </Text>
                                </View>
                            </View>
                            {/* Progress bar */}
                            <View style={[styles.progressBar, { backgroundColor: theme.surfaceElevated }]}>
                                <View style={[styles.progressFill, { width: `${(count / g.milestones.length) * 100}%`, backgroundColor: theme.primary }]} />
                            </View>
                            {g.milestones.map((m, mi) => {
                                const done = achieved[`${gi}-${mi}`];
                                return (
                                    <TouchableOpacity
                                        key={mi}
                                        style={[styles.milestoneRow, { backgroundColor: theme.surface, borderColor: done ? theme.success : theme.border }]}
                                        onPress={() => toggle(gi, mi)}
                                        activeOpacity={0.7}
                                    >
                                        <View style={[styles.check, done && { backgroundColor: theme.success, borderColor: theme.success }]}>
                                            {done && <Ionicons name="checkmark" size={14} color="#fff" />}
                                        </View>
                                        <Ionicons name={m.icon} size={18} color={done ? theme.success : theme.textSecondary} style={{ marginLeft: spacing.md }} />
                                        <View style={{ marginLeft: spacing.sm, flex: 1 }}>
                                            <Text style={[typography.small, { color: theme.text }]}>{m.text}</Text>
                                            <Text style={[typography.caption, { color: theme.textTertiary }]}>{m.category}</Text>
                                        </View>
                                    </TouchableOpacity>
                                );
                            })}
                        </View>
                    );
                })}
            </View>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1 },
    content: { padding: spacing.screenPadding, paddingTop: spacing.xl, paddingBottom: 100 },
    groupHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.sm },
    progressBadge: { paddingHorizontal: 10, paddingVertical: 3, borderRadius: 10 },
    progressBar: { height: 4, borderRadius: 2, marginBottom: spacing.md },
    progressFill: { height: '100%', borderRadius: 2 },
    milestoneRow: {
        flexDirection: 'row', alignItems: 'center', padding: spacing.md,
        borderRadius: borderRadius.md, borderWidth: 1, marginBottom: spacing.xs,
    },
    check: { width: 22, height: 22, borderRadius: 6, borderWidth: 2, borderColor: '#CBD5E1', justifyContent: 'center', alignItems: 'center' },
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
