# 🍼 SantanRaksha - Postnatal & Child Care Extension

> Extension of MatruRaksha for Postnatal Mother Care and Child Health Monitoring (0-5 years)

---

## 📋 Quick Overview

| Aspect | Details |
|--------|---------|
| **Purpose** | Extend MatruRaksha pregnancy care to postnatal recovery and child health |
| **Target Users** | ASHA Workers, Doctors, Mothers with newborns |
| **View Toggle** | Single app with toggle between Pregnancy Care ↔ Postnatal Care |
| **Key Features** | Vaccination tracking, Growth monitoring, Milestone tracking, Postnatal recovery |
| **Clinical Standards** | IAP 2023, WHO Growth Standards, RBSK 4Ds, NHM SUMAN, IMNCI |

---

## 🏗️ Architecture

### Single Website, Two Views

```
┌─────────────────────────────────────────────────────────────────┐
│                    MatruRaksha Frontend (:5173)                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Blue Navbar: [🤰 Pregnancy] [🍼 Postnatal] ←── Toggle     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│              ┌───────────────┴───────────────┐                  │
│              ▼                               ▼                  │
│  ┌──────────────────────┐       ┌──────────────────────┐       │
│  │   MatruRaksha View   │       │  SantanRaksha View   │       │
│  │   (Pregnancy Care)   │       │  (Postnatal Care)    │       │
│  │                      │       │                      │       │
│  │ • Mother registration│       │ • Children list      │       │
│  │ • Risk assessments   │       │ • Vaccination tracker│       │
│  │ • Symptom tracking   │       │ • Growth charts      │       │
│  │ • Chat history       │       │ • Milestone tracker  │       │
│  └──────────────────────┘       └──────────────────────┘       │
│                              │                                   │
│                              ▼                                   │
│              ┌───────────────────────────────┐                  │
│              │     FastAPI Backend (:8000)   │                  │
│              │  Same backend for both views  │                  │
│              └───────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure (New Files)

### Backend - AI Agents

| File | Purpose | Standards |
|------|---------|-----------|
| `backend/agents/postnatal_agent.py` | Postnatal recovery care | NHM SUMAN, EPDS |
| `backend/agents/pediatric_agent.py` | Child illness assessment | IMNCI |
| `backend/agents/vaccine_agent.py` | Vaccination guidance | IAP 2023 |
| `backend/agents/growth_agent.py` | Growth monitoring | WHO z-scores, RBSK |

### Backend - Routes

| File | Purpose |
|------|---------|
| `backend/routes/delivery.py` | Delivery completion API, system switching |

### Frontend - Postnatal Pages

| File | Purpose |
|------|---------|
| `frontend/src/pages/postnatal/PostnatalDashboard.jsx` | Main dashboard with tabs |
| `frontend/src/pages/postnatal/ChildrenList.jsx` | Children registry |
| `frontend/src/pages/postnatal/VaccinationCalendar.jsx` | IAP 2023 vaccine tracking |
| `frontend/src/pages/postnatal/GrowthCharts.jsx` | WHO growth monitoring |
| `frontend/src/pages/postnatal/MilestonesTracker.jsx` | RBSK 4Ds milestones |
| `frontend/src/pages/postnatal/PostnatalDashboard.css` | Dashboard styling |
| `frontend/src/pages/postnatal/PostnatalPages.css` | Shared page styles |

### Frontend - Components

| File | Purpose |
|------|---------|
| `frontend/src/components/ViewToggle.jsx` | Toggle component (used in Navbar) |
| `frontend/src/components/ViewToggle.css` | Toggle styling |
| `frontend/src/contexts/ViewContext.jsx` | Global view state management |

### Database Migrations

| File | Purpose |
|------|---------|
| `infra/supabase/migration_santanraksha_v1.sql` | Children, vaccinations, growth, milestones tables |
| `infra/supabase/migration_delivery_switch.sql` | Delivery completion, active_system switch |

---

## 🗄️ Database Schema

### New Tables

```sql
-- Children (linked to mothers)
CREATE TABLE children (
  id UUID PRIMARY KEY,
  mother_id UUID REFERENCES mothers(id),
  name VARCHAR(255),
  gender VARCHAR(20),
  birth_date DATE,
  birth_weight_kg DECIMAL(4,2),
  birth_length_cm DECIMAL(5,2),
  birth_type VARCHAR(50)  -- normal, cesarean, assisted
);

-- Vaccinations (IAP 2023 schedule)
CREATE TABLE vaccinations (
  id UUID PRIMARY KEY,
  child_id UUID REFERENCES children(id),
  vaccine_name VARCHAR(100),
  due_date DATE,
  administered_date TIMESTAMP,
  status VARCHAR(20)  -- pending, due, overdue, completed
);

