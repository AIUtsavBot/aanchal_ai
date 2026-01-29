
import os

file_path = r"d:\SantanRaksha\frontend\src\pages\postnatal\PostnatalAssessments.jsx"

child_profile_code = r"""
    const renderChildClinicalProfile = (child) => (
        <div className="bg-white rounded-xl shadow-md border border-gray-200 p-5 overflow-y-auto mb-4" style={{ minWidth: '300px' }}>
            <h3 className="text-lg font-bold text-gray-900 mb-5 flex items-center gap-2">
                <Baby className="w-5 h-5 text-blue-600" />
                Child Profile
            </h3>
            <div className="space-y-4 text-sm">
                <div className="pb-3 border-b">
                    <label className="text-xs font-bold text-gray-500 uppercase">Name</label>
                    <p className="text-gray-900 font-semibold mt-1">{child.name}</p>
                </div>
                <div className="grid grid-cols-2 gap-3 pb-3 border-b">
                    <div>
                        <label className="text-xs font-bold text-gray-500 uppercase">Gender</label>
                        <p className="text-gray-900 font-semibold mt-1 capitalize">{child.gender}</p>
                    </div>
                    <div>
                        <label className="text-xs font-bold text-gray-500 uppercase">Birth Weight</label>
                        <p className="text-gray-900 font-semibold mt-1">{child.birth_weight_kg ? `${child.birth_weight_kg} kg` : 'N/A'}</p>
                    </div>
                </div>
                <div>
                     <label className="text-xs font-bold text-gray-500 uppercase">Date of Birth</label>
                     <p className="text-gray-900 font-semibold mt-1">
                         {child.birth_date ? new Date(child.birth_date).toLocaleDateString() : 'N/A'}
                     </p>
                </div>
            </div>
        </div>
    );
"""

