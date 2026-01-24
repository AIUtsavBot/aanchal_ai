# 📋 Changelog

All notable changes to the **MatruRakshaAI** project will be documented in this file.

---

## [v3.0.0] - 2026-01-24

### 🚀 Major Features

- **Hybrid RAG System (Retrieval-Augmented Generation)**
  - Combines BM25 (sparse) and Supabase pgvector (dense) search.
  - Context-aware AI responses using 1,015 maternal health case records.
  - Integrated with Gemini 2.5 Flash for evidence-based recommendations.
- **Offline-First Architecture**
  - `IndexedDB` based local queue for forms, chats, and documents.
  - Auto-sync service that processes pending items when network restores.
  - Seamless experience for ASHA workers in low-connectivity areas.
- **Doctor-Mother Chat Improvements**
  - **Real-time Updates**: 5-second polling + Supabase Realtime for instant message delivery.
  - **Direct Addressing**: Mothers can address doctors directly ("Doctor...", "Didi...") to bypass AI.
  - **Smart Cooldown**: AI agent stays silent during active doctor-patient conversations (30 min timeout).
  - **Emergency Override**: "Blood loss", "pain", and other emergency keywords **always** trigger AI response and alerts, regardless of chat mode.
- **Continuous Learning**
  - New risk assessments are automatically added to the RAG knowledge base.

### ⚡ Improvements

- **Performance**: 2-month local caching for chat history for instant load times.
- **UI/UX**: Distinct coloring for MOTHER (Pink), DOCTOR (Teal), and BOT (Blue) roles in chat.
- **Multilingual Support**: added Hindi/Marathi keyword detection for chat routing.

---

## [v2.3.0] - Performance Optimizations (December 2024)

### ✅ Optimizations

- **In-Memory Caching**: 30-second TTL cache for dashboard data (eliminating Redis dependency).
- **Optimized Database Queries**: Replaced `SELECT *` with `COUNT` queries for aggregates.
- **Combined API Endpoints**: merged `/dashboard/full` and `/admin/full` to reduce API calls by 75%.
- **Fixed N+1 Query Patterns**: Admin routes now batch queries efficiently.
- **Frontend Parallel Fetching**: implemented `Promise.all` with combined endpoint fallback.
- **3x Faster Dashboard Loading**: First load and instant repeat loads within cache TTL.

---

## [v2.2.0] - Enhanced Authentication (December 2024)

### ✅ Features

- **Google OAuth Integration**: Users can now sign in with Google.
- **Role Selection Flow**: New users select their role (Doctor/ASHA Worker) after OAuth.
- **Doctor Certificate Upload**: Doctors must upload medical registration certificates for verification.
- **Multi-Step Onboarding**: Guided registration process with pending approval screen.
- **Unified Approval Center**: `/admin/approvals` endpoint handles all pending registrations.
- **Email Alerts**: Integration with Resend API to send emergency alerts to assigned doctors/ASHA workers.