-- Growth Records (WHO standards)
CREATE TABLE growth_records (
  id UUID PRIMARY KEY,
  child_id UUID REFERENCES children(id),
  measurement_date DATE,
  weight_kg DECIMAL(5,2),
  height_cm DECIMAL(5,2),
  head_circumference_cm DECIMAL(5,2),
  weight_for_age_z DECIMAL(4,2),
  height_for_age_z DECIMAL(4,2)
);

-- Developmental Milestones (RBSK 4Ds)
CREATE TABLE milestones (
  id UUID PRIMARY KEY,
  child_id UUID REFERENCES children(id),
  milestone_name VARCHAR(255),
  milestone_category VARCHAR(50),  -- Motor, Language, Cognitive, Social
  achieved_date TIMESTAMP
);
```

---

## 🤖 AI Agents Summary

### PostnatalAgent
- **Focus**: Mother's recovery (0-6 weeks)
- **Features**: Bleeding assessment, breastfeeding support, mental health (EPDS)
- **Standards**: NHM SUMAN, WHO postnatal guidelines

### PediatricAgent
- **Focus**: Child illness assessment
- **Features**: Fever, diarrhea, respiratory illness triage
- **Standards**: IMNCI algorithms

### VaccineAgent
- **Focus**: Immunization guidance
- **Features**: Full IAP 2023 schedule (19 vaccines), side effects, hesitancy counseling
- **Standards**: IAP 2023 Immunization Schedule

### GrowthAgent
- **Focus**: Growth and nutrition
- **Features**: WHO z-score calculations, malnutrition screening, IYCF feeding plans
- **Standards**: WHO Child Growth Standards, RBSK, WHO IYCF

---

## 🩺 Clinical Standards

| Standard | Application |
|----------|-------------|
| **IAP 2023** | Vaccination schedule - 19 vaccines from birth to 2 years |
| **WHO Growth Standards** | Z-score classification for weight-for-age, height-for-age |
| **RBSK 4Ds** | Developmental screening - Defects, Diseases, Deficiencies, Delays |
| **NHM SUMAN** | Postnatal care guidelines - 6 checkups in 42 days |
| **IMNCI** | Integrated child illness management algorithms |
| **WHO IYCF** | Infant and young child feeding recommendations |
| **EPDS** | Edinburgh Postnatal Depression Scale |

---

## 🔧 How to Use

### 1. Toggle Between Views
- Look for toggle in **blue navbar** at top
- Click **"🤰 Pregnancy"** for MatruRaksha
- Click **"🍼 Postnatal"** for SantanRaksha

### 2. Postnatal Dashboard Tabs
- **Dashboard**: Overview with stats
- **Children**: View/register children
- **Vaccines**: IAP 2023 vaccination tracking
- **Growth**: WHO growth monitoring with z-scores
- **Milestones**: RBSK 4Ds developmental tracking

### 3. Database Switch
When a mother delivers, call the API:
```bash
POST /api/delivery/complete/{mother_id}
{
  "delivery_date": "2026-01-20",
  "delivery_type": "normal",
  "baby_weight": 3.2,
  "baby_gender": "female"
}
```

This:
1. Creates a child record linked to mother
2. Sets mother's `active_system = 'santanraksha'`
3. Generates vaccination schedule for baby


---

## 📊 Files Modified

| File | Changes |
|------|---------|
| `frontend/src/App.jsx` | Added ViewProvider wrapper |
| `frontend/src/components/Navbar.jsx` | Added toggle for ASHA/Doctor roles |
| `frontend/src/pages/ASHAInterface.jsx` | Uses ViewContext, switches to postnatal |
| `frontend/src/pages/DoctorDashboard.jsx` | Uses ViewContext, switches to postnatal |
| `backend/agents/__init__.py` | Exports new agents |
| `backend/agents/orchestrator.py` | Routes to SantanRaksha agents |

---

## 🚀 Deployment Checklist

- [x] AI Agents: PostnatalAgent, PediatricAgent, VaccineAgent, GrowthAgent
- [x] Database migrations ready
- [x] Frontend postnatal pages complete
- [x] View toggle in navbar
- [x] ASHA and Doctor dashboards integrated
- [ ] Deploy migrations to Supabase
- [ ] Test with real data
- [ ] Mobile responsive testing

---

## 🔗 Quick Links

| Resource | Path |
|----------|------|
| Main README | `README.md` |
| Changelog | `CHANGELOG.md` |
| API Docs | `docs/API_SPECIFICATION.md` |
| Database Migrations | `infra/supabase/migration_*.sql` |

---

*Last Updated: January 24, 2026*
