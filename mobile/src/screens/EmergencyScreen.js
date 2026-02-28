// Emergency Screen
import React, { useState } from 'react';
import {
    View, Text, ScrollView, TouchableOpacity, TextInput, StyleSheet, Alert, Linking,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../contexts/ThemeContext';
import { typography, spacing, borderRadius } from '../theme';

const symptoms = [
    'Heavy bleeding', 'Severe headache', 'High fever (>101°F)',
    'Seizures/Convulsions', 'Severe abdominal pain', 'Difficulty breathing',
    'Loss of consciousness', 'Blurred vision', 'Reduced fetal movement',
    'Water breaking', 'Cord prolapse', 'Chest pain',
];

const emergencyContacts = [
    { name: 'Ambulance', number: '102', icon: 'car-outline', color: '#EF4444' },
    { name: 'Emergency', number: '112', icon: 'call-outline', color: '#F97316' },
    { name: 'Women Helpline', number: '181', icon: 'people-outline', color: '#8B5CF6' },
];

export default function EmergencyScreen() {
    const { t } = useTranslation();
    const { theme } = useTheme();
    const [selectedSymptoms, setSelectedSymptoms] = useState([]);
    const [motherName, setMotherName] = useState('');
    const [alertSent, setAlertSent] = useState(false);

    const toggleSymptom = (s) => {
        setSelectedSymptoms((prev) =>
            prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]
        );
    };

    const triggerAlert = () => {
        if (!selectedSymptoms.length) {
            Alert.alert('Select Symptoms', 'Please select at least one symptom');
            return;
        }
        Alert.alert(
            '🚨 Emergency Alert',
            'This will trigger an emergency alert. Continue?',
            [
                { text: t('cancel'), style: 'cancel' },
                {
                    text: 'SEND ALERT',
                    style: 'destructive',
                    onPress: () => {
                        setAlertSent(true);
                        setTimeout(() => setAlertSent(false), 5000);
                    },
                },
            ]
        );
    };

    const callNumber = (number) => {
        Linking.openURL(`tel:${number}`);
    };

    return (
        <ScrollView style={[styles.container, { backgroundColor: theme.background }]}>
            {/* Header */}
            <View style={styles.header}>
                <Ionicons name="warning" size={32} color="#fff" />
                <Text style={styles.headerTitle}>{t('emergency_response')}</Text>
                <Text style={styles.headerSub}>24/7 Emergency Support</Text>
            </View>

            {alertSent && (
                <View style={[styles.alertBanner, { backgroundColor: theme.successLight }]}>
                    <Ionicons name="checkmark-circle" size={24} color={theme.success} />
                    <View style={{ marginLeft: spacing.md, flex: 1 }}>
                        <Text style={[typography.bodyBold, { color: theme.success }]}>{t('emergency_alert_sent')}</Text>
                        <Text style={[typography.caption, { color: theme.success }]}>
                            Ambulance is on the way. Hospital has been notified.
                        </Text>
                    </View>
                </View>
            )}

            <View style={styles.content}>
                {/* Mother's Name */}
                <Text style={[typography.smallBold, { color: theme.text, marginBottom: spacing.xs }]}>
                    Mother's Name
                </Text>
                <View style={[styles.inputWrap, { backgroundColor: theme.surfaceElevated, borderColor: theme.border }]}>
                    <Ionicons name="person-outline" size={18} color={theme.textTertiary} />
                    <TextInput
                        style={[styles.input, { color: theme.text }]}
                        placeholder="Enter mother's name"
                        placeholderTextColor={theme.textTertiary}
                        value={motherName}
                        onChangeText={setMotherName}
                    />
                </View>

                {/* Symptom Selection */}
                <Text style={[typography.h4, { color: theme.text, marginTop: spacing.xl, marginBottom: spacing.md }]}>
                    Select Symptoms
                </Text>
                <View style={styles.symptomsGrid}>
                    {symptoms.map((s) => {
                        const selected = selectedSymptoms.includes(s);
                        return (
                            <TouchableOpacity
                                key={s}
                                style={[
                                    styles.symptomChip,
                                    { borderColor: selected ? theme.error : theme.border },
                                    selected && { backgroundColor: theme.errorLight },
                                ]}
                                onPress={() => toggleSymptom(s)}
                                activeOpacity={0.7}
                            >
                                {selected && <Ionicons name="checkmark-circle" size={16} color={theme.error} style={{ marginRight: 4 }} />}
                                <Text style={[typography.caption, { color: selected ? theme.error : theme.text }]}>{s}</Text>
                            </TouchableOpacity>
                        );
                    })}
                </View>

                {/* Trigger Button */}
                <TouchableOpacity style={styles.alertBtn} onPress={triggerAlert} activeOpacity={0.8}>
                    <Ionicons name="alert-circle" size={24} color="#fff" />
                    <Text style={styles.alertBtnText}>{t('trigger_emergency_alert')}</Text>
                </TouchableOpacity>

                {/* Emergency Contacts */}
                <Text style={[typography.h4, { color: theme.text, marginTop: spacing.xxl, marginBottom: spacing.md }]}>
                    {t('emergency_contacts')}
                </Text>
                {emergencyContacts.map((c) => (
                    <TouchableOpacity
                        key={c.number}
                        style={[styles.contactCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
                        onPress={() => callNumber(c.number)}
                        activeOpacity={0.7}
                    >
                        <View style={[styles.contactIcon, { backgroundColor: c.color + '15' }]}>
                            <Ionicons name={c.icon} size={22} color={c.color} />
                        </View>
                        <View style={{ flex: 1, marginLeft: spacing.md }}>
                            <Text style={[typography.bodyBold, { color: theme.text }]}>{c.name}</Text>
                            <Text style={[typography.small, { color: theme.textSecondary }]}>{c.number}</Text>
                        </View>
                        <View style={[styles.callBtn, { backgroundColor: c.color }]}>
                            <Ionicons name="call" size={18} color="#fff" />
                        </View>
                    </TouchableOpacity>
                ))}
            </View>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1 },
    header: {
        backgroundColor: '#DC2626', paddingTop: 54, paddingBottom: 20,
        paddingHorizontal: spacing.screenPadding, alignItems: 'center',
    },
    headerTitle: { color: '#fff', fontSize: 22, fontWeight: '700', marginTop: 8 },
    headerSub: { color: 'rgba(255,255,255,0.9)', fontSize: 14, marginTop: 4 },
    alertBanner: { flexDirection: 'row', alignItems: 'center', margin: spacing.screenPadding, padding: spacing.base, borderRadius: borderRadius.lg },
    content: { padding: spacing.screenPadding, paddingBottom: 100 },
    inputWrap: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: spacing.base, paddingVertical: 12, borderRadius: borderRadius.md, borderWidth: 1, gap: 10 },
    input: { flex: 1, fontSize: 15 },
    symptomsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
    symptomChip: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: borderRadius.full, borderWidth: 1, flexDirection: 'row', alignItems: 'center' },
    alertBtn: {
        flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
        backgroundColor: '#DC2626', paddingVertical: 18, borderRadius: borderRadius.md,
        marginTop: spacing.xl, gap: 10,
        shadowColor: '#DC2626', shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3, shadowRadius: 8, elevation: 6,
    },
    alertBtnText: { color: '#fff', fontSize: 16, fontWeight: '800', letterSpacing: 0.5 },
    contactCard: { flexDirection: 'row', alignItems: 'center', padding: spacing.base, borderRadius: borderRadius.lg, borderWidth: 1, marginBottom: spacing.md },
    contactIcon: { width: 44, height: 44, borderRadius: 22, justifyContent: 'center', alignItems: 'center' },
    callBtn: { width: 38, height: 38, borderRadius: 19, justifyContent: 'center', alignItems: 'center' },
});
