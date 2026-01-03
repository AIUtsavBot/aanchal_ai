# 🤖 MatruRaksha Telegram Bot Commands

> Complete reference for all Telegram bot commands and user interactions.

---

## 📋 Table of Contents

- [Command Reference](#-command-reference)
- [Registration Flow](#-registration-flow)
- [Daily Check-in](#-daily-check-in)
- [Natural Language Queries](#-natural-language-queries)
- [Document Upload](#-document-upload)
- [Emergency Handling](#-emergency-handling)
- [Dashboard Navigation](#-dashboard-navigation)

---

## 📖 Command Reference

### Core Commands

| Command | Description | Access |
|---------|-------------|--------|
| `/start` | Welcome message and get chat ID | All users |
| `/register` | Start mother registration process | Unregistered |
| `/checkin` | Daily health check-in | Registered mothers |
| `/status` | View current health status | Registered mothers |
| `/timeline` | View health history timeline | Registered mothers |
| `/report` | Report symptoms or concerns | Registered mothers |
| `/help` | Show all available commands | All users |
| `/cancel` | Cancel current operation | All users |

---

## `/start` - Welcome Message

**Usage:** Initiates interaction with the bot.

**Response:**
```
🙏 Welcome to MatruRaksha AI!

I'm your maternal health companion. I'm here to help you through 
your pregnancy journey with:

🏥 Daily health check-ins
📊 Risk assessments
💊 Medication reminders
🥗 Nutrition guidance
🚨 Emergency support

Your Chat ID: 123456789
(Save this for registration)

Type /register to get started or /help for more options.
```

**What happens:**
1. Bot sends welcome message
2. Displays user's Telegram chat ID
3. Shows quick action buttons

---

## `/register` - Mother Registration

**Usage:** Starts the registration process for new mothers.

### Registration Flow

```
Step 1: Name
┌────────────────────────────────────────┐
│ 👩 Please enter your full name:        │
└────────────────────────────────────────┘
User: Priya Sharma

Step 2: Phone Number
┌────────────────────────────────────────┐
│ 📱 Please enter your phone number:     │
│    (10 digits, e.g., 9876543210)       │
└────────────────────────────────────────┘
User: 9876543210

Step 3: Age
┌────────────────────────────────────────┐
│ 🎂 Please enter your age:              │
└────────────────────────────────────────┘
User: 28

Step 4: Location
┌────────────────────────────────────────┐
│ 📍 Please enter your city/location:    │
└────────────────────────────────────────┘
User: Mumbai

Step 5: Confirmation
┌────────────────────────────────────────┐
│ ✅ Registration Complete!              │
│                                         │
│ Name: Priya Sharma                     │
│ Phone: 9876543210                      │
│ Age: 28                                │
│ Location: Mumbai                       │
│                                         │
│ Your health journey begins now! 🌟      │
│ Use /checkin for your daily check-in.  │
└────────────────────────────────────────┘
```

**Cancel at any time:** Send `/cancel` to abort registration.

---

## `/checkin` - Daily Health Check-in

**Usage:** Conduct daily health monitoring.

### Check-in Flow

```
Step 1: Overall Feeling
┌────────────────────────────────────────┐
│ 🌅 Good morning, Priya!                │
│ How are you feeling today?             │
│                                         │
│ [😊 Good] [😐 Okay] [😟 Not Good]      │
└────────────────────────────────────────┘

Step 2: Symptoms (if applicable)
┌────────────────────────────────────────┐
│ Any symptoms to report?                 │
│                                         │
│ [Headache] [Swelling] [Nausea]         │
│ [Dizziness] [Bleeding] [None]          │
└────────────────────────────────────────┘

Step 3: Blood Pressure (optional)
┌────────────────────────────────────────┐
│ 💉 Did you measure your BP today?      │
│                                         │
│ [Yes] [No]                             │
└────────────────────────────────────────┘

If Yes:
┌────────────────────────────────────────┐
│ Please enter BP (e.g., 120/80):        │
└────────────────────────────────────────┘

Step 4: Summary & Recommendations
┌────────────────────────────────────────┐
│ ✅ Check-in Complete!                  │
│                                         │
│ 📊 Status: 🟢 LOW Risk                │
│                                         │
│ 💡 Recommendations:                    │
│ • Stay hydrated (8 glasses water)      │
│ • Take your iron supplement            │
│ • Light walking for 20 minutes         │
│                                         │
│ Next check-in: Tomorrow 8:00 AM        │
└────────────────────────────────────────┘
```

---

## `/status` - Current Health Status

**Usage:** View current health status and recent assessments.

**Response:**
```
📊 Health Status for Priya Sharma

🗓️ Week: 28 of pregnancy

📈 Risk Level: 🟢 LOW
📉 Risk Score: 25/100

Recent Vitals:
• BP: 118/76 mmHg ✅
• Hemoglobin: 11.2 g/dL ✅
• Weight: 65 kg

👩‍⚕️ Assigned ASHA: Seema Patil
👨‍⚕️ Doctor: Dr. Meera Shah

Last Check-in: Today, 8:30 AM
Next Appointment: Jan 10, 2026

[📅 View Timeline] [🏥 Contact Doctor]
```

---

## `/timeline` - Health History

**Usage:** View the health journey over time.

**Response:**
```
📅 Health Timeline - Priya Sharma

────────────────────────────────
🔵 Jan 3, 2026 - Daily Check-in
   Status: Healthy
   BP: 118/76
────────────────────────────────
🟢 Jan 2, 2026 - Check-in
   Status: Healthy
   No symptoms reported
────────────────────────────────
📋 Jan 1, 2026 - Blood Test
   Hemoglobin: 11.2 g/dL
   Result: Normal
────────────────────────────────
🟡 Dec 30, 2025 - Check-in
   Mild headache reported
   Follow-up scheduled
────────────────────────────────
🎉 Dec 15, 2025 - Milestone
   Week 26 completed!
   Glucose test normal
────────────────────────────────

[Show More] [Export Report]
```

---

## `/report` - Report Symptoms

**Usage:** Report concerning symptoms outside of daily check-in.

### Symptom Reporting Flow

```
Step 1: Select Symptom Category
┌────────────────────────────────────────┐
│ 🏥 What would you like to report?      │
│                                         │
│ [🤕 Pain/Discomfort]                   │
│ [🤢 Nausea/Vomiting]                   │
│ [💫 Dizziness]                         │
│ [⚠️ Bleeding]                          │
│ [🔥 Fever]                             │
│ [📝 Other]                             │
└────────────────────────────────────────┘

Step 2: Severity
┌────────────────────────────────────────┐
│ How severe is the symptom?             │
│                                         │
│ [Mild] [Moderate] [Severe]             │
└────────────────────────────────────────┘

Step 3: Duration
┌────────────────────────────────────────┐
│ When did it start?                     │
│                                         │
│ [Just now] [Few hours] [Today]         │
│ [Yesterday] [Days ago]                 │
└────────────────────────────────────────┘

Step 4: AI Analysis & Response
┌────────────────────────────────────────┐
│ 📋 Symptom Report Submitted            │
│                                         │
│ Symptom: Severe Headache               │
│ Duration: 2 hours                      │
│                                         │
│ 🤖 AI Assessment:                      │
│ Your symptoms have been analyzed.      │
│ Current risk level: MODERATE           │
│                                         │
│ ⚠️ Recommendation:                     │
│ • Rest in a quiet, dark room           │
│ • Drink water                          │
│ • If headache persists with vision     │
│   changes, contact doctor immediately  │
│                                         │
│ 📢 Your ASHA worker has been notified. │
└────────────────────────────────────────┘
```

---

## `/help` - Show All Commands

**Usage:** Display all available commands and features.

**Response:**
```
📚 MatruRaksha Bot - Help Guide

🔹 Basic Commands:
/start    - Start bot and get chat ID
/register - Register as a new mother
/help     - Show this help message
/cancel   - Cancel current operation

🔹 Health Tracking:
/checkin  - Daily health check-in
/status   - View current health status
/timeline - View health history
/report   - Report symptoms

🔹 Features:
📱 Upload Documents - Send photos of medical reports
💬 Ask Questions - Type any health question
🚨 Emergency - Keywords trigger immediate response

🔹 Examples of Questions:
• "What foods increase hemoglobin?"
• "When should I take my iron tablets?"
• "Is mild cramping normal at 28 weeks?"

🔹 Emergency Keywords:
⚠️ Bleeding, severe pain, vision problems,
   difficulty breathing, unconscious

Need more help? Contact your ASHA worker.
```

---

## 📝 Natural Language Queries

The bot understands natural language queries and routes them to specialized AI agents.

### Example Queries & Responses

**Nutrition Query:**
```
User: What should I eat to increase my hemoglobin?

Bot: 🥗 Nutrition Advice for Anemia

Based on your current hemoglobin (10.5 g/dL), here are iron-rich 
foods to include in your diet:

🥬 Leafy Greens:
• Spinach (palak)
• Fenugreek leaves (methi)
• Amaranth leaves (lal saag)

🥜 Protein Sources:
• Eggs (especially yolk)
• Lentils (dal)
• Chickpeas (chana)

🍎 Fruits:
• Pomegranate
• Dates (khajoor)
• Dried apricots

💡 Tip: Eat vitamin C rich foods (orange, lemon) with 
iron-rich foods to improve absorption.

Avoid tea/coffee with meals as they reduce iron absorption.
```

**Medication Query:**
```
User: When should I take my iron tablets?

Bot: 💊 Iron Supplement Schedule

Best time to take iron tablets:
⏰ 1 hour before meals OR 2 hours after meals
   (Empty stomach for best absorption)

✅ DO:
• Take with orange juice or vitamin C
• Space 2 hours from calcium/antacids
• Take at the same time daily

❌ DON'T:
• Take with milk, tea, or coffee
• Take with calcium supplements
• Skip doses

Your scheduled reminder: 9:00 AM daily

[Set Custom Reminder]
```

---

## 📄 Document Upload

Mothers can upload medical reports for AI analysis.

### Upload Flow

```
Step 1: User sends photo/document
┌────────────────────────────────────────┐
│ [📷 Photo of blood test report]        │
└────────────────────────────────────────┘

Step 2: Processing
┌────────────────────────────────────────┐
│ 📄 Processing your document...         │
│ Please wait while our AI analyzes it.  │
└────────────────────────────────────────┘

Step 3: Analysis Results
┌────────────────────────────────────────┐
│ 📋 Report Analysis Complete!           │
│                                         │
│ Type: Blood Test Report                │
│ Date: Jan 2, 2026                      │
│                                         │
│ 📊 Key Findings:                       │
│ • Hemoglobin: 11.2 g/dL ✅ Normal      │
│ • Blood Sugar: 92 mg/dL ✅ Normal      │
│ • Platelet: 180,000 ✅ Normal          │
│                                         │
│ 💡 Summary:                            │
│ Your blood test results are normal.    │
│ Hemoglobin has improved from last test │
│ (was 10.5 g/dL).                       │
│                                         │
│ 📌 Saved to your health records.       │
│                                         │
│ [View Full Analysis] [Share with Doctor]│
└────────────────────────────────────────┘
```

---

## 🚨 Emergency Handling

The bot automatically detects emergency keywords and triggers immediate response.

### Emergency Keywords
- Bleeding (खून बह रहा है)
- Severe pain (तेज दर्द)
- Vision problems
- Difficulty breathing
- Unconscious
- Fainting (बेहोशी)
- Seizures

### Emergency Response

```
User: I am bleeding heavily

Bot: 
🚨 EMERGENCY ALERT 🚨

I understand you're experiencing bleeding.
This requires immediate attention.

⚡ IMMEDIATE ACTIONS:
1. Lie down on your left side
2. Do NOT put anything inside
3. Note the color and amount
4. Call emergency: 108 (Ambulance)

📞 Emergency Contacts:
• Ambulance: 108
• Dr. Meera Shah: 9100000001
• ASHA Seema Patil: 9000000001

🔔 ALERT SENT TO:
✅ Your assigned doctor
✅ Your ASHA worker
✅ Emergency responders

Stay calm. Help is on the way.
Your location has been shared.

[📍 Share Location] [📞 Call Doctor]
```

---

## 🏠 Dashboard Navigation

The bot's home screen provides quick access buttons.

### Home Dashboard

```
┌────────────────────────────────────────┐
│ 🏠 MatruRaksha Home                    │
│                                         │
│ Hello, Priya! 👋                       │
│ Week 28 • Risk: 🟢 LOW                 │
│                                         │
│ ┌─────────────────────────────────┐    │
│ │ 📋 Health Reports               │    │
│ │ View your uploaded reports      │    │
│ └─────────────────────────────────┘    │
│                                         │
│ ┌─────────────────────────────────┐    │
│ │ 👥 Switch Profiles              │    │
│ │ Manage linked profiles          │    │
│ └─────────────────────────────────┘    │
│                                         │
│ ┌─────────────────────────────────┐    │
│ │ 📤 Upload Documents             │    │
│ │ Send new medical reports        │    │
│ └─────────────────────────────────┘    │
│                                         │
│ ┌─────────────────────────────────┐    │
│ │ ➕ Register Another Mother      │    │
│ │ Add a family member             │    │
│ └─────────────────────────────────┘    │
│                                         │
└────────────────────────────────────────┘
```

---

## 🌍 Multilingual Support (Coming Soon)

The bot will support multiple Indian languages:
- Hindi (हिंदी)
- Tamil (தமிழ்)
- Telugu (తెలుగు)
- Bengali (বাংলা)
- Marathi (मराठी)
- Kannada (ಕನ್ನಡ)

---

## 📚 Related Documentation

- [Telegram Setup Guide](./telegram_setup.md)
- [API Endpoints](../api/telegram_endpoints.md)
- [System Design](../architecture/system_design.md)

---

*Last Updated: January 2026*
