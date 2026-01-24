# MatruRaksha AI - Telegram Bot Commands

> Complete reference for Telegram bot commands and interactions

---

## Getting Started

### Finding the Bot
1. Open Telegram app
2. Search for your bot username (e.g., `@MatruRakshaBot`)
3. Click **Start** or send `/start`

---

## Available Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot and show home dashboard |
| `/cancel` | Cancel current operation |

> **Note**: Most interactions use **inline buttons** rather than commands for a better user experience.

---

## Quick Greetings

The bot responds to simple greetings like a regular conversation:

- **"Hi"** - Opens the home dashboard
- **"Hello"** - Opens the home dashboard
- **"Hey"** - Opens the home dashboard

---

## Home Dashboard

After registration, the bot shows a **home dashboard** with:

### Profile Card
```
🤰 MatruRaksha AI
━━━━━━━━━━━━━━━━━━━━━━━━

👩 Anjali Sharma
📞 +91 98765 43210

📅 Due Date: Jun 15, 2026
⏰ Week 24 of pregnancy

📍 Pune, Maharashtra
🗣️ Language: Hindi
```

### Action Buttons

| Button | Action |
|--------|--------|
| **📊 Health Summary** | View detailed health summary with metrics |
| **📤 Upload Report** | Upload medical documents for AI analysis |
| **📝 Check-in** | Daily health check-in |
| **🚨 Emergency** | Send SOS alert to healthcare providers |
| **👥 Switch Profile** | Switch between registered mothers |
| **➕ Register New** | Register additional mother |

---

## Registration Flow

When registering a new mother, the bot collects:

### Step 1: Name
```
What is the mother's full name?
> Anjali Sharma
```

### Step 2: Age
```
How old is she? (in years)
> 28
```

### Step 3: Phone
```
What is her mobile number?
> 9876543210
```

### Step 4: Due Date
```
Expected delivery date? (DD/MM/YYYY)
> 15/06/2026
```

### Step 5: Location
```
Which city/village does she live in?
> Pune
```

### Step 6: Gravida
```
Number of pregnancies (including current)?
> 2
```

### Step 7: Parity
```
Number of previous live births?
> 1
```

### Step 8: BMI
```
Body Mass Index (weight in kg / height in m²)?
(Example: 24.5)
> 24.5
```

### Step 9: Preferred Language
```
Choose preferred language:
[English] [Hindi] [Marathi]
```

### Step 10: Confirmation
```
Please confirm the registration:

👩 Name: Anjali Sharma
📞 Phone: 9876543210
🎂 Age: 28 years
📅 Due Date: 15/06/2026
📍 Location: Pune
🤰 Gravida: 2
👶 Parity: 1
⚖️ BMI: 24.5
🗣️ Language: Hindi

[✅ Confirm] [❌ Cancel]
```

---

## Health Summary

The **📊 Health Summary** shows comprehensive health information:

```
📊 Health Summary for Anjali Sharma
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 Pregnancy Week: 24
📆 Last Check-up: Jan 3, 2026

📈 Latest Vitals:
• Blood Pressure: 118/76 mmHg ✅
• Hemoglobin: 11.2 g/dL ✅
• Blood Sugar: 95 mg/dL ✅
• Weight: 62 kg

⚠️ Concerns:
• Mild fatigue reported

💊 Current Medications:
• Iron + Folic Acid (daily)
• Calcium (twice daily)

📋 Upcoming Appointments:
• Ultrasound - Jan 10, 2026

🔬 Recent Reports:
• Blood Test (Jan 2) - Analyzed ✅

💡 AI Recommendations:
• Continue current medications
• Stay hydrated
• Light walking recommended
```

---

## Document Upload

When you click **📤 Upload Report** or send a document:

### Supported Formats
- **PDF** documents
- **Images** (JPG, PNG, WebP)

### Upload Flow
1. Click **📤 Upload Report** or just send the document
2. Bot acknowledges receipt
3. AI analysis begins (takes 10-30 seconds)
4. Results are displayed

### Analysis Results
```
🔍 Report Analysis Complete

📊 Risk Level: LOW ✅

📋 Extracted Data:
• Hemoglobin: 11.5 g/dL
• Blood Pressure: 120/80 mmHg
• Blood Sugar: 98 mg/dL

💡 Recommendations:
• Continue iron supplementation
• Maintain healthy diet
• Next checkup in 2 weeks
```

If high-risk findings are detected:
```
🚨 ATTENTION REQUIRED

📊 Risk Level: HIGH ⚠️

⚠️ Concerns Detected:
• Low hemoglobin (8.5 g/dL)
• Elevated blood pressure

🏥 Recommended Actions:
• Contact your doctor immediately
• Increase iron-rich foods
• Monitor blood pressure daily

📞 Your assigned doctor has been notified.
```

---

## Emergency Alert

The **🚨 Emergency** button sends immediate alerts:

```
🚨 EMERGENCY ALERT SENT

Your emergency has been forwarded to:
• Dr. Meera Shah (Doctor)
• Seema Patil (ASHA Worker)

📞 They will contact you shortly.

If this is a medical emergency,
please also call 108 (Ambulance).
```

### What Happens Behind the Scenes
1. Alert message sent to assigned doctor (email)
2. Alert sent to assigned ASHA worker (email/SMS)
3. Emergency logged in system
4. Mother's location shared with responders

---

## Multi-Profile Support

One Telegram account can manage multiple mothers (useful for ASHA workers):

### Switch Profile
Click **👥 Switch Profile** to see registered mothers:
```
Select a profile to switch to:

[👩 Anjali Sharma - Pune]
[👩 Priya Devi - Nashik]
[👩 Suman Kumari - Mumbai]
```

### Register Additional Mother
Click **➕ Register New** to add another mother to your account.

---

## Daily Check-in

The **📝 Check-in** feature collects daily health data:

```
📝 Daily Check-in for Anjali

How are you feeling today?
[😊 Good] [😐 Okay] [😟 Not Well]

Any symptoms?
[Headache] [Fatigue] [Swelling]
[Nausea] [Bleeding] [None]

Did you take your medications today?
[✅ Yes] [❌ No]
```

After submission:
```
✅ Check-in recorded!

Your AI health companion says:
"Great! Your symptoms look normal.
Keep staying hydrated and get
plenty of rest. 💪"
```

---

## Language Support

The bot supports multiple languages:

| Code | Language | Greeting |
|------|----------|----------|
| `en` | English | Welcome! |
| `hi` | Hindi | स्वागत है! |
| `mr` | Marathi | स्वागत आहे! |

To change language:
1. Go to profile settings
2. Select new language
3. All messages will be in selected language

---

## Error Messages

### Common Errors

**Not Registered:**
```
You haven't registered yet.
Tap the button below to get started!

[📝 Register]
```

**Invalid Input:**
```
⚠️ Invalid input. Please try again.
Expected: A number between 1-50
```

**Upload Failed:**
```
❌ Upload failed. Please try again.

Supported formats:
• PDF documents
• JPG, PNG, WebP images
• Max size: 10 MB
```

---

## Tips for Users

1. **Keep documents clear**: For best AI analysis, ensure documents are:
   - Well-lit
   - Not blurry
   - All text visible

2. **Regular check-ins**: Daily check-ins help track health trends

3. **Emergency button**: Only use for real emergencies

4. **Language setting**: Set to your preferred language for easier use

5. **Multiple profiles**: ASHA workers can manage multiple mothers from one account

---

*Last updated: January 2026*
