# 🔄 Migration Guide: Two Websites → Single Integrated Website

## ⚠️ MANUAL STEPS REQUIRED

### Step 1: Stop the SantanRaksha Frontend
1. Find the terminal running `npm run dev` in `frontend-santanraksha`
2. Press `Ctrl + C` to stop it
3. Wait for the process to terminate

### Step 2: Delete the Separate Frontend Directory
```bash
# After stopping the dev server, delete the folder
cd d:\SantanRaksha
# Manually delete or use:
rmdir /s frontend-santanraksha
```

**Or manually:**
- Navigate to `d:\SantanRaksha\`
- Delete the `frontend-santanraksha` folder

---

## ✅ What to Keep

### Backend (No Changes Needed) ✅
- All agents work correctly
- Orchestrator already checks `active_system`
- Delivery API ready
- **Keep everything in `backend/` as-is!**

### Database Migrations ✅
- `migration_santanraksha_v1.sql` - Child health tables
- `migration_delivery_switch.sql` - System switching
- **Keep both migration files!**

### MatruRaksha Frontend ✅  
- Keep entire `frontend/` directory
- **This will become the single integrated website**

---

## 🚀 Next Steps: Add SantanRaksha to MatruRaksha Frontend

### 1. Create Postnatal Pages Directory
```bash
cd d:\SantanRaksha\frontend\src
mkdir pages\postnatal
```

### 2. Add View Toggle to Dashboard
Create: `frontend/src/components/ViewToggle.tsx`

```tsx
import { useState } from 'react';

export type ViewMode = 'pregnancy' | 'postnatal';

interface ViewToggleProps {
  currentView: ViewMode;
  onViewChange: (view: ViewMode) => void;
}

export function ViewToggle({ currentView, onViewChange }: ViewToggleProps) {
  return (
    <div className="view-toggle">
      <button
        className={`toggle-btn ${currentView === 'pregnancy' ? 'active' : ''}`}
        onClick={() => onViewChange('pregnancy')}
      >
        🤰 Pregnancy Care
      </button>
      <button
        className={`toggle-btn ${currentView === 'postnatal' ? 'active' : ''}`}
        onClick={() => onViewChange('postnatal')}
      >
        🍼 Postnatal & Child Care
      </button>
    </div>
  );
}
```

### 3. Update Dashboard Component
Update: `frontend/src/pages/Dashboard.tsx` (or wherever dashboard is)

```tsx
import { useState } from 'react';
import { ViewToggle, ViewMode } from '../components/ViewToggle';
import { PregnancyDashboard } from './pregnancy/PregnancyDashboard'; // Existing
import { PostnatalDashboard } from './postnatal/PostnatalDashboard'; // New

export function Dashboard() {
  const [currentView, setCurrentView] = useState<ViewMode>('pregnancy');

  return (
    <div className="dashboard">
      <h1>MatruRaksha Dashboard</h1>
      
      {/* Toggle Switch */}
      <ViewToggle 
        currentView={currentView}
        onViewChange={setCurrentView}
      />

      {/* Conditional rendering based on view */}
      {currentView === 'pregnancy' ? (
        <PregnancyDashboard />  // Existing MatruRaksha view
      ) : (
        <PostnatalDashboard />  // New SantanRaksha view
      )}
    </div>
  );
}
```

### 4. Create Postnatal Dashboard
Create: `frontend/src/pages/postnatal/PostnatalDashboard.tsx`

```tsx
export function PostnatalDashboard() {
  return (
    <div className="postnatal-dashboard">
      <h2>Postnatal & Child Care Dashboard</h2>
      
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Delivered Mothers</h3>
          <p className="stat-number">0</p>
        </div>
        <div className="stat-card">
          <h3>Children Registered</h3>
          <p className="stat-number">0</p>
        </div>
        <div className="stat-card">
          <h3>Vaccines Due</h3>
          <p className="stat-number">0</p>
        </div>
        <div className="stat-card">
          <h3>Growth Alerts</h3>
          <p className="stat-number">0</p>
        </div>
      </div>

      {/* Add more sections */}
      <div className="quick-actions">
        <button>View All Children</button>
        <button>Vaccination Calendar</button>
        <button>Growth Charts</button>
        <button>Postnatal Check-ins</button>
      </div>
    </div>
  );
}
```

### 5. Add Routing (if using React Router)
Update: `frontend/src/App.tsx`

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Existing routes */}
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/mothers" element={<MothersList />} />
        
        {/* NEW: Postnatal routes */}
        <Route path="/postnatal/children" element={<ChildrenList />} />
        <Route path="/postnatal/vaccines" element={<VaccinationCalendar />} />
        <Route path="/postnatal/growth" element={<GrowthCharts />} />
        <Route path="/postnatal/milestones" element={<MilestonesTracker />} />
      </Routes>
    </BrowserRouter>
  );
}
```

