// AI Chat Screen
import React, { useState, useRef } from 'react';
import {
    View, Text, ScrollView, TextInput, TouchableOpacity, StyleSheet, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../contexts/ThemeContext';
import { typography, spacing, borderRadius } from '../../theme';
import { queryAgent } from '../../services/api';

export default function AIChatScreen() {
    const { t } = useTranslation();
    const { theme } = useTheme();
    const scrollRef = useRef(null);
    const [messages, setMessages] = useState([
        { role: 'assistant', content: 'Hello! I am Aanchal AI, your maternal & child health assistant. I have 10 specialized agents to help you with pregnancy care, nutrition, risk assessment, child health, vaccinations, growth monitoring, and more. How can I help you today?' },
    ]);
    const [input, setInput] = useState('');
    const [sending, setSending] = useState(false);
    const [isRecording, setIsRecording] = useState(false);

    const sendMessage = async () => {
        if (!input.trim()) return;
        const userMsg = { role: 'user', content: input.trim() };
        setMessages((prev) => [...prev, userMsg]);
        setInput('');
        setSending(true);
        setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 100);

        try {
            const res = await queryAgent({ query: userMsg.content });
            const aiResponse = res?.response || res?.message || 'I apologize, I could not process your request. Please try again.';
            setMessages((prev) => [...prev, { role: 'assistant', content: aiResponse, agent: res?.agent }]);
        } catch (e) {
            setMessages((prev) => [...prev, {
                role: 'assistant',
                content: 'Sorry, I encountered an error. The server might be starting up — please try again in a moment.',
            }]);
        } finally {
            setSending(false);
            setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 100);
        }
    };

    const toggleRecording = () => {
        if (isRecording) {
            setIsRecording(false);
            // In production: stop recording, transcribe with Gemini, set input
            Alert.alert('Voice Input', 'Voice recording stopped. Transcription would appear here in production.');
        } else {
            setIsRecording(true);
            // In production: start recording using expo-av
        }
    };

    return (
        <View style={[styles.container, { backgroundColor: theme.background }]}>
            {/* Header */}
            <View style={[styles.header, { backgroundColor: theme.primary }]}>
                <View style={styles.headerContent}>
                    <View style={styles.headerAvatar}>
                        <Ionicons name="chatbubbles" size={24} color="#fff" />
                    </View>
                    <View>
                        <Text style={styles.headerTitle}>{t('appName')} Chat</Text>
                        <Text style={styles.headerSub}>10 Specialized Health Agents</Text>
                    </View>
                </View>
            </View>

            {/* Messages */}
            <ScrollView ref={scrollRef} style={styles.messageList} contentContainerStyle={styles.messageContent}>
                {messages.map((msg, i) => (
                    <View key={i} style={[
                        styles.bubble,
                        msg.role === 'user'
                            ? { alignSelf: 'flex-end', backgroundColor: theme.primary, borderBottomRightRadius: 4 }
                            : { alignSelf: 'flex-start', backgroundColor: theme.surface, borderBottomLeftRadius: 4, borderColor: theme.border, borderWidth: 1 },
                    ]}>
                        {msg.agent && (
                            <View style={[styles.agentTag, { backgroundColor: theme.primary + '15' }]}>
                                <Ionicons name="flash" size={12} color={theme.primary} />
                                <Text style={[typography.captionBold, { color: theme.primary, marginLeft: 2 }]}>{msg.agent}</Text>
                            </View>
                        )}
                        <Text style={[typography.body, { color: msg.role === 'user' ? '#fff' : theme.text }]}>
                            {msg.content}
                        </Text>
                    </View>
                ))}
                {sending && (
                    <View style={[styles.bubble, { alignSelf: 'flex-start', backgroundColor: theme.surface, borderColor: theme.border, borderWidth: 1 }]}>
                        <View style={styles.typingDots}>
                            {[0, 1, 2].map((i) => (
                                <View key={i} style={[styles.dot, { backgroundColor: theme.textTertiary }]} />
                            ))}
                        </View>
                    </View>
                )}
            </ScrollView>

            {/* Input Bar */}
            <View style={[styles.inputBar, { backgroundColor: theme.surface, borderTopColor: theme.border }]}>
                {/* Voice Button */}
                <TouchableOpacity
                    style={[styles.voiceBtn, isRecording && { backgroundColor: theme.error }]}
                    onPress={toggleRecording}
                >
                    <Ionicons name={isRecording ? 'stop' : 'mic-outline'} size={20} color={isRecording ? '#fff' : theme.primary} />
                </TouchableOpacity>

                <TextInput
                    style={[styles.inputField, { color: theme.text, backgroundColor: theme.surfaceElevated }]}
                    placeholder={t('type_message')}
                    placeholderTextColor={theme.textTertiary}
                    value={input}
                    onChangeText={setInput}
                    multiline
                    onSubmitEditing={sendMessage}
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
    );
}

const styles = StyleSheet.create({
    container: { flex: 1 },
    header: { paddingTop: 54, paddingBottom: 16, paddingHorizontal: spacing.screenPadding },
    headerContent: { flexDirection: 'row', alignItems: 'center', gap: 12 },
    headerAvatar: { width: 40, height: 40, borderRadius: 20, backgroundColor: 'rgba(255,255,255,0.2)', justifyContent: 'center', alignItems: 'center' },
    headerTitle: { color: '#fff', fontSize: 18, fontWeight: '700' },
    headerSub: { color: 'rgba(255,255,255,0.8)', fontSize: 12 },
    messageList: { flex: 1 },
    messageContent: { padding: spacing.screenPadding, paddingBottom: 16 },
    bubble: { maxWidth: '82%', padding: spacing.md, borderRadius: borderRadius.lg, marginBottom: spacing.md },
    agentTag: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 8, marginBottom: 6, alignSelf: 'flex-start' },
    typingDots: { flexDirection: 'row', gap: 4 },
    dot: { width: 8, height: 8, borderRadius: 4, opacity: 0.4 },
    inputBar: {
        flexDirection: 'row', alignItems: 'flex-end',
        paddingHorizontal: spacing.sm, paddingVertical: spacing.sm,
        paddingBottom: 30, borderTopWidth: 1, gap: 8,
    },
    voiceBtn: {
        width: 42, height: 42, borderRadius: 21,
        justifyContent: 'center', alignItems: 'center',
        backgroundColor: 'transparent', borderWidth: 1.5, borderColor: '#0D9488',
    },
    inputField: {
        flex: 1, paddingHorizontal: 14, paddingVertical: 10,
        borderRadius: borderRadius.xl, fontSize: 15, maxHeight: 100,
    },
    sendBtn: {
        width: 42, height: 42, borderRadius: 21,
        justifyContent: 'center', alignItems: 'center',
    },
});
