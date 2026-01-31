
import os

file_path = r"d:\SantanRaksha\frontend\src\pages\postnatal\PostnatalAssessments.jsx"

new_content_code = r"""    // Mother Assessments Tab
    const renderMotherAssessments = () => (
        <div className="mother-assessments">
            <div className="section-header">
                <h3>👩 Mother's Postnatal Health</h3>
                <p>Monitor recovery, breastfeeding, and mental health</p>
            </div>

            {/* Mother List */}
            <div className="patient-list">
                {mothers.length === 0 ? (
                    <div className="empty-state">
                        <User size={48} />
                        <p>No postnatal mothers found</p>
                        <span>Mothers will appear here after delivery completion</span>
                    </div>
                ) : (
                    <div className="patient-cards">
                        {mothers.map(mother => (
                            <div
                                key={mother.id}
                                className={`patient-card ${selectedMother?.id === mother.id ? 'selected' : ''}`}
                                onClick={() => {
                                    setSelectedMother(mother);
                                    loadAssessments(mother.id);
                                }}
                            >
                                <div className="patient-avatar">
                                    {mother.name?.charAt(0) || 'M'}
                                </div>
                                <div className="patient-info">
                                    <h4>{mother.name}</h4>
                                    <p>Age: {mother.age} · {mother.location}</p>
                                </div>
                                <div className="patient-status">
                                    {getRiskBadge('low')}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Assessment Form / Details */}
            {selectedMother && (
                <div className="assessment-panel">
                    {/* Header */}
                    <div className="bg-white border-b border-gray-200 px-8 py-6 shadow-sm mb-6 rounded-lg">
                        <div className="flex items-center justify-between">
                            <div>
                                <div className="flex items-center gap-3">
                                    <h2 className="text-2xl font-bold text-gray-900">{selectedMother.name}</h2>
                                    <span className="bg-purple-100 text-purple-700 px-3 py-1 rounded-full text-xs font-bold border border-purple-200 uppercase tracking-wide">
                                        Postnatal
                                    </span>
                                </div>
                                <p className="text-gray-600 mt-1 flex items-center gap-2 text-sm">
                                    <Clock className="w-4 h-4" /> Delivered: {selectedMother.delivery_date ? new Date(selectedMother.delivery_date).toLocaleDateString() : 'N/A'} · Location: {selectedMother.location}
                                </p>
                            </div>
                           
                            <div className="flex gap-2">
                                <button
                                    onClick={() => setSelectedMother(null)}
                                    className="px-4 py-2 rounded-lg font-semibold text-sm bg-gray-100 text-gray-700 flex items-center gap-2 hover:bg-gray-200"
                                >
                                    <X size={16} /> Close
                                </button>
                            </div>
                        </div>

                         {/* Tab buttons */}
                         <div className="flex gap-3 mt-4 flex-wrap">
                            <button
                                className={`px-4 py-2 rounded-lg font-semibold text-sm flex items-center gap-2 ${showForm !== 'mother' ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-700"}`}
                                onClick={() => setShowForm(null)}
                            >
                                <FileText className="w-4 h-4" /> Assessment History
                            </button>
                            <button
                                className={`px-4 py-2 rounded-lg font-semibold text-sm flex items-center gap-2 ${showForm === 'mother' ? "bg-green-600 text-white" : "bg-gray-100 text-gray-700"}`}
                                onClick={() => setShowForm('mother')}
                            >
                                <Plus className="w-4 h-4" /> New Assessment
                            </button>
                        </div>
                    </div>

                    <div className="flex gap-6 items-start">
                         {/* Left Panel: Clinical Profile */}
                        {renderClinicalProfile(selectedMother)}

                        {/* Right Panel: Content */}
                        <div className="flex-1 bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden flex flex-col p-4">
                             {showForm === 'mother' ? (
                                <div className="assessment-form">
                                    <h5>📝 Mother Postnatal Assessment Form</h5>
                                    {/* Form Fields Injected Here */}
                                    <div className="form-section">
                                        <h6>Physical Health</h6>
                                        <div className="form-row">
                                            <div className="form-field">
                                                <label>Temperature (°C)</label>
                                                <input type="number" step="0.1" value={motherAssessment.temperature} onChange={e => setMotherAssessment({ ...motherAssessment, temperature: e.target.value })} placeholder="e.g., 37.0" />
                                            </div>
                                            <div className="form-field">
                                                <label>BP (Systolic)</label>
                                                <input type="number" value={motherAssessment.blood_pressure_systolic} onChange={e => setMotherAssessment({ ...motherAssessment, blood_pressure_systolic: e.target.value })} placeholder="e.g., 120" />
                                            </div>
                                            <div className="form-field">
                                                <label>BP (Diastolic)</label>
                                                <input type="number" value={motherAssessment.blood_pressure_diastolic} onChange={e => setMotherAssessment({ ...motherAssessment, blood_pressure_diastolic: e.target.value })} placeholder="e.g., 80" />
                                            </div>
                                            <div className="form-field">
                                                <label>Pulse Rate</label>
                                                <input type="number" value={motherAssessment.pulse_rate} onChange={e => setMotherAssessment({ ...motherAssessment, pulse_rate: e.target.value })} placeholder="bpm" />
                                            </div>
                                        </div>
                                    </div>

                                    <div className="form-section">
                                        <h6>Postnatal Recovery</h6>
                                        <div className="form-row">
                                            <div className="form-field">
                                                <label>Uterine Involution</label>
                                                <select value={motherAssessment.uterine_involution} onChange={e => setMotherAssessment({ ...motherAssessment, uterine_involution: e.target.value })}>
                                                    <option value="normal">Normal</option>
                                                    <option value="subinvolution">Subinvolution</option>
                                                    <option value="tender">Tender</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>Lochia Status</label>
                                                <select value={motherAssessment.lochia_status} onChange={e => setMotherAssessment({ ...motherAssessment, lochia_status: e.target.value })}>
                                                    <option value="normal">Normal</option>
                                                    <option value="foul_smelling">Foul Smelling</option>
                                                    <option value="excessive">Excessive</option>
                                                    <option value="absent">Absent</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>Breast Condition</label>
                                                <select value={motherAssessment.breast_condition} onChange={e => setMotherAssessment({ ...motherAssessment, breast_condition: e.target.value })}>
                                                    <option value="normal">Normal</option>
                                                    <option value="engorged">Engorged</option>
                                                    <option value="cracked_nipples">Cracked Nipples</option>
                                                    <option value="mastitis">Mastitis Signs</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                 <label>Episiotomy Wound</label>
                                                 <select value={motherAssessment.episiotomy_wound} onChange={e => setMotherAssessment({ ...motherAssessment, episiotomy_wound: e.target.value })}>
                                                     <option value="healing_well">Healing Well</option>
                                                     <option value="infected">Infected</option>
                                                     <option value="dehisced">Dehisced (Open)</option>
                                                     <option value="not_applicable">N/A</option>
                                                 </select>
                                             </div>
                                            <div className="form-field">
                                                <label>C-Section Wound</label>
                                                <select value={motherAssessment.cesarean_wound} onChange={e => setMotherAssessment({ ...motherAssessment, cesarean_wound: e.target.value })}>
                                                    <option value="healing_well">Healing Well</option>
                                                    <option value="infected">Infected</option>
                                                    <option value="dehisced">Dehisced</option>
                                                    <option value="not_applicable">N/A</option>
                                                </select>
                                            </div>
                                             <div className="form-field">
                                                <label>Breastfeeding Established?</label>
                                                <div className="toggle-switch">
                                                    <label>
                                                        <input type="checkbox" checked={motherAssessment.breastfeeding_established} onChange={e => setMotherAssessment({ ...motherAssessment, breastfeeding_established: e.target.checked })} />
                                                        <span className="slider"></span>
                                                        <span className="label-text">{motherAssessment.breastfeeding_established ? 'Yes' : 'No'}</span>
                                                    </label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="form-section">
                                        <h6>Mental Health (PPD Screening)</h6>
                                        <div className="form-row">
                                            <div className="form-field">
                                                <label>Mood Status</label>
                                                <select value={motherAssessment.mood_status} onChange={e => setMotherAssessment({ ...motherAssessment, mood_status: e.target.value })}>
                                                    <option value="stable">Stable & Happy</option>
                                                    <option value="anxious">Anxious</option>
                                                    <option value="sad">Persistently Sad</option>
                                                    <option value="overwhelmed">Overwhelmed</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>PPD Risk</label>
                                                <select value={motherAssessment.postpartum_depression_risk} onChange={e => setMotherAssessment({ ...motherAssessment, postpartum_depression_risk: e.target.value })}>
                                                    <option value="low">Low</option>
                                                    <option value="medium">Medium</option>
                                                    <option value="high">High</option>
                                                </select>
                                            </div>
                                             <div className="form-field">
                                                <label>Sleep Quality</label>
                                                <select value={motherAssessment.sleep_quality} onChange={e => setMotherAssessment({ ...motherAssessment, sleep_quality: e.target.value })}>
                                                    <option value="adequate">Adequate</option>
                                                    <option value="poor">Poor</option>
                                                    <option value="insomnia">Insomnia</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>Bonding with Baby</label>
                                                <select value={motherAssessment.bonding_with_baby} onChange={e => setMotherAssessment({ ...motherAssessment, bonding_with_baby: e.target.value })}>
                                                    <option value="good">Good</option>
                                                    <option value="developing">Developing</option>
                                                    <option value="poor">Poor/Detached</option>
                                                </select>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="form-section">
                                        <h6>Risk Assessment & Referral</h6>
                                        <div className="form-row">
                                            <div className="form-field">
                                                <label>Overall Risk Level</label>
                                                <select value={motherAssessment.overall_risk_level} onChange={e => setMotherAssessment({ ...motherAssessment, overall_risk_level: e.target.value })} className={`risk-select ${motherAssessment.overall_risk_level}`}>
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
                                                        <input type="checkbox" checked={motherAssessment.referral_needed} onChange={e => setMotherAssessment({ ...motherAssessment, referral_needed: e.target.checked })} />
                                                        <span className="slider"></span>
                                                        <span className="label-text">{motherAssessment.referral_needed ? 'Yes' : 'No'}</span>
                                                    </label>
                                                </div>
                                            </div>
                                            {motherAssessment.referral_needed && (
                                                <div className="form-row">
                                                    <div className="form-field">
                                                        <label>Referral Facility</label>
                                                        <input type="text" value={motherAssessment.referral_facility} onChange={e => setMotherAssessment({ ...motherAssessment, referral_facility: e.target.value })} placeholder="e.g. District Hospital" />
                                                    </div>
                                                    <div className="form-field">
                                                        <label>Reason for Referral</label>
                                                        <input type="text" value={motherAssessment.referral_reason} onChange={e => setMotherAssessment({ ...motherAssessment, referral_reason: e.target.value })} placeholder="Reason..." />
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    <div className="form-section">
                                        <h6>Danger Signs (Check if present)</h6>
                                        <div className="checkbox-grid">
                                            {[
                                                { key: 'fever', label: 'High Fever (>38°C)' },
                                                { key: 'excessive_bleeding', label: 'Excessive Bleeding' },
                                                { key: 'foul_discharge', label: 'Foul-smelling Discharge' },
                                                { key: 'breast_engorgement', label: 'Breast Engorgement' },
                                                { key: 'mastitis', label: 'Signs of Mastitis' },
                                                { key: 'urinary_issues', label: 'Urinary Problems' }
                                            ].map(item => (
                                                <label key={item.key} className="checkbox-item">
                                                    <input type="checkbox" checked={motherAssessment[item.key]} onChange={e => setMotherAssessment({ ...motherAssessment, [item.key]: e.target.checked })} />
                                                    <span>{item.label}</span>
                                                </label>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="form-section">
                                        <h6>{userRole === 'doctor' ? 'Notes, Nutrition & Medications' : 'Remarks'}</h6>
                                        {userRole === 'doctor' ? (
                                            <>
                                                <div className="form-row">
                                                    <div className="form-field full">
                                                        <label>Clinical Notes</label>
                                                        <textarea value={motherAssessment.notes} onChange={e => setMotherAssessment({ ...motherAssessment, notes: e.target.value })} placeholder="Enter observations..." rows={3} />
                                                    </div>
                                                </div>
                                                <div className="form-row">
                                                    <div className="form-field full">
                                                        <label>Recommendations</label>
                                                        <textarea value={motherAssessment.recommendations} onChange={e => setMotherAssessment({ ...motherAssessment, recommendations: e.target.value })} placeholder="Enter recommendations..." rows={2} />
                                                    </div>
                                                </div>
                                                <div className="form-row">
                                                    <div className="form-field full">
                                                        <label>Nutrition Advice</label>
                                                        <textarea value={motherAssessment.nutrition_advice} onChange={e => setMotherAssessment({ ...motherAssessment, nutrition_advice: e.target.value })} placeholder="Dietary recommendations..." rows={2} />
                                                    </div>
                                                </div>
                                                <div className="form-row">
                                                    <div className="form-field full">
                                                        <label>Medications</label>
                                                        <textarea value={motherAssessment.medications} onChange={e => setMotherAssessment({ ...motherAssessment, medications: e.target.value })} placeholder="Prescribed medicines..." rows={2} />
                                                    </div>
                                                </div>
                                                <div className="form-row">
                                                    <div className="form-field">
                                                        <label>Next Visit Date</label>
                                                        <input type="date" min={new Date().toISOString().split('T')[0]} value={motherAssessment.next_visit_date} onChange={e => setMotherAssessment({ ...motherAssessment, next_visit_date: e.target.value })} />
                                                    </div>
                                                </div>
                                            </>
                                        ) : (
                                            <div className="form-row">
                                                <div className="form-field full">
                                                    <label>Remarks</label>
                                                    <textarea value={motherAssessment.notes} onChange={e => setMotherAssessment({ ...motherAssessment, notes: e.target.value })} placeholder="Enter remarks..." rows={3} />
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    <div className="form-actions">
                                        <button className="btn-secondary" onClick={() => setShowForm(null)}>
                                            <X size={16} /> Cancel
                                        </button>
                                        <button className="btn-primary" onClick={submitMotherAssessment}>
                                            <Save size={16} /> Save Assessment
                                        </button>
                                    </div>
                                </div>
                             ) : (
                                 <div className="assessment-history">
                                     <div className="flex justify-between items-center mb-4">
                                         <h5>📜 Assessment History</h5>
                                         <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">Latest on top</span>
                                     </div>
                                     {assessments.length === 0 ? (
                                         <div className="text-center py-8 text-gray-400">
                                             <ClipboardCheck size={32} className="mx-auto mb-2 opacity-50" />
                                             <p>No assessments recorded yet</p>
                                         </div>
                                     ) : (
                                         <div className="history-list space-y-4">
                                             {assessments.map((a, i) => renderAssessmentCard(a, 'mother'))}
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

    start_idx = -1
    end_idx = -1

    for i, line in enumerate(lines):
        if "// Mother Assessments Tab" in line:
            start_idx = i
        if "// Child Assessments Tab" in line:
            end_idx = i
            break
            
    if start_idx != -1 and end_idx != -1:
        # Prepend newline to separate from previous function
        final_content = "".join(lines[:start_idx]) + "\n" + new_content_code + "\n\n" + "".join(lines[end_idx:])
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(final_content)
        print("Successfully replaced content.")
    else:
        print(f"Could not find start/end markers. Start: {start_idx}, End: {end_idx}")

except Exception as e:
    print(f"Error: {e}")