### 6. Style the Toggle
Add to your CSS file:

```css
.view-toggle {
  display: flex;
  gap: 1rem;
  margin: 2rem 0;
  justify-content: center;
}

.toggle-btn {
  padding: 1rem 2rem;
  border: none;
  background: #f3f4f6;
  color: #374151;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.toggle-btn:hover {
  background: #e5e7eb;
  transform: translateY(-2px);
}

.toggle-btn.active {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
}
```

---

## 📊 Final Architecture

```
MatruRaksha Website (localhost:5173)
│
├── Login (ASHA/Doctor)
│
├── Dashboard
│   ├── [Toggle: Pregnancy ↔ Postnatal]
│   │
│   ├── Pregnancy View (Default):
│   │   ├── Pregnant mothers list
│   │   ├── Appointments
│   │   ├── Risk assessments
│   │   └── Health timeline
│   │
│   └── Postnatal View:
│       ├── Delivered mothers list
│       ├── Children registry
│       ├── Vaccination calendar
│       ├── Growth monitoring
│       └── Postnatal check-ins
│
├── Routes:
│   ├── /dashboard → Main with toggle
│   ├── /mothers → Pregnancy list
│   ├── /postnatal/children → Children list
│   ├── /postnatal/vaccines → Vaccine schedule
│   └── /postnatal/growth → Growth charts
│
└── Backend API (localhost:8000)
    └── Auto-routes based on active_system
```

---

## 🎯 Benefits of This Approach

✅ **Single login** for ASHA/Doctor  
✅ **No separate website** to maintain  
✅ **Easy toggle** between views  
✅ **MatruRaksha unchanged** - just extended  
✅ **Same codebase** - easier to maintain  
✅ **Backend already ready** - no changes needed  

---

## 📝 Summary of Changes

### DELETE:
- ❌ `frontend-santanraksha/` directory (entire folder)

### KEEP:
- ✅ `backend/` - No changes
- ✅ `frontend/` - Add postnatal pages
- ✅ `infra/supabase/` - Keep migrations
- ✅ `docs/` - Keep documentation

### ADD to `frontend/`:
- ✨ `src/components/ViewToggle.tsx`
- ✨ `src/pages/postnatal/PostnatalDashboard.tsx`
- ✨ `src/pages/postnatal/ChildrenList.tsx`
- ✨ `src/pages/postnatal/VaccinationCalendar.tsx`
- ✨ `src/pages/postnatal/GrowthCharts.tsx`
- ✨ Update `src/pages/Dashboard.tsx`
- ✨ Update routing in `src/App.tsx`

---

## 🚀 Ready to Start?

1. **Stop** the SantanRaksha frontend (Ctrl+C in terminal)
2. **Delete** `frontend-santanraksha/` folder
3. **Open** the MatruRaksha frontend codebase
4. **Add** the new components as described above
5. **Test** the toggle functionality

**Backend is already perfect - no changes needed!** ✅
