// Home Screen — Exact replica of website Home.jsx sections
import React from 'react';
import {
    View, Text, ScrollView, TouchableOpacity, Image, StyleSheet, StatusBar, Dimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../contexts/ThemeContext';
import { typography, spacing, borderRadius } from '../../theme';

const { width } = Dimensions.get('window');
const CARD_WIDTH = width - spacing.screenPadding * 2;

// --- Section Title (matches web SectionTitle) ---
function SectionTitle({ title, subtitle }) {
    return (
        <View style={styles.sectionTitle}>
            <Text style={styles.sectionTitleText}>{title}</Text>
            {subtitle && <Text style={styles.sectionSubtitle}>{subtitle}</Text>}
        </View>
    );
}

export default function HomeScreen({ navigation }) {
    const { t } = useTranslation();
    const { theme } = useTheme();

    return (
        <ScrollView style={{ flex: 1, backgroundColor: theme.backgroundGradientFrom || '#FDF2F8' }} bounces={false}>
            <StatusBar barStyle="light-content" />

            {/* ============ NAVBAR ============ */}
            <View style={[styles.navbar, { backgroundColor: '#2563EB' }]}>
                <View style={styles.navBrand}>
                    <Ionicons name="heart" size={32} color="#fff" />
                    <View style={{ marginLeft: 12 }}>
                        <Text style={[typography.h3, { color: '#fff' }]}>Aanchal AI</Text>
                        <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: 13, marginTop: 2 }}>Maternal & Child Health Guardian</Text>
                    </View>
                </View>
                <View style={styles.navActions}>
                    <TouchableOpacity onPress={() => navigation.navigate('Login')} style={styles.navBtnLogin}>
                        <Text style={[typography.smallBold, { color: '#fff' }]}>Login</Text>
                    </TouchableOpacity>
                    <TouchableOpacity onPress={() => navigation.navigate('Signup')} style={styles.navBtnSignup}>
                        <Text style={[typography.smallBold, { color: '#2563EB' }]}>Signup</Text>
                    </TouchableOpacity>
                </View>
            </View>

            {/* ============ HERO SECTION ============ */}
            <View style={[styles.heroSection, { backgroundColor: theme.backgroundGradientFrom || '#FDF2F8' }]}>
                <Text style={[styles.heroTitle, { color: theme.text }]}>
                    AI-Powered 24/7 Maternal Health Monitoring for Mothers in Low-Resource Settings.
                </Text>
                <Text style={[styles.heroSubtitle, { color: theme.textSecondary }]}>
                    Aanchal AI automates maternal risk assessment, report analysis, and care coordination using multi-agent AI and chat-first interfaces—no app required.
                </Text>
                <View style={styles.heroCTA}>
                    <TouchableOpacity style={[styles.ctaBtn, { backgroundColor: theme.accent }]}>
                        <Text style={styles.ctaBtnText}>Start a Chat on Telegram</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                        style={[styles.ctaBtn, styles.ctaOutline, { borderColor: theme.accent }]}
                        onPress={() => navigation.navigate('Login')}
                    >
                        <Ionicons name="play-circle-outline" size={18} color={theme.accent} />
                        <Text style={[styles.ctaBtnText, { color: theme.accent }]}>View Dashboard</Text>
                    </TouchableOpacity>
                </View>
                {/* Hero Image */}
                <View style={[styles.heroImageCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                    <View style={[styles.heroImagePlaceholder, { backgroundColor: theme.primaryLight }]}>
                        <Ionicons name="heart-circle" size={64} color={theme.primary} />
                        <Text style={[typography.bodyBold, { color: theme.primary, marginTop: 8 }]}>Aanchal AI</Text>
                        <Text style={[typography.caption, { color: theme.textSecondary }]}>Maternal & Child Health Platform</Text>
                    </View>
                </View>
            </View>

            {/* ============ THE PROBLEM ============ */}
            <View style={[styles.section, { backgroundColor: theme.backgroundGradientTo || '#FAF5FF' }]}>
                <SectionTitle title="The Problem" />
                <View style={[styles.contentCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                    <Text style={[styles.cardParagraph, { color: theme.text }]}>
                        Every two minutes, a woman dies from preventable pregnancy complications. Frontline ASHA workers lack tools, real-time insights, and automated coordination, leading to late referrals and avoidable emergencies.
                    </Text>
                    <View style={styles.problemList}>
                        {[
                            { icon: 'warning-outline', color: '#DC2626', text: 'Fragmented medical records' },
                            { icon: 'document-text-outline', color: '#D97706', text: 'Reports are unanalyzed PDFs' },
                            { icon: 'shield-checkmark-outline', color: '#0d9488', text: 'No proactive alerts' },
                            { icon: 'people-outline', color: '#059669', text: 'High workload for ASHAs' },
                        ].map((item, i) => (
                            <View key={i} style={styles.problemItem}>
                                <Ionicons name={item.icon} size={16} color={item.color} />
                                <Text style={[styles.problemText, { color: theme.textSecondary }]}>{item.text}</Text>
                            </View>
                        ))}
                    </View>
                </View>
            </View>

            {/* ============ THE SOLUTION ============ */}
            <View style={[styles.section, { backgroundColor: theme.backgroundGradientFrom || '#FDF2F8' }]}>
                <SectionTitle title="The Solution – Aanchal AI" />
                <View style={[styles.contentCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                    <Text style={[styles.cardParagraph, { color: theme.text }]}>
                        A multi-agent AI platform that detects maternal risk early, analyzes medical documents instantly, and coordinates care across Telegram, WhatsApp, and web dashboards.
                    </Text>
                    <View style={[styles.flowDiagram, { backgroundColor: theme.primaryLight }]}>
                        <Ionicons name="git-network-outline" size={48} color={theme.primary} />
                        <Text style={[typography.captionBold, { color: theme.primary, marginTop: 8 }]}>System Architecture</Text>
                    </View>
                </View>
            </View>

            {/* ============ KEY FEATURES ============ */}
            <View style={[styles.section, { backgroundColor: theme.backgroundGradientTo || '#FAF5FF' }]}>
                <SectionTitle title="Key Features" />
                <View style={styles.featuresGrid}>
                    {[
                        { icon: 'heart-outline', title: 'AI Risk Agent', desc: 'Automated maternal risk scoring' },
                        { icon: 'document-text-outline', title: 'Document Analyzer', desc: 'Extract vitals & insights from PDFs/images' },
                        { icon: 'people-outline', title: 'ASHA Dashboard', desc: 'Manage mothers, tasks, and follow-ups' },
                        { icon: 'warning-outline', title: 'Emergency Agent', desc: 'Triage & escalation workflows' },
                        { icon: 'nutrition-outline', title: 'Nutrition & Meds', desc: 'Personalized recommendations' },
                        { icon: 'chatbubbles-outline', title: 'No-App Adoption', desc: 'Available on Telegram & WhatsApp' },
                    ].map((f, i) => (
                        <View key={i} style={[styles.featureCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                            <Ionicons name={f.icon} size={22} color={theme.accent} />
                            <Text style={[styles.featureTitle, { color: theme.text }]}>{f.title}</Text>
                            <Text style={[styles.featureDesc, { color: theme.textSecondary }]}>{f.desc}</Text>
                        </View>
                    ))}
                </View>
            </View>

            {/* ============ WHO IT'S FOR ============ */}
            <View style={[styles.section, { backgroundColor: theme.backgroundGradientFrom || '#FDF2F8' }]}>
                <SectionTitle title="Who It's For" />
                <View style={styles.audienceGrid}>
                    {[
                        { icon: 'chatbubble-outline', color: '#DB2777', title: 'Mothers', desc: 'Health reminders & summaries' },
                        { icon: 'people-outline', color: '#059669', title: 'ASHAs', desc: 'Automated tasks & simplified workflows' },
                        { icon: 'business-outline', color: '#0d9488', title: 'Clinics / Govt', desc: 'Population-level monitoring' },
                    ].map((a, i) => (
                        <View key={i} style={[styles.audienceCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                            <View style={styles.audienceHeader}>
                                <Ionicons name={a.icon} size={22} color={a.color} />
                                <Text style={[styles.audienceTitle, { color: theme.text }]}>{a.title}</Text>
                            </View>
                            <Text style={[styles.audienceDesc, { color: theme.textSecondary }]}>{a.desc}</Text>
                        </View>
                    ))}
                </View>
            </View>

            {/* ============ IMPACT METRICS ============ */}
            <View style={[styles.section, { backgroundColor: theme.backgroundGradientTo || '#FAF5FF' }]}>
                <SectionTitle title="Impact Metrics" />
                <View style={styles.statsRow}>
                    {[
                        { value: '40%', label: 'reduction in manual risk evaluation time' },
                        { value: '5x', label: 'faster report processing' },
                        { value: 'Low-BW', label: 'deployment in rural India' },
                    ].map((s, i) => (
                        <View key={i} style={[styles.statCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                            <Text style={[styles.statValue, { color: theme.accent }]}>{s.value}</Text>
                            <Text style={[styles.statLabel, { color: theme.textSecondary }]}>{s.label}</Text>
                        </View>
                    ))}
                </View>
            </View>

            {/* ============ COMPETITIVE ADVANTAGE ============ */}
            <View style={[styles.section, { backgroundColor: theme.backgroundGradientFrom || '#FDF2F8' }]}>
                <SectionTitle title="Why Aanchal AI Wins" />
                <View style={[styles.contentCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                    {[
                        { icon: 'git-network-outline', color: '#0d9488', text: 'Multi-agent orchestration' },
                        { icon: 'sparkles-outline', color: '#DB2777', text: 'Report intelligence powered by Gemini' },
                        { icon: 'chatbubble-outline', color: '#059669', text: 'Chat-first UX lowers literacy barriers' },
                        { icon: 'shield-checkmark-outline', color: '#0d9488', text: 'Designed for Bharat-scale healthcare' },
                    ].map((item, i) => (
                        <View key={i} style={styles.advantageItem}>
                            <Ionicons name={item.icon} size={16} color={item.color} />
                            <Text style={[styles.advantageText, { color: theme.text }]}>{item.text}</Text>
                        </View>
                    ))}
                </View>
            </View>

            {/* ============ FOOTER ============ */}
            <View style={[styles.footer, { backgroundColor: theme.surface, borderTopColor: theme.border }]}>
                <View style={styles.footerBrand}>
                    <Ionicons name="heart" size={20} color="#DB2777" />
                    <Text style={[styles.footerBrandText, { color: theme.text }]}>Aanchal AI</Text>
                </View>
                <View style={styles.footerLinks}>
                    <TouchableOpacity onPress={() => navigation.navigate('Login')}>
                        <Text style={[styles.footerLink, { color: theme.textSecondary }]}>Login</Text>
                    </TouchableOpacity>
                    <Text style={{ color: theme.textTertiary }}> · </Text>
                    <TouchableOpacity onPress={() => navigation.navigate('Signup')}>
                        <Text style={[styles.footerLink, { color: theme.textSecondary }]}>Signup</Text>
                    </TouchableOpacity>
                </View>
                <TouchableOpacity style={[styles.telegramBtn, { backgroundColor: theme.accent }]}>
                    <Text style={styles.telegramBtnText}>Start Chat on Telegram @MatruRaksha_AI_Bot</Text>
                </TouchableOpacity>
                <Text style={[styles.copyright, { color: theme.textTertiary }]}>
                    © 2025 Aanchal AI · React · FastAPI · Supabase · Gemini
                </Text>
            </View>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    /* NAVBAR */
    navbar: { paddingTop: 60, paddingBottom: 20, paddingHorizontal: spacing.screenPadding, elevation: 4, boxShadow: '0px 4px 10px rgba(0, 0, 0, 0.1)' },
    navBrand: { flexDirection: 'row', alignItems: 'center' },
    navActions: { flexDirection: 'row', alignItems: 'center', marginTop: 16, gap: 12 },
    navBtnLogin: { paddingVertical: 8, paddingHorizontal: 16, backgroundColor: 'rgba(255,255,255,0.2)', borderRadius: 8 },
    navBtnSignup: { paddingVertical: 8, paddingHorizontal: 16, backgroundColor: '#fff', borderRadius: 8 },

    /* HERO */
    heroSection: { paddingTop: 40, paddingHorizontal: spacing.screenPadding, paddingBottom: spacing.xl },
    heroTitle: { fontSize: 28, fontWeight: '800', lineHeight: 36 },
    heroSubtitle: { fontSize: 15, lineHeight: 22, marginTop: 12 },
    heroCTA: { flexDirection: 'row', gap: 10, marginTop: 20, flexWrap: 'wrap' },
    ctaBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 12, paddingHorizontal: 20, borderRadius: 10, gap: 6 },
    ctaOutline: { backgroundColor: 'transparent', borderWidth: 1.5 },
    ctaBtnText: { color: '#fff', fontWeight: '600', fontSize: 14 },
    heroImageCard: { marginTop: 24, borderRadius: 16, padding: 12, borderWidth: 1, boxShadow: '0px 4px 12px rgba(0, 0, 0, 0.1)', elevation: 4 },
    heroImagePlaceholder: { height: 200, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },

    /* SECTIONS */
    section: { paddingHorizontal: spacing.screenPadding, paddingVertical: spacing.xxl },
    sectionTitle: { alignItems: 'center', marginBottom: 24 },
    sectionTitleText: { fontSize: 24, fontWeight: '700', color: '#111827' },
    sectionSubtitle: { fontSize: 14, color: '#4B5563', marginTop: 6, textAlign: 'center' },

    /* CONTENT CARDS */
    contentCard: { borderRadius: 12, padding: 20, borderWidth: 1, boxShadow: '0px 2px 6px rgba(0, 0, 0, 0.04)', elevation: 1 },
    cardParagraph: { fontSize: 15, lineHeight: 22 },

    /* PROBLEM */
    problemList: { marginTop: 16, gap: 10 },
    problemItem: { flexDirection: 'row', alignItems: 'center', gap: 8 },
    problemText: { fontSize: 14 },

    /* FLOW DIAGRAM PLACEHOLDER */
    flowDiagram: { marginTop: 16, height: 120, borderRadius: 8, justifyContent: 'center', alignItems: 'center' },

    /* FEATURES */
    featuresGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
    featureCard: { width: (CARD_WIDTH - 12) / 2, borderRadius: 12, padding: 16, borderWidth: 1 },
    featureTitle: { fontSize: 14, fontWeight: '600', marginTop: 8 },
    featureDesc: { fontSize: 12, marginTop: 4, lineHeight: 16 },

    /* AUDIENCE */
    audienceGrid: { gap: 12 },
    audienceCard: { borderRadius: 12, padding: 16, borderWidth: 1 },
    audienceHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 4 },
    audienceTitle: { fontSize: 16, fontWeight: '600' },
    audienceDesc: { fontSize: 13 },

    /* STATS */
    statsRow: { flexDirection: 'row', gap: 10 },
    statCard: { flex: 1, borderRadius: 12, padding: 16, borderWidth: 1, alignItems: 'center' },
    statValue: { fontSize: 24, fontWeight: '700' },
    statLabel: { fontSize: 11, marginTop: 6, textAlign: 'center', lineHeight: 15 },

    /* ADVANTAGES */
    advantageItem: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingVertical: 6 },
    advantageText: { fontSize: 14 },

    /* FOOTER */
    footer: { paddingHorizontal: spacing.screenPadding, paddingVertical: 32, alignItems: 'center', borderTopWidth: 1 },
    footerBrand: { flexDirection: 'row', alignItems: 'center', gap: 6 },
    footerBrandText: { fontWeight: '700', fontSize: 16 },
    footerLinks: { flexDirection: 'row', alignItems: 'center', marginTop: 12 },
    footerLink: { fontSize: 13 },
    telegramBtn: { marginTop: 16, paddingVertical: 10, paddingHorizontal: 20, borderRadius: 8 },
    telegramBtnText: { color: '#fff', fontWeight: '600', fontSize: 13 },
    copyright: { fontSize: 11, marginTop: 16 },
});
