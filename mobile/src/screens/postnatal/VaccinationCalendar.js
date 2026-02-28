import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { supabase } from '../../services/auth';
import { typography, spacing, borderRadius } from '../../theme';

// IAP 2023 Schedule
const schedule = [
    {
        age: 'Birth', vaccines: [
            { name: 'BCG', desc: 'Bacillus Calmette-Guérin' },
            { name: 'OPV-0', desc: 'Oral Polio Vaccine' },
            { name: 'Hep-B Birth', desc: 'Hepatitis B' },
        ]
    },
    {
        age: '6 Weeks', vaccines: [
            { name: 'DTwP/DTaP-1', desc: 'Diphtheria, Tetanus, Pertussis' },
            { name: 'IPV-1', desc: 'Inactivated Polio Vaccine' },
            { name: 'Hep-B-2', desc: 'Hepatitis B' },
            { name: 'Hib-1', desc: 'Haemophilus influenzae type b' },
            { name: 'PCV-1', desc: 'Pneumococcal Conjugate Vaccine' },
            { name: 'RV-1', desc: 'Rotavirus Vaccine' },
        ]
    },
    {
        age: '10 Weeks', vaccines: [
            { name: 'DTwP/DTaP-2', desc: 'Diphtheria, Tetanus, Pertussis' },
            { name: 'IPV-2', desc: 'Inactivated Polio Vaccine' },
            { name: 'Hib-2', desc: 'Haemophilus influenzae type b' },
            { name: 'RV-2', desc: 'Rotavirus Vaccine' },
        ]
    },
    {
        age: '14 Weeks', vaccines: [
            { name: 'DTwP/DTaP-3', desc: 'Diphtheria, Tetanus, Pertussis' },
            { name: 'IPV-3', desc: 'Inactivated Polio Vaccine' },
            { name: 'Hep-B-3', desc: 'Hepatitis B' },
            { name: 'Hib-3', desc: 'Haemophilus influenzae type b' },
            { name: 'PCV-2', desc: 'Pneumococcal Conjugate Vaccine' },
            { name: 'RV-3', desc: 'Rotavirus Vaccine' },
        ]
    },
    {
        age: '6 Months', vaccines: [
            { name: 'OPV-1', desc: 'Oral Polio Vaccine' },
            { name: 'Hep-B-4', desc: 'Hepatitis B (if needed)' },
        ]
    },
    {
        age: '9 Months', vaccines: [
            { name: 'MR/MMR-1', desc: 'Measles, Mumps, Rubella' },
            { name: 'OPV-2', desc: 'Oral Polio Vaccine' },
            { name: 'PCV Booster', desc: 'Pneumococcal Booster' },
        ]
    },
    {
        age: '12 Months', vaccines: [
            { name: 'Hep-A-1', desc: 'Hepatitis A' },
        ]
    },
    {
        age: '15 Months', vaccines: [
            { name: 'MR/MMR-2', desc: 'Measles, Mumps, Rubella' },
            { name: 'Varicella-1', desc: 'Chickenpox Vaccine' },
        ]
    },
];