new_child_assessments_code = r"""    // Child Assessments Tab
    const renderChildAssessments = () => (
        <div className="child-assessments">
            <div className="section-header">
                <h3>👶 Child Health Checks</h3>
                <p>Monitor newborn and infant health, growth, and development</p>
                <button
                    className="btn-primary"
                    style={{ marginTop: '10px' }}
                    onClick={() => setShowForm('register_child')}
                >
                    <UserPlus size={16} /> Register Child
                </button>
            </div>

            {/* Child Registration Form */}
            {showForm === 'register_child' && (
                <div className="assessment-panel">
                    <div className="panel-header">
                        <h4>👶 Register New Child</h4>
                        <button className="btn-secondary" onClick={() => setShowForm(null)}>
                            <X size={16} /> Cancel
                        </button>
                    </div>
                     <div className="assessment-form">
                        <div className="form-section">
                            <h6>Child Details</h6>
                            <div className="form-row">
                                <div className="form-field">
                                    <label>Name</label>
                                    <input
                                        type="text"
                                        value={newChild.name}
                                        onChange={e => setNewChild({ ...newChild, name: e.target.value })}
                                        placeholder="Enter child name"
                                    />
                                </div>
                                <div className="form-field">
                                    <label>Birth Date *</label>
                                    <input
                                        type="date"
                                        max={new Date().toISOString().split('T')[0]}
                                        value={newChild.birth_date}
                                        onChange={e => setNewChild({ ...newChild, birth_date: e.target.value })}
                                    />
                                </div>
                            </div>
                            <div className="form-row">
                                <div className="form-field">
                                    <label>Gender *</label>
                                    <select
                                        value={newChild.gender}
                                        onChange={e => setNewChild({ ...newChild, gender: e.target.value })}
                                    >
                                        <option value="male">Male</option>
                                        <option value="female">Female</option>
                                        <option value="other">Other</option>
                                    </select>
                                </div>
                                <div className="form-field">
                                    <label>Birth Weight (kg)</label>
                                    <input
                                        type="number"
                                        step="0.1"
                                        value={newChild.birth_weight_kg}
                                        onChange={e => setNewChild({ ...newChild, birth_weight_kg: e.target.value })}
                                        placeholder="e.g. 3.2"
                                    />
                                </div>
                            </div>
                            <div className="form-actions">
                                <button className="btn-secondary" onClick={() => setShowForm(null)}>Cancel</button>
                                <button className="btn-primary" onClick={handleRegisterChild}>Register Child</button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Child List */}
            <div className="patient-list">
                {children.length === 0 ? (
                    <div className="empty-state">
                        <Baby size={48} />
                        <p>No children registered yet</p>
                        <span>Children will appear after being added during delivery completion or registration</span>
                    </div>
                ) : (
                    <div className="patient-cards">
                        {children.map(child => (
                            <div
                                key={child.id}
                                className={`patient-card child ${selectedChild?.id === child.id ? 'selected' : ''}`}
                                onClick={() => {
                                    setSelectedChild(child);
                                    loadAssessments(null, child.id);
                                }}
                            >
                                <div className="patient-avatar child">
                                    {child.gender === 'male' ? '👦' : '👧'}
                                </div>
                                <div className="patient-info">
                                    <h4>{child.name}</h4>
                                    <p>Born: {child.birth_date}</p>
                                    <p>Weight: {child.birth_weight_kg || '?'} kg</p>
                                </div>
                                <div className="patient-status">
                                    {getRiskBadge('low')}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Assessment Form / Details for Child */}
            {selectedChild && (
                <div className="assessment-panel">
                    {/* Header */}
                   <div className="bg-white border-b border-gray-200 px-8 py-6 shadow-sm mb-6 rounded-lg">
                        <div className="flex items-center justify-between">
                            <div>
                                <div className="flex items-center gap-3">
                                    <h2 className="text-2xl font-bold text-gray-900">{selectedChild.name}</h2>
                                     <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-xs font-bold border border-blue-200 uppercase tracking-wide">
                                        Child
                                    </span>
                                </div>
                                <p className="text-gray-600 mt-1 flex items-center gap-2 text-sm">
                                    <Calendar className="w-4 h-4" /> Born: {selectedChild.birth_date} · {selectedChild.gender === 'male' ? 'Boy' : 'Girl'}
                                </p>
                            </div>
                             <div className="flex gap-2">
                                <button
                                    onClick={() => setSelectedChild(null)}
                                    className="px-4 py-2 rounded-lg font-semibold text-sm bg-gray-100 text-gray-700 flex items-center gap-2 hover:bg-gray-200"
                                >
                                    <X size={16} /> Close
                                </button>
                            </div>
                        </div>
                        
                        {/* Tabs */}
                        <div className="flex gap-3 mt-4 flex-wrap">
                            <button
                                className={`px-4 py-2 rounded-lg font-semibold text-sm flex items-center gap-2 ${showForm !== 'child' ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-700"}`}
                                onClick={() => setShowForm(null)}
                            >
                                <FileText className="w-4 h-4" /> Health History
                            </button>
                            <button
                                className={`px-4 py-2 rounded-lg font-semibold text-sm flex items-center gap-2 ${showForm === 'child' ? "bg-green-600 text-white" : "bg-gray-100 text-gray-700"}`}
                                onClick={() => setShowForm('child')}
                            >
                                <Plus className="w-4 h-4" /> New Health Check
                            </button>
                        </div>
                   </div>

                    <div className="flex gap-6 items-start">
                        {/* Left: Clinical Profile */}
                        {renderChildClinicalProfile(selectedChild)}

                        {/* Right: Content */}
                        <div className="flex-1 bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden flex flex-col p-4">
                            {showForm === 'child' ? (
                                <div className="assessment-form">
                                    <h5>📝 Child Health Check Form</h5>

                                    <div className="form-section">
                                        <h6>Growth Measurements</h6>
                                        <div className="form-row">
                                            <div className="form-field">
                                                <label>Weight (kg)</label>
                                                <input
                                                    type="number"
                                                    step="0.01"
                                                    value={childAssessment.weight_kg}
                                                    onChange={e => setChildAssessment({ ...childAssessment, weight_kg: e.target.value })}
                                                    placeholder="e.g., 3.5"
                                                />
                                            </div>
                                            <div className="form-field">
                                                <label>Length (cm)</label>
                                                <input
                                                    type="number"
                                                    step="0.1"
                                                    value={childAssessment.length_cm}
                                                    onChange={e => setChildAssessment({ ...childAssessment, length_cm: e.target.value })}
                                                    placeholder="e.g., 50"
                                                />
                                            </div>
                                            <div className="form-field">
                                                <label>Head Circumference (cm)</label>
                                                <input
                                                    type="number"
                                                    step="0.1"
                                                    value={childAssessment.head_circumference_cm}
                                                    onChange={e => setChildAssessment({ ...childAssessment, head_circumference_cm: e.target.value })}
                                                    placeholder="e.g., 35"
                                                />
                                            </div>
                                        </div>
                                    </div>

                                    <div className="form-section">
                                        <h6>Vital Signs</h6>
                                        <div className="form-row">
                                            <div className="form-field">
                                                <label>Temperature (°C)</label>
                                                <input
                                                    type="number"
                                                    step="0.1"
                                                    value={childAssessment.temperature}
                                                    onChange={e => setChildAssessment({ ...childAssessment, temperature: e.target.value })}
                                                    placeholder="e.g., 36.8"
                                                />
                                            </div>
                                            <div className="form-field">
                                                <label>Heart Rate (bpm)</label>
                                                <input
                                                    type="number"
                                                    value={childAssessment.heart_rate}
                                                    onChange={e => setChildAssessment({ ...childAssessment, heart_rate: e.target.value })}
                                                    placeholder="e.g., 140"
                                                />
                                            </div>
                                            <div className="form-field">
                                                <label>Respiratory Rate</label>
                                                <input
                                                    type="number"
                                                    value={childAssessment.respiratory_rate}
                                                    onChange={e => setChildAssessment({ ...childAssessment, respiratory_rate: e.target.value })}
                                                    placeholder="breaths/min"
                                                />
                                            </div>
                                        </div>
                                    </div>

                                    <div className="form-section">
                                        <h6>Feeding Assessment</h6>
                                        <div className="form-row">
                                            <div className="form-field">
                                                <label>Feeding Type</label>
                                                <select
                                                    value={childAssessment.feeding_type}
                                                    onChange={e => setChildAssessment({ ...childAssessment, feeding_type: e.target.value })}
                                                >
                                                    <option value="exclusive_breastfeeding">Exclusive Breastfeeding</option>
                                                    <option value="mixed">Mixed Feeding</option>
                                                    <option value="formula">Formula Only</option>
                                                    <option value="complementary">Complementary Foods Started</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>Feeding Frequency</label>
                                                <input
                                                    type="text"
                                                    value={childAssessment.feeding_frequency}
                                                    onChange={e => setChildAssessment({ ...childAssessment, feeding_frequency: e.target.value })}
                                                    placeholder="e.g., 8-10 times/day"
                                                />
                                            </div>
                                        </div>
                                    </div>

                                    <div className="form-section">
                                        <h6>Physical Examination</h6>
                                        <div className="form-row">
                                            <div className="form-field">
                                                <label>Skin Color</label>
                                                <select
                                                    value={childAssessment.skin_color}
                                                    onChange={e => setChildAssessment({ ...childAssessment, skin_color: e.target.value })}
                                                >
                                                    <option value="normal">Normal/Pink</option>
                                                    <option value="pale">Pale</option>
                                                    <option value="cyanotic">Bluish (Cyanotic)</option>
                                                    <option value="jaundiced">Yellow (Jaundiced)</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>Jaundice Level</label>
                                                <select
                                                    value={childAssessment.jaundice_level}
                                                    onChange={e => setChildAssessment({ ...childAssessment, jaundice_level: e.target.value })}
                                                >
                                                    <option value="none">None</option>
                                                    <option value="mild_face">Mild (Face only)</option>
                                                    <option value="moderate">Moderate (Up to trunk)</option>
                                                    <option value="severe">Severe (Palms/Soles)</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>Umbilical Cord</label>
                                                <select
                                                    value={childAssessment.umbilical_cord}
                                                    onChange={e => setChildAssessment({ ...childAssessment, umbilical_cord: e.target.value })}
                                                >
                                                    <option value="clean_dry">Clean & Dry</option>
                                                    <option value="moist">Moist/Sticky</option>
                                                    <option value="infected">Infected/Redness</option>
                                                    <option value="separated">Separated</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>Fontanelle</label>
                                                <select
                                                    value={childAssessment.fontanelle}
                                                    onChange={e => setChildAssessment({ ...childAssessment, fontanelle: e.target.value })}
                                                >
                                                    <option value="normal">Normal</option>
                                                    <option value="bulging">Bulging</option>
                                                    <option value="sunken">Sunken</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>Eyes</label>
                                                <select
                                                    value={childAssessment.eyes}
                                                    onChange={e => setChildAssessment({ ...childAssessment, eyes: e.target.value })}
                                                >
                                                    <option value="normal">Normal</option>
                                                    <option value="discharge">Discharge</option>
                                                    <option value="swelling">Swelling</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>Reflexes</label>
                                                <select
                                                    value={childAssessment.reflexes}
                                                    onChange={e => setChildAssessment({ ...childAssessment, reflexes: e.target.value })}
                                                >
                                                    <option value="present">Present</option>
                                                    <option value="weak">Weak</option>
                                                    <option value="absent">Absent</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>Muscle Tone</label>
                                                <select
                                                    value={childAssessment.muscle_tone}
                                                    onChange={e => setChildAssessment({ ...childAssessment, muscle_tone: e.target.value })}
                                                >
                                                    <option value="normal">Normal</option>
                                                    <option value="hypotonic">Floppy (Hypotonic)</option>
                                                    <option value="hypertonic">Stiff (Hypertonic)</option>
                                                </select>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="form-section">
                                        <h6>⚠️ IMNCI Danger Signs (Check if present)</h6>
                                        <div className="checkbox-grid danger-signs">
                                            {[
                                                { key: 'not_feeding_well', label: 'Not feeding well' },
                                                { key: 'convulsions', label: 'Convulsions/Fits' },
                                                { key: 'fast_breathing', label: 'Fast breathing (>60/min)' },
                                                { key: 'chest_indrawing', label: 'Severe chest indrawing' },
                                                { key: 'high_fever', label: 'High fever (>38°C)' },
                                                { key: 'hypothermia', label: 'Hypothermia (<35.5°C)' },
                                                { key: 'jaundice_extending', label: 'Jaundice extending to palms' },
                                                { key: 'umbilical_infection', label: 'Umbilical infection/bleeding' }
                                            ].map(item => (
                                                <label key={item.key} className="checkbox-item danger">
                                                    <input
                                                        type="checkbox"
                                                        checked={childAssessment[item.key]}
                                                        onChange={e => setChildAssessment({ ...childAssessment, [item.key]: e.target.checked })}
                                                    />
                                                    <span>{item.label}</span>
                                                </label>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="form-section">
                                        <h6>Risk Assessment & Referral</h6>
                                        <div className="form-row">
                                            <div className="form-field">
                                                <label>Overall Risk Level</label>
                                                <select
                                                    value={childAssessment.overall_risk_level}
                                                    onChange={e => setChildAssessment({ ...childAssessment, overall_risk_level: e.target.value })}
                                                    className={`risk-select ${childAssessment.overall_risk_level}`}
                                                >
                                                    <option value="low">Low Risk</option>
                                                    <option value="medium">Medium Risk</option>
                                                    <option value="high">High Risk</option>
                                                    <option value="critical">Critical</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>Referral Needed?</label>
                                                <div className="toggle-switch">
                                                    <label>
                                                        <input
                                                            type="checkbox"
                                                            checked={childAssessment.referral_needed}
                                                            onChange={e => setChildAssessment({ ...childAssessment, referral_needed: e.target.checked })}
                                                        />
                                                        <span className="slider"></span>
                                                        <span className="label-text">{childAssessment.referral_needed ? 'Yes' : 'No'}</span>
                                                    </label>
                                                </div>
                                            </div>
                                        </div>
                                        {childAssessment.referral_needed && (
                                            <div className="form-row">
                                                <div className="form-field">
                                                    <label>Referral Facility</label>
                                                    <input
                                                        type="text"
                                                        value={childAssessment.referral_facility}
                                                        onChange={e => setChildAssessment({ ...childAssessment, referral_facility: e.target.value })}
                                                        placeholder="e.g. District Hospital"
                                                    />
                                                </div>
                                                <div className="form-field">
                                                    <label>Reason for Referral</label>
                                                    <input
                                                        type="text"
                                                        value={childAssessment.referral_reason}
                                                        onChange={e => setChildAssessment({ ...childAssessment, referral_reason: e.target.value })}
                                                        placeholder="Reason..."
                                                    />
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                    
                                     <div className="form-section">
                                         <h6>{userRole === 'doctor' ? 'Notes, Nutrition & Medications' : 'Remarks'}</h6>
                                        {userRole === 'doctor' ? (
                                             <>
                                                <div className="form-row">
                                                    <div className="form-field full">
                                                        <label>Clinical Notes</label>
                                                        <textarea value={childAssessment.notes} onChange={e => setChildAssessment({ ...childAssessment, notes: e.target.value })} placeholder="Enter observations..." rows={3} />
                                                    </div>
                                                </div>
                                                <div className="form-row">
                                                    <div className="form-field full">
                                                        <label>Recommendations</label>
                                                        <textarea value={childAssessment.recommendations} onChange={e => setChildAssessment({ ...childAssessment, recommendations: e.target.value })} placeholder="Enter recommendations..." rows={2} />
                                                    </div>
                                                </div>
                                                <div className="form-row">
                                                    <div className="form-field full">
                                                        <label>Nutrition Advice</label>
                                                        <textarea value={childAssessment.nutrition_advice} onChange={e => setChildAssessment({ ...childAssessment, nutrition_advice: e.target.value })} placeholder="Dietary recommendations..." rows={2} />
                                                    </div>
                                                </div>
                                                 <div className="form-row">
                                                    <div className="form-field full">
                                                        <label>Medications</label>
                                                        <textarea value={childAssessment.medications} onChange={e => setChildAssessment({ ...childAssessment, medications: e.target.value })} placeholder="Prescribed medicines..." rows={2} />
                                                    </div>
                                                </div>
                                                <div className="form-row">
                                                    <div className="form-field">
                                                        <label>Next Visit Date</label>
                                                        <input type="date" min={new Date().toISOString().split('T')[0]} value={childAssessment.next_visit_date} onChange={e => setChildAssessment({ ...childAssessment, next_visit_date: e.target.value })} />
                                                    </div>
                                                </div>
                                            </>
                                        ) : (
                                            <div className="form-row">
                                                <div className="form-field full">
                                                    <label>Remarks</label>
                                                    <textarea value={childAssessment.notes} onChange={e => setChildAssessment({ ...childAssessment, notes: e.target.value })} placeholder="Enter remarks..." rows={3} />
                                                </div>
                                            </div>
                                        )}
                                     </div>

                                    <div className="form-actions">
                                        <button className="btn-secondary" onClick={() => setShowForm(null)}>
                                            <X size={16} /> Cancel
                                        </button>
                                        <button className="btn-primary" onClick={submitChildAssessment}>
                                            <Save size={16} /> Save Health Check
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                <div className="assessment-history">
                                    <div className="flex justify-between items-center mb-4">
                                        <h5>📜 Health Check History</h5>
                                        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">Latest on top</span>
                                    </div>
                                    {assessments.length === 0 ? (
                                        <div className="text-center py-8 text-gray-400">
                                            <Baby size={32} className="mx-auto mb-2 opacity-50" />
                                            <p>No health checks recorded yet</p>
                                        </div>
                                    ) : (
                                        <div className="history-list space-y-4">
                                            {assessments.map((a, i) => renderAssessmentCard(a, 'child'))}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
"""

