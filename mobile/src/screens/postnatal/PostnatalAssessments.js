// Postnatal Assessments Screen
import React, { useState, useEffect } from 'react';
import {
    View, Text, ScrollView, TouchableOpacity, TextInput, StyleSheet, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';
import { supabase } from '../../services/auth';
import { typography, spacing, borderRadius } from '../../theme';
import { postnatalAPI } from '../../services/api';

export default function PostnatalAssessmentsScreen({ route }) {
    const { childId: routeChildId, motherId: routeMotherId } = route?.params || {};
    const { t } = useTranslation();
    const { theme } = useTheme();
    const [tab, setTab] = useState(routeChildId ? 'child' : 'mother'); // mother | child
    const [form, setForm] = useState({
        temperature: '', bloodPressure: '', pulse: '',
        lochiaColor: '', lochiaAmount: '',
        breastfeedingStatus: '', moodScore: '',
        childWeight: '', childTemp: '', feedingType: '', stools: '',
        notes: '',
    });
    const { user } = useAuth();
    const [mothers, setMothers] = useState([]);
    const [children, setChildren] = useState([]);
    const [selectedMotherId, setSelectedMotherId] = useState(routeMotherId || null);
    const [selectedChildId, setSelectedChildId] = useState(routeChildId || null);
    const [submitting, setSubmitting] = useState(false);
    const [dropdownOpen, setDropdownOpen] = useState(false);

    useEffect(() => {
        if (!user?.id) return;
        const loadMothersAndChildren = async () => {
            try {
                let mQuery = supabase.from('mothers').select('id, name').eq('delivery_status', 'delivered');
                if (user.role === 'ASHA_WORKER') {
                    const { data: asha } = await supabase.from('asha_workers').select('id').eq('user_id', user.id).maybeSingle();
                    if (asha) mQuery = mQuery.eq('asha_worker_id', asha.id);
                } else if (user.role === 'DOCTOR') {
                    const { data: doc } = await supabase.from('doctors').select('id').eq('user_profile_id', user.id).maybeSingle();
                    if (doc) mQuery = mQuery.eq('doctor_id', doc.id);
                }
                const { data: mData } = await mQuery;
                if (mData) {
                    setMothers(mData);
                    if (mData.length > 0) {
                        const mIds = mData.map(m => m.id);
                        const { data: cData } = await supabase.from('children').select('id, name, mother_id, gender').in('mother_id', mIds);
                        if (cData) setChildren(cData);
                    }
                }
            } catch (err) {
                console.error("Error loading target selection for assessments", err);
            }
        };
        loadMothersAndChildren();
    }, [user?.id]);

    const handleSubmit = async () => {
        if (tab === 'mother' && !selectedMotherId) return Alert.alert('Error', 'Please select a mother');
        if (tab === 'child' && !selectedChildId) return Alert.alert('Error', 'Please select a child');
        try {
            setSubmitting(true);
            const parentMotherId = tab === 'child' ? children.find(c => c.id === selectedChildId)?.mother_id : selectedMotherId;

            await postnatalAPI.createAssessment({
                type: tab,
                mother_id: parentMotherId,
                child_id: tab === 'child' ? selectedChildId : undefined,
                ...form,
            });
            Alert.alert('Success', 'Assessment recorded successfully');
            setForm({
                temperature: '', bloodPressure: '', pulse: '',
                lochiaColor: '', lochiaAmount: '',
                breastfeedingStatus: '', moodScore: '',
                childWeight: '', childTemp: '', feedingType: '', stools: '',
                notes: '',
            });
        } catch (e) {
            Alert.alert('Error', e.message || 'Failed to submit assessment');
        } finally { setSubmitting(false); }
    };

    const motherFields = [
        { key: 'temperature', label: 'Temperature (°C)', icon: 'thermometer-outline', keyboard: 'decimal-pad' },
        { key: 'bloodPressure', label: 'Blood Pressure', icon: 'heart-outline', placeholder: '120/80' },
        { key: 'pulse', label: 'Pulse (bpm)', icon: 'pulse-outline', keyboard: 'number-pad' },
        { key: 'lochiaColor', label: 'Lochia Color', icon: 'color-palette-outline', placeholder: 'Red / Pink / Yellow' },
        { key: 'lochiaAmount', label: 'Lochia Amount', icon: 'water-outline', placeholder: 'Heavy / Moderate / Light' },
        { key: 'breastfeedingStatus', label: 'Breastfeeding Status', icon: 'nutrition-outline', placeholder: 'Good / Issues' },
        { key: 'moodScore', label: 'Mood Score (1-10)', icon: 'happy-outline', keyboard: 'number-pad' },
    ];

    const childFields = [
        { key: 'childWeight', label: 'Weight (kg)', icon: 'scale-outline', keyboard: 'decimal-pad' },
        { key: 'childTemp', label: 'Temperature (°C)', icon: 'thermometer-outline', keyboard: 'decimal-pad' },
        { key: 'feedingType', label: 'Feeding Type', icon: 'nutrition-outline', placeholder: 'Breast / Formula / Mixed' },
        { key: 'stools', label: 'Stools (freq/day)', icon: 'analytics-outline', keyboard: 'number-pad' },
    ];

    const fields = tab === 'mother' ? motherFields : childFields;

    return (
        <ScrollView style={[styles.container, { backgroundColor: theme.background }]}>
            <View style={styles.content}>
                <Text style={[typography.h3, { color: theme.text, marginBottom: spacing.base }]}>
                    {t('assessments')}
                </Text>

                {/* Tab Toggle */}
                <View style={[styles.tabBar, { backgroundColor: theme.surfaceElevated }]}>
                    {['mother', 'child'].map((tb) => (
                        <TouchableOpacity
                            key={tb}
                            style={[styles.tabBtn, tab === tb && { backgroundColor: theme.primary }]}
                            onPress={() => { setTab(tb); setDropdownOpen(false); }}
                        >
                            <Ionicons name={tb === 'mother' ? 'heart' : 'happy'} size={16} color={tab === tb ? '#fff' : theme.textSecondary} />
                            <Text style={[typography.smallBold, { color: tab === tb ? '#fff' : theme.textSecondary, marginLeft: 4 }]}>
                                {tb === 'mother' ? 'Mother' : 'Child'}
                            </Text>
                        </TouchableOpacity>
                    ))}
                </View>

                {/* Dropdown Target Selection */}
                <Text style={[typography.smallBold, { color: theme.textSecondary, marginBottom: spacing.sm }]}>
                    Select {tab === 'mother' ? 'Mother' : 'Child'} for Assessment
                </Text>
                <View style={{ marginBottom: spacing.xl, zIndex: 10 }}>
                    <TouchableOpacity
                        style={[styles.dropdown, { backgroundColor: theme.surface, borderColor: theme.border }]}
                        onPress={() => setDropdownOpen(!dropdownOpen)}
                        activeOpacity={0.7}
                    >
                        <View style={{ flexDirection: 'row', alignItems: 'center', flex: 1 }}>
                            <View style={[styles.dropdownAvatar, { backgroundColor: tab === 'mother' ? theme.primary + '20' : theme.info + '20' }]}>
                                <Ionicons name={tab === 'mother' ? 'heart' : 'happy'} size={18} color={tab === 'mother' ? theme.primary : theme.info} />
                            </View>
                            <Text style={[typography.body, { color: theme.text, marginLeft: spacing.sm }]}>
                                {tab === 'mother'
                                    ? (mothers.find(m => m.id === selectedMotherId)?.name || 'Select a mother')
                                    : (children.find(c => c.id === selectedChildId)?.name || 'Select a child')
                                }
                            </Text>
                        </View>
                        <Ionicons name={dropdownOpen ? 'chevron-up' : 'chevron-down'} size={20} color={theme.textSecondary} />
                    </TouchableOpacity>

                    {dropdownOpen && (
                        <View style={[styles.dropdownList, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                            {tab === 'mother' ? (
                                mothers.map(m => (
                                    <TouchableOpacity
                                        key={m.id}
                                        style={[
                                            styles.dropdownItem,
                                            { borderBottomColor: theme.border },
                                            selectedMotherId === m.id && { backgroundColor: theme.primary + '15' }
                                        ]}
                                        onPress={() => { setSelectedMotherId(m.id); setDropdownOpen(false); }}
                                    >
                                        <View style={[styles.dropdownAvatar, { backgroundColor: theme.primary + '20' }]}>
                                            <Ionicons name="heart" size={16} color={theme.primary} />
                                        </View>
                                        <Text style={[typography.body, { color: theme.text, marginLeft: spacing.sm, flex: 1 }]}>
                                            {m.name || 'Unknown'}
                                        </Text>
                                        {selectedMotherId === m.id && <Ionicons name="checkmark-circle" size={20} color={theme.primary} />}
                                    </TouchableOpacity>
                                ))
                            ) : (
                                children.map(c => (
                                    <TouchableOpacity
                                        key={c.id}
                                        style={[
                                            styles.dropdownItem,
                                            { borderBottomColor: theme.border },
                                            selectedChildId === c.id && { backgroundColor: theme.info + '15' }
                                        ]}
                                        onPress={() => { setSelectedChildId(c.id); setDropdownOpen(false); }}
                                    >
                                        <View style={[styles.dropdownAvatar, { backgroundColor: c.gender === 'male' ? '#DBEAFE' : '#FCE7F3' }]}>
                                            <Text style={{ fontSize: 14 }}>{c.gender === 'male' ? '♂' : '♀'}</Text>
                                        </View>
                                        <Text style={[typography.body, { color: theme.text, marginLeft: spacing.sm, flex: 1 }]}>
                                            {c.name || 'Baby'}
                                        </Text>
                                        {selectedChildId === c.id && <Ionicons name="checkmark-circle" size={20} color={theme.info} />}
                                    </TouchableOpacity>
                                ))
                            )}
                        </View>
                    )}
                </View>

                {/* Form Fields */}
                {fields.map((f) => (
                    <View key={f.key} style={styles.fieldWrap}>
                        <Text style={[typography.smallBold, { color: theme.text, marginBottom: spacing.xs }]}>{f.label}</Text>
                        <View style={[styles.inputWrap, { backgroundColor: theme.surfaceElevated, borderColor: theme.border }]}>
                            <Ionicons name={f.icon} size={18} color={theme.textTertiary} />
                            <TextInput
                                style={[styles.input, { color: theme.text }]}
                                placeholder={f.placeholder || f.label}
                                placeholderTextColor={theme.textTertiary}
                                value={form[f.key]}
                                onChangeText={(v) => setForm((p) => ({ ...p, [f.key]: v }))}
                                keyboardType={f.keyboard || 'default'}
                            />
                        </View>
                    </View>
                ))}

                {/* Notes */}
                <View style={styles.fieldWrap}>
                    <Text style={[typography.smallBold, { color: theme.text, marginBottom: spacing.xs }]}>Notes</Text>
                    <TextInput
                        style={[styles.textArea, { backgroundColor: theme.surfaceElevated, borderColor: theme.border, color: theme.text }]}
                        placeholder="Additional observations..."
                        placeholderTextColor={theme.textTertiary}
                        value={form.notes}
                        onChangeText={(v) => setForm((p) => ({ ...p, notes: v }))}
                        multiline
                        numberOfLines={4}
                    />
                </View>

                <TouchableOpacity
                    style={[styles.submitBtn, { backgroundColor: theme.primary, opacity: submitting ? 0.6 : 1 }]}
                    onPress={handleSubmit}
                    disabled={submitting}
                    activeOpacity={0.8}
                >
                    <Ionicons name="save-outline" size={20} color="#fff" />
                    <Text style={styles.submitText}>{submitting ? 'Saving...' : t('submit')}</Text>
                </TouchableOpacity>
            </View>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1 },
    content: { padding: spacing.screenPadding, paddingTop: spacing.xl, paddingBottom: 100 },
    tabBar: { flexDirection: 'row', borderRadius: borderRadius.md, padding: 4, marginBottom: spacing.xl },
    tabBtn: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 10, borderRadius: borderRadius.sm },
    fieldWrap: { marginBottom: spacing.base },
    inputWrap: {
        flexDirection: 'row', alignItems: 'center',
        paddingHorizontal: spacing.base, paddingVertical: 12,
        borderRadius: borderRadius.md, borderWidth: 1, gap: 10,
    },
    input: { flex: 1, fontSize: 15 },
    textArea: { padding: spacing.base, borderRadius: borderRadius.md, borderWidth: 1, fontSize: 15, minHeight: 80, textAlignVertical: 'top' },
    submitBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 16, borderRadius: borderRadius.md, gap: 8, marginTop: spacing.md },
    submitText: { color: '#fff', fontSize: 16, fontWeight: '700' },
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
