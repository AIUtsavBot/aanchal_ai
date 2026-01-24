# 🔄 REVISED ARCHITECTURE - Single Integrated Website

## ❌ OLD CONCEPT (Discarded)
- Two separate websites
- MatruRaksha (port 5173)
- SantanRaksha (port 5174)

## ✅ NEW CONCEPT (Correct)

### Single Website: **MatruRaksha** (localhost:5173)

```
MatruRaksha Frontend (Single Website)
├── Login (ASHA Workers & Doctors)
├── Dashboard
│   ├── [Toggle/Switch Button]
│   │   ├── 🤰 Pregnancy View (MatruRaksha)
│   │   └── 🍼 Postnatal & Child View (SantanRaksha)
│   │
│   ├── IF Toggle = "Pregnancy View":
│   │   ├── Show pregnant mothers list
│   │   ├── Appointments
│   │   ├── Health Timeline
│   │   └── Risk Assessments
│   │
│   └── IF Toggle = "Postnatal & Child View":
│       ├── Show delivered mothers list
│       ├── Children registered
│       ├── Vaccination schedule
│       ├── Growth records
│       └── Postnatal check-ins
│
├── Routing:
│   ├── /dashboard → Main dashboard with toggle
│   ├── /pregnancy/* → MatruRaksha routes
│   └── /postnatal/* → SantanRaksha routes
│
└── Same ASHA/Doctor login for both views
```

---

## 📋 Implementation Steps

### 1. **Delete Separate Frontend** ✅
```bash
# Stop the separate SantanRaksha frontend
# Delete the directory
rm -rf frontend-santanraksha/
```

### 2. **Keep MatruRaksha Frontend** ✅
- Everything stays in `frontend/` (port 5173)
- No changes to existing MatruRaksha functionality

### 3. **Add SantanRaksha as Routes/Pages** ✅
```
frontend/
├── src/
│   ├── pages/
│   │   ├── Dashboard.tsx         # ✅ Keep existing
│   │   ├── pregnancy/            # ✅ Keep existing MatruRaksha pages
│   │   └── postnatal/            # ✨ NEW: Add SantanRaksha pages
│   │       ├── PostnatalDashboard.tsx
│   │       ├── ChildrenList.tsx
│   │       ├── VaccinationCalendar.tsx
│   │       ├── GrowthCharts.tsx
│   │       └── MilestonesTracker.tsx
│   │
│   ├── components/
│   │   ├── ViewToggle.tsx        # ✨ NEW: Pregnancy ↔ Postnatal toggle
│   │   └── ...existing components
│   │
│   └── App.tsx                   # ✅ Update routing
```

### 4. **Update Dashboard** ✅
Add toggle switch:
```tsx
<Dashboard>
  <ViewToggle 
    currentView={view}  // 'pregnancy' or 'postnatal'
    onChange={setView}
  />
  
  {view === 'pregnancy' ? (
    <PregnancyView />   // Existing MatruRaksha
  ) : (
    <PostnatalView />   // New SantanRaksha
  )}
</Dashboard>
```

### 5. **Backend** ✅ Already Ready!
- ✅ Orchestrator already checks `active_system`
- ✅ Delivery API already switches systems
- ✅ All SantanRaksha agents working
- **NO BACKEND CHANGES NEEDED!**

---

## 🗑️ Files to DELETE

### Delete Entire `frontend-santanraksha` Directory:
```
d:\SantanRaksha\frontend-santanraksha\
├── src/
├── node_modules/
├── package.json
├── vite.config.ts
└── ... (delete everything)
```

### Commands:
```bash
# 1. Stop the running SantanRaksha frontend
# (Kill the npm process on port 5174)

# 2. Delete the directory
cd d:\SantanRaksha
rm -rf frontend-santanraksha
```

---

## ✨ What to ADD to MatruRaksha Frontend

### 1. **View Toggle Component**
```tsx
// components/ViewToggle.tsx
export function ViewToggle({ currentView, onChange }) {
  return (
    <div className="view-toggle">
      <button 
        className={currentView === 'pregnancy' ? 'active' : ''}
        onClick={() => onChange('pregnancy')}
      >
        🤰 Pregnancy Care
      </button>
      <button 
        className={currentView === 'postnatal' ? 'active' : ''}
        onClick={() => onChange('postnatal')}
      >
        🍼 Postnatal & Child Care
      </button>
    </div>
  );
}
```

### 2. **Postnatal Routes**
```tsx
// App.tsx
<Routes>
  {/* Existing MatruRaksha routes */}
  <Route path="/dashboard" element={<Dashboard />} />
  <Route path="/mothers" element={<MothersList />} />
  
  {/* NEW: SantanRaksha routes */}
  <Route path="/postnatal/dashboard" element={<PostnatalDashboard />} />
  <Route path="/postnatal/children" element={<ChildrenList />} />
  <Route path="/postnatal/vaccines" element={<VaccinationCalendar />} />
  <Route path="/postnatal/growth" element={<GrowthCharts />} />
</Routes>
```

### 3. **Updated Navigation**
```tsx
// Navigation.tsx
{currentView === 'pregnancy' ? (
  <Nav>
    <Link to="/dashboard">Dashboard</Link>
    <Link to="/mothers">Mothers</Link>
    <Link to="/appointments">Appointments</Link>
  </Nav>
) : (
  <Nav>
    <Link to="/postnatal/dashboard">Dashboard</Link>
    <Link to="/postnatal/children">Children</Link>
    <Link to="/postnatal/vaccines">Vaccines</Link>
    <Link to="/postnatal/growth">Growth</Link>
  </Nav>
)}
```

---

## 🎯 User Flow

### ASHA Worker Login:
1. Login to MatruRaksha (localhost:5173)
2. See Dashboard with **toggle switch** at top
3. Default view: **🤰 Pregnancy Care** (existing MatruRaksha)
4. Click toggle → Switch to **🍼 Postnatal & Child Care**
5. Now sees:
   - List of delivered mothers
   - Their children
   - Vaccination schedules
   - Growth records

### When Mother Delivers:
1. Doctor marks delivery complete (existing flow)
2. `active_system` switches to 'santanraksha' in database
3. Mother appears in **Postnatal view** (when ASHA toggles to it)
4. Mother disappears from **Pregnancy view**

---

## 📊 Summary

| Aspect | Old (Wrong) | New (Correct) |
|--------|-------------|---------------|
| **Frontends** | 2 separate websites | 1 website with toggle |
| **Ports** | 5173 + 5174 | Only 5173 |
| **Login** | Separate logins | Same login |
| **Navigation** | Different sites | Toggle switch |
| **ASHA/Doctor** | Choose which site | Toggle views in dashboard |
| **Backend** | Same | Same (no changes) |

---

## ✅ Action Plan

1. **Stop** the `frontend-santanraksha` dev server
2. **Delete** the `frontend-santanraksha/` directory
3. **Keep** everything in `frontend/` (MatruRaksha)
4. **Add** SantanRaksha pages to `frontend/src/pages/postnatal/`
5. **Add** toggle component to dashboard
6. **Update** routing in MatruRaksha frontend
7. **Test** switching between views

---

**NO BACKEND CHANGES NEEDED** - The backend is already perfect! It automatically routes to correct agents based on `active_system` field.

---

**Ready to proceed with this new architecture?** ✅
