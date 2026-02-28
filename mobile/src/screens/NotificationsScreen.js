// Notifications Screen
import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../contexts/ThemeContext';
import { typography, spacing, borderRadius } from '../theme';
import { EmptyState } from '../components/shared';

export default function NotificationsScreen() {
    const { t } = useTranslation();
    const { theme } = useTheme();
    const [notifications, setNotifications] = useState([
        { id: 1, title: 'New Assessment', message: 'A high-risk assessment was recorded for Swati Patel.', time: '2 hours ago', read: false, type: 'alert' },
        { id: 2, title: 'Upcoming Consultation', message: 'You have a consultation scheduled with Priya Sharma tomorrow at 10:00 AM.', time: '5 hours ago', read: false, type: 'calendar' },
        { id: 3, title: 'System Update', message: 'The Aanchal AI mobile app has been updated to version 1.1 with new Postnatal features.', time: '1 day ago', read: true, type: 'information' },
    ]);

    const markAsRead = (id) => {
        setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
    };

    const getIconInfo = (type) => {
        switch (type) {
            case 'alert': return { icon: 'warning', color: '#EF4444' };
            case 'calendar': return { icon: 'calendar', color: '#3B82F6' };
            default: return { icon: 'information-circle', color: '#0d9488' };
        }
    };

    return (
        <ScrollView style={[styles.container, { backgroundColor: theme.background }]}>
            <View style={[styles.header, { backgroundColor: theme.primary }]}>
                <Text style={styles.headerTitle}>Notifications</Text>
                <Text style={styles.headerSub}>Stay updated with alerts and messages</Text>
            </View>

            <View style={styles.content}>
                {notifications.length > 0 ? (
                    notifications.map((n) => {
                        const iconInfo = getIconInfo(n.type);
                        return (
                            <TouchableOpacity
                                key={n.id}
                                style={[
                                    styles.card,
                                    { backgroundColor: n.read ? theme.surface : theme.surfaceElevated, borderColor: theme.border },
                                    !n.read && { borderLeftWidth: 4, borderLeftColor: theme.primary }
                                ]}
                                onPress={() => markAsRead(n.id)}
                            >
                                <View style={[styles.iconWrap, { backgroundColor: iconInfo.color + '15' }]}>
                                    <Ionicons name={iconInfo.icon} size={24} color={iconInfo.color} />
                                </View>
                                <View style={{ flex: 1, marginLeft: spacing.md }}>
                                    <Text style={[typography.bodyBold, { color: theme.text }]}>{n.title}</Text>
                                    <Text style={[typography.caption, { color: theme.textSecondary, marginTop: 4 }]} numberOfLines={2}>
                                        {n.message}
                                    </Text>
                                    <Text style={[typography.caption, { color: theme.textTertiary, marginTop: 6 }]}>{n.time}</Text>
                                </View>
                                {!n.read && <View style={[styles.unreadDot, { backgroundColor: theme.primary }]} />}
                            </TouchableOpacity>
                        );
                    })
                ) : (
                    <EmptyState icon="notifications-off-outline" title="No Notifications" message="You're all caught up!" />
                )}
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
        flexDirection: 'row', alignItems: 'flex-start',
        padding: spacing.base, borderRadius: borderRadius.lg,
        borderWidth: 1, marginBottom: spacing.md,
    },
    iconWrap: { width: 44, height: 44, borderRadius: 22, justifyContent: 'center', alignItems: 'center' },
    unreadDot: { width: 10, height: 10, borderRadius: 5, marginTop: spacing.sm },
});
