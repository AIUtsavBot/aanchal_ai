// Doctor Dashboard Screen
import React, { useState, useEffect, useCallback } from 'react';
import {
    View, Text, ScrollView, TouchableOpacity, TextInput, StyleSheet, RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';
import { supabase } from '../../services/auth';
import { typography, spacing, borderRadius } from '../../theme';
import { motherAPI, riskAPI, queryAgent } from '../../services/api';
import { PatientCard, StatCard, EmptyState, LoadingSpinner } from '../../components/shared';

export default function DoctorDashboardScreen() {
    const { t } = useTranslation();
    const { theme } = useTheme();
    const { user } = useAuth();
    const [mothers, setMothers] = useState([]);
    const [selectedMother, setSelectedMother] = useState(null);
    const [activeTab, setActiveTab] = useState('chat'); // 'history', 'documents', 'chat', 'consultation'
    const [messages, setMessages] = useState([]);
    const [loadingChat, setLoadingChat] = useState(false);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(true);
    const [sending, setSending] = useState(false);
    const [refreshing, setRefreshing] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [assessments, setAssessments] = useState([]);
    const [loadingAssessments, setLoadingAssessments] = useState(false);
    const [documents, setDocuments] = useState([]);

    const loadMotherDetails = async (motherId) => {
        setLoadingAssessments(true);
        try {
            // 1. Fetch AI/ASHA Risk Assessments
            let riskData = [];
            try {
                const { data } = await supabase
                    .from('risk_assessments')
                    .select('*')
                    .eq('mother_id', motherId)
                    .order('created_at', { ascending: false });
                if (data) riskData = data;
            } catch (e) { console.warn('risk_assessments query failed:', e); }

            // 2. Fetch Doctor Consultations from postnatal_assessments
            let consultationData = [];
            try {
                const { data } = await supabase
                    .from('postnatal_assessments')
                    .select('*')
                    .eq('mother_id', motherId)
                    .order('assessment_date', { ascending: false });
                if (data) consultationData = data;
            } catch (e) { console.warn('postnatal_assessments query failed:', e); }

            const combined = [];
            if (riskData) combined.push(...riskData.map(item => ({ ...item, type: 'risk_assessment' })));
            if (consultationData) combined.push(...consultationData.map(item => ({
                ...item, type: 'consultation', created_at: item.assessment_date || item.created_at, risk_level: item.overall_risk_level || 'CONSULTATION',
            })));

            combined.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
            setAssessments(combined);

            // 3. Fetch Documents (Medical Reports)
            let reportsData = [];
            try {
                const { data } = await supabase
                    .from('medical_reports')
                    .select('*')
                    .eq('mother_id', motherId)
                    .order('created_at', { ascending: false });
                if (data) reportsData = data;
            } catch (e) {
                console.warn('medical_reports query failed, trying upload_date:', e);
                try {
                    const { data } = await supabase
                        .from('medical_reports')
                        .select('*')
                        .eq('mother_id', motherId)
                        .order('upload_date', { ascending: false });
                    if (data) reportsData = data;
                } catch (e2) { console.warn('medical_reports fallback also failed:', e2); }
            }

            if (reportsData && reportsData.length > 0) {
                setDocuments(reportsData.map(r => ({
                    id: r.id,
                    title: r.filename || r.report_type || 'Medical Report',
                    summary: r.analysis_summary || r.ai_analysis_summary || '',
                    date: r.upload_date || r.created_at,
                    type: r.filename?.toLowerCase().endsWith('.pdf') ? 'PDF' : r.filename?.toLowerCase().match(/\.(jpg|jpeg|png)$/) ? 'Image' : 'DOC',
                    status: r.analysis_status || r.status || 'uploaded',
                    risk_level: r.risk_level || null,
                })));
            } else {
                setDocuments([]);
            }
        } catch (e) {
            console.error('Error loading mother details:', e);
        } finally {
            setLoadingAssessments(false);
        }

        // Fetch Chat History
        setLoadingChat(true);
        try {
            const { data: chatData, error: chatErr } = await supabase
                .from('telegram_logs')
                .select('*')
                .eq('mother_id', motherId)
                .order('created_at', { ascending: true });

            if (!chatErr && chatData) {
                const formattedChats = chatData.map(log => ({
                    role: log.message_type === 'user_query' || log.message_type === 'user' ? 'user' : 'assistant',
                    content: log.message_content || ''
                }));
                // Filter out empty messages just in case
                setMessages(formattedChats.filter(m => m.content.trim() !== ''));
            } else {
                if (chatErr) console.error("Chat error:", chatErr);
                setMessages([]);
            }
        } catch (e) {
            console.error('Error loading chat history:', e);
        } finally {
            setLoadingChat(false);
        }
    };

    useEffect(() => {
        if (selectedMother) {
            loadMotherDetails(selectedMother.id);
        } else {
            setAssessments([]);
            setDocuments([]);
            setMessages([]);
        }
    }, [selectedMother]);

    const loadData = useCallback(async (retryCount = 0) => {
        try {
            if (!user?.id) return;

            // Small delay to let auth session settle and avoid GoTrue lock conflicts
            if (retryCount === 0) {
                await new Promise(r => setTimeout(r, 300));
            }

            let staffId = null;

            // Lookup staff record based on role
            if (user.role === 'DOCTOR') {
                const { data: doctorsData, error: docError } = await supabase
                    .from('doctors')
                    .select('*')
                    .eq('user_profile_id', user.id)
                    .limit(1);

                if (docError) {
                    if (retryCount < 3 && (docError.message?.includes('AbortError') || docError.message?.includes('Lock broken'))) {
                        console.warn(`Staff load retry ${retryCount + 1}/3...`);
                        await new Promise(r => setTimeout(r, 1000));
                        return loadData(retryCount + 1);
                    }
                    console.error('Doctor load error:', docError);
                    return;
                }
                if (!doctorsData || doctorsData.length === 0) {
                    console.warn('No doctor record found for user:', user.id);
                    return;
                }
                staffId = doctorsData[0].id;
            } else if (user.role === 'ASHA_WORKER') {
                const { data: ashaData, error: ashaError } = await supabase
                    .from('asha_workers')
                    .select('*')
                    .eq('user_profile_id', user.id)
                    .limit(1);

                if (ashaError) {
                    if (retryCount < 3 && (ashaError.message?.includes('AbortError') || ashaError.message?.includes('Lock broken'))) {
                        console.warn(`Staff load retry ${retryCount + 1}/3...`);
                        await new Promise(r => setTimeout(r, 1000));
                        return loadData(retryCount + 1);
                    }
                    console.error('ASHA load error:', ashaError);
                    return;
                }
                if (!ashaData || ashaData.length === 0) {
                    console.warn('No ASHA record found for user:', user.id);
                    return;
                }
                staffId = ashaData[0].id;
            }

            if (!staffId) return;

            // Fetch assigned mothers based on role
            const filterColumn = user.role === 'DOCTOR' ? 'doctor_id' : 'asha_worker_id';
            const { data: mothersData, error: mothersError } = await supabase
                .from('mothers')
                .select('*')
                .eq(filterColumn, staffId);

            if (!mothersError && mothersData) {
                setMothers(mothersData);
            }
        } catch (e) {
            // Retry on network/abort errors
            if (retryCount < 3 && (e.message?.includes('AbortError') || e.message?.includes('Lock broken') || e.name === 'AbortError')) {
                console.warn(`Dashboard retry ${retryCount + 1}/3...`);
                await new Promise(r => setTimeout(r, 1000));
                return loadData(retryCount + 1);
            }
            console.error('Dashboard loadData error:', e);
        } finally { setLoading(false); }
    }, [user?.id, user?.role]);

    useEffect(() => { loadData(); }, []);

    const onRefresh = async () => { setRefreshing(true); await loadData(); setRefreshing(false); };

    const sendMessage = async () => {
        if (!input.trim() || !selectedMother) return;
        const userMsg = { role: 'user', content: input.trim() };
        setMessages((prev) => [...prev, userMsg]);
        setInput('');
        setSending(true);
        try {
            const res = await queryAgent({ motherId: selectedMother.id, query: userMsg.content });
            setMessages((prev) => [...prev, { role: 'assistant', content: res?.response || res?.message || 'No response' }]);
        } catch {
            setMessages((prev) => [...prev, { role: 'assistant', content: 'Error getting response. Please try again.' }]);
        } finally { setSending(false); }
    };

    const filteredMothers = mothers.filter((m) =>
        (m.name || m.full_name || '').toLowerCase().includes(searchQuery.toLowerCase())
    );

    if (loading) return <LoadingSpinner />;

    return (
        <View style={[styles.container, { backgroundColor: theme.background }]}>
            <View style={[styles.header, { backgroundColor: theme.primary }]}>
                <Text style={styles.headerTitle}>{user?.role === 'ASHA_WORKER' ? 'ASHA Dashboard' : 'Prenatal Care'}</Text>
                <Text style={styles.headerSub}>{mothers.length} patients</Text>
            </View>

            {selectedMother ? (
                /* Detail View */
                <View style={{ flex: 1 }}>
                    <TouchableOpacity
                        style={[styles.backBar, { backgroundColor: theme.surface, borderColor: theme.border }]}
                        onPress={() => { setSelectedMother(null); setMessages([]); }}
                    >
                        <Ionicons name="arrow-back" size={20} color={theme.primary} />
                        <Text style={[typography.bodyBold, { color: theme.text, marginLeft: spacing.sm }]}>
                            {selectedMother.name || selectedMother.full_name || 'Patient Details'}
                        </Text>
                    </TouchableOpacity>

                    {/* Mother Details Banner */}
                    <View style={[styles.motherDetailsBanner, { backgroundColor: theme.surfaceElevated, borderBottomColor: theme.border }]}>
                        <View style={styles.motherDetailsRow}>
                            <View style={styles.motherDetailItem}>
                                <Text style={[styles.detailLabel, { color: theme.textTertiary }]}>GRAVIDA</Text>
                                <Text style={[typography.bodyBold, { color: theme.text }]}>{selectedMother.gravida != null ? `G${selectedMother.gravida}` : '–'}</Text>
                            </View>
                            <View style={styles.motherDetailItem}>
                                <Text style={[styles.detailLabel, { color: theme.textTertiary }]}>PARITY</Text>
                                <Text style={[typography.bodyBold, { color: theme.text }]}>{selectedMother.parity != null ? `P${selectedMother.parity}` : '–'}</Text>
                            </View>
                            <View style={styles.motherDetailItem}>
                                <Text style={[styles.detailLabel, { color: theme.textTertiary }]}>BLOOD</Text>
                                <Text style={[typography.bodyBold, { color: theme.text }]}>{selectedMother.blood_group || '–'}</Text>
                            </View>
                            <View style={styles.motherDetailItem}>
                                <Text style={[styles.detailLabel, { color: theme.textTertiary }]}>GEST. AGE</Text>
                                <Text style={[typography.bodyBold, { color: theme.text }]}>{selectedMother.gestational_age_weeks ? `${selectedMother.gestational_age_weeks}w` : '–'}</Text>
                            </View>
                            <View style={styles.motherDetailItem}>
                                <Text style={[styles.detailLabel, { color: theme.textTertiary }]}>STATUS</Text>
                                <View style={[styles.statusBadge, { backgroundColor: selectedMother.status === 'postnatal' ? '#10B98120' : selectedMother.risk_level === 'HIGH' ? '#EF444420' : '#3B82F620' }]}>
                                    <Text style={{ fontSize: 10, fontWeight: '700', color: selectedMother.status === 'postnatal' ? '#10B981' : selectedMother.risk_level === 'HIGH' ? '#EF4444' : '#3B82F6' }}>
                                        {selectedMother.status === 'postnatal' ? 'Delivered' : selectedMother.risk_level || 'Active'}
                                    </Text>
                                </View>
                            </View>
                        </View>
                    </View>

                    {/* Functioanlity Tabs */}
                    <ScrollView horizontal showsHorizontalScrollIndicator={false} style={[styles.functionTabs, { backgroundColor: theme.surface, borderBottomColor: theme.border }]}>
                        {['history', 'documents', 'chat', 'consultation'].map((tab) => (
                            <TouchableOpacity
                                key={tab}
                                style={[styles.funcTabBtn, activeTab === tab && { borderBottomColor: theme.primary, borderBottomWidth: 2 }]}
                                onPress={() => setActiveTab(tab)}
                            >
                                <Text style={[styles.funcTabBtnText, { color: activeTab === tab ? theme.primary : theme.textSecondary, fontWeight: activeTab === tab ? '700' : '500' }]}>
                                    {tab === 'history' ? 'Assessment History' : tab === 'documents' ? 'Documents' : tab === 'chat' ? 'Chat History' : 'Consultation'}
                                </Text>
                            </TouchableOpacity>
                        ))}
                    </ScrollView>

                    {activeTab === 'chat' && (
                        <View style={{ flex: 1 }}>
                            <ScrollView style={{ flex: 1, padding: spacing.screenPadding }}>
                                {loadingChat ? (
                                    <LoadingSpinner />
                                ) : messages.length === 0 ? (
                                    <View style={{ alignItems: 'center', marginTop: spacing.xl }}>
                                        <Text style={[typography.body, { color: theme.textSecondary }]}>No chat history available.</Text>
                                    </View>
                                ) : (
                                    messages.map((msg, i) => (
                                        <View key={i} style={[
                                            styles.msgBubble,
                                            msg.role === 'user' ? { alignSelf: 'flex-end', backgroundColor: theme.primary } : { alignSelf: 'flex-start', backgroundColor: theme.surfaceElevated },
                                        ]}>
                                            <Text style={[typography.body, { color: msg.role === 'user' ? '#fff' : theme.text }]}>{msg.content}</Text>
                                        </View>
                                    ))
                                )}
                                {sending && (
                                    <View style={[styles.msgBubble, { alignSelf: 'flex-start', backgroundColor: theme.surfaceElevated }]}>
                                        <Text style={[typography.body, { color: theme.textSecondary }]}>Thinking...</Text>
                                    </View>
                                )}
                            </ScrollView>

                            <View style={[styles.chatInput, { backgroundColor: theme.surface, borderTopColor: theme.border }]}>
                                <TextInput
                                    style={[styles.chatTextInput, { color: theme.text, backgroundColor: theme.surfaceElevated }]}
                                    placeholder={t('type_message')}
                                    placeholderTextColor={theme.textTertiary}
                                    value={input}
                                    onChangeText={setInput}
                                    multiline
                                />
                                <TouchableOpacity
                                    style={[styles.sendBtn, { backgroundColor: theme.primary, opacity: input.trim() ? 1 : 0.4 }]}
                                    onPress={sendMessage}
                                    disabled={!input.trim() || sending}
                                >
                                    <Ionicons name="send" size={18} color="#fff" />
                                </TouchableOpacity>
                            </View>
                        </View>
                    )}

                    {activeTab === 'history' && (
                        <ScrollView style={{ flex: 1, padding: spacing.screenPadding }}>
                            {loadingAssessments ? (
                                <LoadingSpinner />
                            ) : assessments.length > 0 ? (
                                assessments.map((assessment, idx) => (
                                    <View key={idx} style={[styles.card, { backgroundColor: theme.surfaceElevated, borderColor: theme.border }]}>
                                        <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 }}>
                                            <Text style={[typography.bodyBold, { color: theme.text }]}>
                                                {assessment.type === 'consultation' ? 'Doctor Consultation' : 'Risk Assessment'}
                                            </Text>
                                            {assessment.risk_level && assessment.risk_level !== 'CONSULTATION' && (
                                                <View style={{ backgroundColor: assessment.risk_level === 'HIGH' ? '#EF444420' : '#10B98120', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 4 }}>
                                                    <Text style={{ fontSize: 10, fontWeight: 'bold', color: assessment.risk_level === 'HIGH' ? '#EF4444' : '#10B981' }}>{assessment.risk_level}</Text>
                                                </View>
                                            )}
                                        </View>
                                        <Text style={[typography.body, { color: theme.textSecondary }]}>
                                            {assessment.details?.notes || assessment.notes || assessment.description || "Routine check completed."}
                                        </Text>
                                        <Text style={[typography.caption, { color: theme.textTertiary, marginTop: 8 }]}>
                                            {new Date(assessment.created_at).toLocaleDateString()}
                                        </Text>
                                    </View>
                                ))
                            ) : (
                                <EmptyState icon="clipboard-outline" title="No Assessments Yet" message="No history found for this patient." />
                            )}
                        </ScrollView>
                    )}

                    {activeTab === 'documents' && (
                        <ScrollView style={{ flex: 1, padding: spacing.screenPadding }}>
                            {documents.length > 0 ? documents.map(doc => (
                                <TouchableOpacity key={doc.id} style={[styles.card, { backgroundColor: theme.surfaceElevated, borderColor: theme.border }]}>
                                    <View style={{ flexDirection: 'row', alignItems: 'flex-start' }}>
                                        <View style={[styles.docIcon, { backgroundColor: doc.type === 'PDF' ? theme.primary + '15' : theme.info + '15' }]}>
                                            <Ionicons name={doc.type === 'PDF' ? "document-text" : doc.type === 'Image' ? "image" : "document"} size={24} color={doc.type === 'PDF' ? theme.primary : theme.info} />
                                        </View>
                                        <View style={{ flex: 1, marginLeft: 12 }}>
                                            <Text style={[typography.bodyBold, { color: theme.text }]} numberOfLines={1}>{doc.title}</Text>
                                            <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 4, gap: 8 }}>
                                                <Text style={[typography.caption, { color: theme.textTertiary }]}>
                                                    {doc.type} • {new Date(doc.date).toLocaleDateString()}
                                                </Text>
                                                {doc.status && (
                                                    <View style={[styles.statusBadge, { backgroundColor: doc.status === 'analyzed' ? '#10B98120' : doc.status === 'processing' ? '#F9731620' : '#3B82F620' }]}>
                                                        <Text style={{ fontSize: 9, fontWeight: '700', color: doc.status === 'analyzed' ? '#10B981' : doc.status === 'processing' ? '#F97316' : '#3B82F6' }}>
                                                            {doc.status === 'analyzed' ? '✓ Analyzed' : doc.status === 'processing' ? '⏳ Processing' : '📄 Uploaded'}
                                                        </Text>
                                                    </View>
                                                )}
                                            </View>
                                            {doc.summary ? (
                                                <Text style={[typography.caption, { color: theme.textSecondary, marginTop: 6, lineHeight: 18 }]} numberOfLines={3}>
                                                    {doc.summary}
                                                </Text>
                                            ) : null}
                                            {doc.risk_level && (
                                                <View style={{ marginTop: 4 }}>
                                                    <Text style={[typography.caption, { color: doc.risk_level === 'HIGH' ? '#EF4444' : '#10B981', fontWeight: '600' }]}>
                                                        Risk: {doc.risk_level}
                                                    </Text>
                                                </View>
                                            )}
                                        </View>
                                    </View>
                                </TouchableOpacity>
                            )) : (
                                <EmptyState icon="folder-open-outline" title="No Documents" message="Upload lab reports and scans here." />
                            )}
                            <TouchableOpacity style={[styles.submitBtn, { backgroundColor: theme.primary, marginTop: spacing.xl }]}>
                                <Ionicons name="cloud-upload-outline" size={20} color="#fff" />
                                <Text style={{ color: '#fff', fontSize: 16, fontWeight: '600', marginLeft: 8 }}>Upload Report</Text>
                            </TouchableOpacity>
                        </ScrollView>
                    )}

                    {activeTab === 'consultation' && (
                        <View style={{ flex: 1, padding: spacing.screenPadding, justifyContent: 'center', alignItems: 'center' }}>
                            <Ionicons name="calendar-outline" size={64} color={theme.textTertiary} />
                            <Text style={[typography.h3, { color: theme.text, marginTop: spacing.md }]}>Postnatal & Consultations</Text>
                            <Text style={[typography.body, { color: theme.textSecondary, textAlign: 'center', marginTop: spacing.sm }]}>
                                Upcoming checkups and consultation schedules will appear here. Syncing with ASHA worker logs...
                            </Text>
                            <TouchableOpacity style={[styles.submitBtn, { backgroundColor: theme.primary, marginTop: spacing.xl, paddingHorizontal: 32 }]}>
                                <Text style={{ color: '#fff', fontSize: 16, fontWeight: '600' }}>Schedule Checkup</Text>
                            </TouchableOpacity>
                        </View>
                    )}
                </View>
            ) : (
                /* Patient List */
                <ScrollView
                    refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.primary} />}
                    contentContainerStyle={styles.content}
                >
                    <View style={[styles.searchBar, { backgroundColor: theme.surfaceElevated, borderColor: theme.border }]}>
                        <Ionicons name="search-outline" size={18} color={theme.textTertiary} />
                        <TextInput
                            style={[styles.searchInput, { color: theme.text }]}
                            placeholder="Search patients..."
                            placeholderTextColor={theme.textTertiary}
                            value={searchQuery}
                            onChangeText={setSearchQuery}
                        />
                    </View>

                    {filteredMothers.length > 0
                        ? filteredMothers.map((m, i) => (
                            <PatientCard key={m.id || i} patient={m} onPress={() => setSelectedMother(m)} />
                        ))
                        : <EmptyState icon="search-outline" title={t('no_data')} message="No patients found" />
                    }
                </ScrollView>
            )}
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1 },
    header: { paddingTop: 54, paddingBottom: 16, paddingHorizontal: spacing.screenPadding },
    headerTitle: { color: '#fff', fontSize: 22, fontWeight: '700' },
    headerSub: { color: 'rgba(255,255,255,0.8)', fontSize: 14, marginTop: 4 },
    content: { padding: spacing.screenPadding, paddingBottom: 100 },
    searchBar: {
        flexDirection: 'row', alignItems: 'center',
        paddingHorizontal: spacing.base, paddingVertical: 10,
        borderRadius: borderRadius.md, borderWidth: 1, gap: 8,
        marginBottom: spacing.base,
    },
    searchInput: { flex: 1, fontSize: 15 },
    functionTabs: {
        flexDirection: 'row',
        paddingHorizontal: spacing.sm,
        borderBottomWidth: 1,
        maxHeight: 48,
        minHeight: 48,
    },
    funcTabBtn: {
        paddingHorizontal: spacing.md,
        paddingVertical: 14,
        marginRight: spacing.sm,
    },
    funcTabBtnText: {
        fontSize: 14,
    },
    card: {
        padding: spacing.base, borderRadius: borderRadius.lg, borderWidth: 1, marginBottom: spacing.md,
    },
    submitBtn: {
        flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
        paddingVertical: 14, borderRadius: borderRadius.md,
    },
    backBar: {
        flexDirection: 'row', alignItems: 'center',
        paddingHorizontal: spacing.screenPadding, paddingVertical: 12,
        borderBottomWidth: 1,
    },
    motherDetailsBanner: {
        paddingHorizontal: spacing.screenPadding, paddingVertical: 10,
        borderBottomWidth: 1,
    },
    motherDetailsRow: {
        flexDirection: 'row', flexWrap: 'wrap', gap: 12,
    },
    motherDetailItem: {
        alignItems: 'center', minWidth: 50,
    },
    detailLabel: {
        fontSize: 10, fontWeight: '700', letterSpacing: 0.5, marginBottom: 2,
    },
    statusBadge: {
        paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4,
    },
    docIcon: {
        width: 44, height: 44, borderRadius: 10, justifyContent: 'center', alignItems: 'center',
    },
    msgBubble: {
        maxWidth: '80%', padding: spacing.md,
        borderRadius: borderRadius.lg, marginBottom: spacing.sm,
    },
    chatInput: {
        flexDirection: 'row', alignItems: 'flex-end',
        padding: spacing.sm, paddingBottom: 30, borderTopWidth: 1, gap: 8,
    },
    chatTextInput: {
        flex: 1, paddingHorizontal: 14, paddingVertical: 10,
        borderRadius: borderRadius.xl, fontSize: 15, maxHeight: 100,
    },
    sendBtn: {
        width: 42, height: 42, borderRadius: 21,
        justifyContent: 'center', alignItems: 'center',
    },
});
