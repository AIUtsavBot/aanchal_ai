// Postnatal Dashboard
import React from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../contexts/ThemeContext';
import { typography, spacing, borderRadius } from '../../theme';

const sections = [
    { key: 'MothersList', icon: 'heart-outline', color: '#EC4899', title: 'Mother Registry', desc: 'View & manage all mothers' },
    { key: 'ChildrenList', icon: 'people-outline', color: '#0D9488', title: 'Children Registry', desc: 'View & manage all children' },
    { key: 'GrowthCharts', icon: 'trending-up-outline', color: '#10B981', title: 'Growth Charts', desc: 'WHO z-score tracking' },
    { key: 'VaccinationCalendar', icon: 'calendar-outline', color: '#3B82F6', title: 'Vaccination Calendar', desc: 'IAP 2023 schedule' },
    { key: 'MilestonesTracker', icon: 'flag-outline', color: '#F97316', title: 'Milestones Tracker', desc: 'Developmental milestones' },
    { key: 'PostnatalAssessments', icon: 'clipboard-outline', color: '#0d9488', title: 'New Assessment', desc: 'Create mother & child health checks' },
];

export default function PostnatalDashboardScreen({ navigation }) {
    const { t } = useTranslation();
    const { theme } = useTheme();

    return (
        <ScrollView style={[styles.container, { backgroundColor: theme.background }]}>
            <View style={[styles.header, { backgroundColor: theme.primary }]}>
                <Text style={styles.headerTitle}>Postnatal Care</Text>
                <Text style={styles.headerSub}>Complete postnatal care management</Text>
            </View>
            <View style={styles.content}>
                {sections.map((s) => (
                    <TouchableOpacity
                        key={s.key}
                        style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}
                        onPress={() => navigation.navigate(s.key)}
                        activeOpacity={0.7}
                    >
                        <View style={[styles.iconWrap, { backgroundColor: s.color + '15' }]}>
                            <Ionicons name={s.icon} size={28} color={s.color} />
                        </View>
                        <View style={{ flex: 1, marginLeft: spacing.base }}>
                            <Text style={[typography.bodyBold, { color: theme.text }]}>{s.title}</Text>
                            <Text style={[typography.caption, { color: theme.textSecondary }]}>{s.desc}</Text>
                        </View>
                        <Ionicons name="chevron-forward" size={20} color={theme.textTertiary} />
                    </TouchableOpacity>
                ))}
            </View>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1 },
    header: { paddingTop: 54, paddingBottom: 20, paddingHorizontal: spacing.screenPadding },
    headerTitle: { color: '#fff', fontSize: 22, fontWeight: '700' },
    headerSub: { color: 'rgba(255,255,255,0.8)', fontSize: 14, marginTop: 4 },
    content: { padding: spacing.screenPadding, paddingBottom: 100 },
    card: {
        flexDirection: 'row', alignItems: 'center',
        padding: spacing.base, borderRadius: borderRadius.lg,
        borderWidth: 1, marginBottom: spacing.md,
    },
    iconWrap: { width: 52, height: 52, borderRadius: 26, justifyContent: 'center', alignItems: 'center' },
});
