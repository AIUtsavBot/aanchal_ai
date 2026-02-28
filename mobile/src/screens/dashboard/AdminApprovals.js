// Admin Approvals Screen
import React, { useState, useEffect } from 'react';
import {
    View, Text, ScrollView, TouchableOpacity, StyleSheet, Alert, RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../contexts/ThemeContext';
import { typography, spacing, borderRadius } from '../../theme';
import { authAPI } from '../../services/api';
import { LoadingSpinner, EmptyState } from '../../components/shared';

export default function AdminApprovalsScreen() {
    const { t } = useTranslation();
    const { theme } = useTheme();
    const [requests, setRequests] = useState([]);
    const [roleRequests, setRoleRequests] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    const loadData = async () => {
        try {
            const [reqs, roles] = await Promise.all([
                authAPI.listRegisterRequests().catch(() => []),
                authAPI.listRoleRequests().catch(() => []),
            ]);
            setRequests(Array.isArray(reqs) ? reqs : []);
            setRoleRequests(Array.isArray(roles) ? roles : []);
        } finally { setLoading(false); }
    };

    useEffect(() => { loadData(); }, []);

    const onRefresh = async () => { setRefreshing(true); await loadData(); setRefreshing(false); };

    const handleApprove = async (id, type) => {
        Alert.alert('Approve', 'Approve this request?', [
            { text: t('cancel'), style: 'cancel' },
            {
                text: t('approve'), onPress: async () => {
                    try {
                        if (type === 'register') await authAPI.decideRegisterRequest(id, true, 'Approved');
                        else await authAPI.approveRoleRequest(id);
                        await loadData();
                    } catch (e) { Alert.alert('Error', e.message); }
                }
            },
        ]);
    };

    const handleReject = async (id, type) => {
        Alert.alert('Reject', 'Reject this request?', [
            { text: t('cancel'), style: 'cancel' },
            {
                text: t('reject'), style: 'destructive', onPress: async () => {
                    try {
                        if (type === 'register') await authAPI.decideRegisterRequest(id, false, 'Rejected');
                        else await authAPI.rejectRoleRequest(id, 'Rejected');
                        await loadData();
                    } catch (e) { Alert.alert('Error', e.message); }
                }
            },
        ]);
    };

    if (loading) return <LoadingSpinner />;

    const allRequests = [
        ...requests.map((r) => ({ ...r, _type: 'register' })),
        ...roleRequests.map((r) => ({ ...r, _type: 'role' })),
    ];

    return (
        <ScrollView
            style={[styles.container, { backgroundColor: theme.background }]}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.primary} />}
        >
            <View style={[styles.header, { backgroundColor: theme.primary }]}>
                <Text style={styles.headerTitle}>{t('approvals')}</Text>
                <Text style={styles.headerSub}>{allRequests.length} pending</Text>
            </View>

            <View style={styles.content}>
                {allRequests.length === 0 ? (
                    <EmptyState icon="checkmark-done-circle-outline" title="All caught up!" message="No pending approvals" />
                ) : (
                    allRequests.map((req, i) => (
                        <View key={req.id || i} style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                            <View style={styles.cardTop}>
                                <View style={[styles.roleTag, { backgroundColor: theme.primary + '15' }]}>
                                    <Ionicons
                                        name={req.role === 'DOCTOR' ? 'medkit-outline' : 'people-outline'}
                                        size={16}
                                        color={theme.primary}
                                    />
                                    <Text style={[typography.captionBold, { color: theme.primary, marginLeft: 4 }]}>
                                        {req.role || 'Pending'}
                                    </Text>
                                </View>
                                <Text style={[typography.caption, { color: theme.textTertiary }]}>
                                    {req.created_at ? new Date(req.created_at).toLocaleDateString() : ''}
                                </Text>
                            </View>
                            <Text style={[typography.bodyBold, { color: theme.text, marginTop: spacing.sm }]}>
                                {req.full_name || req.email || 'Unknown'}
                            </Text>
                            <Text style={[typography.small, { color: theme.textSecondary }]}>{req.email || ''}</Text>

                            <View style={styles.actions}>
                                <TouchableOpacity
                                    style={[styles.actionBtn, { backgroundColor: theme.success }]}
                                    onPress={() => handleApprove(req.id, req._type)}
                                >
                                    <Ionicons name="checkmark" size={18} color="#fff" />
                                    <Text style={styles.actionText}>{t('approve')}</Text>
                                </TouchableOpacity>
                                <TouchableOpacity
                                    style={[styles.actionBtn, { backgroundColor: theme.error }]}
                                    onPress={() => handleReject(req.id, req._type)}
                                >
                                    <Ionicons name="close" size={18} color="#fff" />
                                    <Text style={styles.actionText}>{t('reject')}</Text>
                                </TouchableOpacity>
                            </View>
                        </View>
                    ))
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
    card: { borderRadius: borderRadius.lg, borderWidth: 1, padding: spacing.base, marginBottom: spacing.md },
    cardTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
    roleTag: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
    actions: { flexDirection: 'row', marginTop: spacing.base, gap: 10 },
    actionBtn: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 10, borderRadius: borderRadius.md, gap: 4 },
    actionText: { color: '#fff', fontWeight: '600', fontSize: 14 },
});