export default function VaccinationCalendarScreen({ route }) {
    const { childId: initialChildId } = route?.params || {};
    const [childId, setChildId] = useState(initialChildId);
    const { user } = useAuth();
    const [children, setChildren] = useState([]);
    const { t } = useTranslation();
    const { theme } = useTheme();
    const [doneMap, setDoneMap] = useState({});
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
                    const { data: cData } = await supabase.from('children').select('id, name, gender, birth_date').in('mother_id', mIds);
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
        const fetchVaccines = async () => {
            setLoading(true);
            try {
                const { data, error } = await supabase
                    .from('vaccinations')
                    .select('vaccine_name, status')
                    .eq('child_id', childId)
                    .eq('status', 'completed');

                if (!error && data) {
                    const mapped = {};
                    data.forEach(v => {
                        // Find the index in our schedule
                        schedule.forEach((group, gi) => {
                            group.vaccines.forEach((vac, vi) => {
                                if (vac.name === v.vaccine_name) {
                                    mapped[`${gi}-${vi}`] = true;
                                }
                            });
                        });
                    });
                    setDoneMap(mapped);
                }
            } catch (err) {
                console.error("Error fetching vaccines:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchVaccines();
    }, [childId]);

    const toggleDone = async (ageIdx, vacIdx) => {
        if (!childId) return;
        const key = `${ageIdx}-${vacIdx}`;
        const vacName = schedule[ageIdx].vaccines[vacIdx].name;
        const isCurrentlyDone = doneMap[key];

        // Optimistic update
        setDoneMap((prev) => ({ ...prev, [key]: !isCurrentlyDone }));

        try {
            if (!isCurrentlyDone) {
                const today = new Date().toISOString().split('T')[0]; // date-only YYYY-MM-DD
                // Mark done - include all required columns
                await supabase.from('vaccinations').insert({
                    child_id: childId,
                    vaccine_name: vacName,
                    vaccine_category: 'primary',
                    recommended_age_days: 0,
                    status: 'completed',
                    administered_date: today,
                    due_date: today,
                    created_at: new Date().toISOString(),
                });
            } else {
                // Mark pending/delete
                await supabase.from('vaccinations')
                    .delete()
                    .eq('child_id', childId)
                    .eq('vaccine_name', vacName);
            }
        } catch (e) {
            console.error("Error updating vaccine:", e);
            // Revert
            setDoneMap((prev) => ({ ...prev, [key]: isCurrentlyDone }));
        }
    };

    return (
        <ScrollView style={[styles.container, { backgroundColor: theme.background }]}>
            <View style={styles.content}>
                <Text style={[typography.h3, { color: theme.text, marginBottom: spacing.sm }]}>
                    {t('vaccination_calendar')}
                </Text>

                {/* Child Dropdown Selector */}
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
                                    {children.find(c => c.id === childId)?.name || 'Select a child'}
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
                    IAP 2023 Immunization Schedule
                </Text>

                {schedule.map((group, gi) => (
                    <View key={gi} style={{ marginBottom: spacing.xl }}>
                        <View style={styles.ageHeader}>
                            <View style={[styles.ageDot, { backgroundColor: theme.primary }]} />
                            <Text style={[typography.bodyBold, { color: theme.primary }]}>{group.age}</Text>
                        </View>
                        {group.vaccines.map((v, vi) => {
                            const key = `${gi}-${vi}`;
                            const done = doneMap[key];
                            return (
                                <TouchableOpacity
                                    key={vi}
                                    style={[styles.vaccineRow, { backgroundColor: theme.surface, borderColor: done ? theme.success : theme.border }]}
                                    onPress={() => toggleDone(gi, vi)}
                                    activeOpacity={0.7}
                                >
                                    <View style={[styles.checkbox, done && { backgroundColor: theme.success, borderColor: theme.success }]}>
                                        {done && <Ionicons name="checkmark" size={14} color="#fff" />}
                                    </View>
                                    <View style={{ flex: 1, marginLeft: spacing.md }}>
                                        <Text style={[typography.smallBold, { color: theme.text, textDecorationLine: done ? 'line-through' : 'none' }]}>
                                            {v.name}
                                        </Text>
                                        <Text style={[typography.caption, { color: theme.textTertiary }]}>{v.desc}</Text>
                                    </View>
                                    {done && <Ionicons name="checkmark-circle" size={20} color={theme.success} />}
                                </TouchableOpacity>
                            );
                        })}
                    </View>
                ))}
            </View>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1 },
    content: { padding: spacing.screenPadding, paddingTop: spacing.xl, paddingBottom: 100 },
    ageHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.md },
    ageDot: { width: 10, height: 10, borderRadius: 5, marginRight: spacing.sm },
    vaccineRow: {
        flexDirection: 'row', alignItems: 'center',
        padding: spacing.md, borderRadius: borderRadius.md, borderWidth: 1,
        marginBottom: spacing.sm, marginLeft: spacing.lg,
    },
    checkbox: {
        width: 22, height: 22, borderRadius: 6, borderWidth: 2,
        borderColor: '#CBD5E1', justifyContent: 'center', alignItems: 'center',
    },
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