try:
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Part 1: Insert renderChildClinicalProfile after renderClinicalProfile
    profile_insert_idx = -1
    for i, line in enumerate(lines):
        if "const renderClinicalProfile" in line:
            # find the end of this function. It ends with ); around line 646.
            # I can search for the next blank line or function definition.
            # A simpler way: search for "Mother Assessments Tab" and insert BEFORE it.
            pass
        if "// Mother Assessments Tab" in line:
            profile_insert_idx = i
            break
            
    if profile_insert_idx != -1:
        # Check if renderChildClinicalProfile already exists (to prevent dupes if rerun)
        content_for_check = "".join(lines)
        if "renderChildClinicalProfile" not in content_for_check:
            lines.insert(profile_insert_idx, child_profile_code + "\n\n")
            print("Inserted renderChildClinicalProfile.")
        else:
            print("renderChildClinicalProfile already exists.")
    else:
        print("Could not find insertion point for renderChildClinicalProfile.")
        
    # Recalculate content
    content = "".join(lines)
    lines = content.splitlines(keepends=True) # Reset lines

    # Part 2: Replace renderChildAssessments
    start_idx = -1
    end_idx = -1
    
    for i, line in enumerate(lines):
        if "// Child Assessments Tab" in line:
            start_idx = i
        if "const subTabs = [" in line:
            end_idx = i
            # Move back to capture the closing parenthesis of the function renderChildAssessments
            # The function ends with ); just before subTabs
            # Actually, let's just replace up to subTabs
            break
            
    if start_idx != -1 and end_idx != -1:
         # Find the exact line before "const subTabs" is probably the closing ); 
         # I will just replace from marker to marker.
         final_content = "".join(lines[:start_idx]) + new_child_assessments_code + "\n\n" + "".join(lines[end_idx:])
         
         with open(file_path, "w", encoding="utf-8") as f:
            f.write(final_content)
         print("Successfully replaced renderChildAssessments.")
    else:
        print(f"Could not find start/end markers for child assessments. Start: {start_idx}, End: {end_idx}")

except Exception as e:
    print(f"Error: {e}")
