"""
Postnatal Care Models
Pydantic models for validating postnatal assessment data
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime, timedelta
from enum import Enum


# ==================== ENUMS ====================

class UterineInvolutionStatus(str, Enum):
    NORMAL = "normal"
    SUBINVOLUTION = "subinvolution"
    TENDER = "tender"


class LochiaStatus(str, Enum):
    NORMAL = "normal"
    FOUL_SMELLING = "foul_smelling"
    EXCESSIVE = "excessive"
    ABSENT = "absent"


class BreastCondition(str, Enum):
    NORMAL = "normal"
    ENGORGED = "engorged"
    CRACKED_NIPPLES = "cracked_nipples"
    MASTITIS = "mastitis"


class MoodStatus(str, Enum):
    STABLE = "stable"
    ANXIOUS = "anxious"
    SAD = "sad"
    OVERWHELMED = "overwhelmed"


class SleepQuality(str, Enum):
    ADEQUATE = "adequate"
    POOR = "poor"
    INSOMNIA = "insomnia"


class BondingQuality(str, Enum):
    GOOD = "good"
    DEVELOPING = "developing"
    POOR = "poor"


class PPDRisk(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class FeedingType(str, Enum):
    EXCLUSIVE_BREASTFEEDING = "exclusive_breastfeeding"
    MIXED = "mixed"
    FORMULA = "formula"
    COMPLEMENTARY = "complementary"


class JaundiceLevel(str, Enum):
    NONE = "none"
    MILD = "mild_face"
    MODERATE = "moderate"
    SEVERE = "severe"


class UmbilicalCordStatus(str, Enum):
    CLEAN_DRY = "clean_dry"
    MOIST = "moist"
    INFECTED = "infected"
    SEPARATED = "separated"


# ==================== MOTHER POSTNATAL ASSESSMENT ====================

class MotherPostnatalAssessmentCreate(BaseModel):
    """Model for creating a mother's postnatal assessment"""
    
    mother_id: str
    assessment_date: date = Field(default_factory=date.today)
    days_postpartum: int = Field(ge=0, le=365, description="Days since delivery")
    
    # Vital Signs
    temperature: Optional[float] = Field(None, ge=35.0, le=42.0, description="Temperature in Celsius")
    blood_pressure_systolic: Optional[int] = Field(None, ge=60, le=250)
    blood_pressure_diastolic: Optional[int] = Field(None, ge=40, le=150)
    pulse_rate: Optional[int] = Field(None, ge=40, le=180, description="Beats per minute")
    
    # Postnatal Recovery
    uterine_involution: UterineInvolutionStatus = Field(default=UterineInvolutionStatus.NORMAL)
    lochia_status: LochiaStatus = Field(default=LochiaStatus.NORMAL)
    episiotomy_wound: Optional[str] = Field(None, description="Episiotomy wound status")
    cesarean_wound: Optional[str] = Field(None, description="C-section wound status")
    breast_condition: BreastCondition = Field(default=BreastCondition.NORMAL)
    breastfeeding_established: bool = Field(default=True)
    
    # Mental Health (PPD Screening)
    mood_status: MoodStatus = Field(default=MoodStatus.STABLE)
    sleep_quality: SleepQuality = Field(default=SleepQuality.ADEQUATE)
    postpartum_depression_risk: PPDRisk = Field(default=PPDRisk.LOW)
    bonding_with_baby: BondingQuality = Field(default=BondingQuality.GOOD)
    
    # Danger Signs
    fever: bool = Field(default=False, description="Fever > 38°C")
    excessive_bleeding: bool = Field(default=False)
    foul_discharge: bool = Field(default=False)
    breast_engorgement: bool = Field(default=False)
    mastitis: bool = Field(default=False)
    urinary_issues: bool = Field(default=False)
    
    # Clinical Notes
    notes: Optional[str] = Field(None, max_length=2000)
    recommendations: Optional[str] = Field(None, max_length=1000)
    nutrition_advice: Optional[str] = Field(None, max_length=1000)
    medications: Optional[str] = Field(None, max_length=1000)
    next_visit_date: Optional[date] = None

    # Risk & Referral
    overall_risk_level: Optional[str] = Field(None, description="low, medium, high, critical")
    referral_needed: bool = Field(default=False)
    referral_reason: Optional[str] = Field(None, max_length=500)
    referral_facility: Optional[str] = Field(None, max_length=200)
    
    # Assessor Info
    assessor_id: Optional[int] = None
    assessor_role: Optional[str] = Field(None, description="doctor, asha_worker, nurse")
    
    @validator('blood_pressure_systolic')
    def validate_systolic_bp(cls, v, values):
        """Ensure systolic BP is higher than diastolic"""
        if v and values.get('blood_pressure_diastolic'):
            if v <= values['blood_pressure_diastolic']:
                raise ValueError("Systolic BP must be greater than diastolic BP")
        return v
    
    @validator('assessment_date')
    def validate_assessment_date(cls, v):
        """Ensure assessment date is not in the future"""
        if v > date.today():
            raise ValueError("Assessment date cannot be in the future")
        return v
    
    class Config:
        use_enum_values = True


class MotherPostnatalAssessmentResponse(MotherPostnatalAssessmentCreate):
    """Model for mother postnatal assessment response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== CHILD HEALTH ASSESSMENT ====================

class ChildHealthAssessmentCreate(BaseModel):
    """Model for creating a child health assessment"""
    
    child_id: str
    mother_id: str
    assessment_date: date = Field(default_factory=date.today)
    age_days: int = Field(ge=0, description="Age in days")
    
    # Growth Measurements
    weight_kg: Optional[float] = Field(None, ge=1.0, le=30.0, description="Weight in kilograms")
    length_cm: Optional[float] = Field(None, ge=30.0, le=120.0, description="Length in centimeters")
    head_circumference_cm: Optional[float] = Field(None, ge=25.0, le=60.0)
    
    # Vital Signs
    temperature: Optional[float] = Field(None, ge=35.0, le=42.0)
    heart_rate: Optional[int] = Field(None, ge=60, le=200)
    respiratory_rate: Optional[int] = Field(None, ge=20, le=80)
    
    # Feeding Assessment
    feeding_type: FeedingType = Field(default=FeedingType.EXCLUSIVE_BREASTFEEDING)
    feeding_frequency: Optional[str] = Field(None, description="e.g., every 2-3 hours")
    feeding_issues: Optional[List[str]] = Field(default_factory=list)
    
    # Physical Examination
    skin_color: str = Field(default="normal", description="normal, pale, cyanotic")
    jaundice_level: JaundiceLevel = Field(default=JaundiceLevel.NONE)
    umbilical_cord: UmbilicalCordStatus = Field(default=UmbilicalCordStatus.CLEAN_DRY)
    fontanelle: str = Field(default="normal", description="normal, bulging, sunken")
    eyes: str = Field(default="normal")
    reflexes: str = Field(default="present", description="present, absent, weak")
    muscle_tone: str = Field(default="normal")
    
    # IMNCI Danger Signs
    not_feeding_well: bool = Field(default=False)
    convulsions: bool = Field(default=False)
    fast_breathing: bool = Field(default=False)
    chest_indrawing: bool = Field(default=False)
    high_fever: bool = Field(default=False, description="Temperature > 38°C")
    hypothermia: bool = Field(default=False, description="Temperature < 35.5°C")
    jaundice_extending: bool = Field(default=False, description="Jaundice extending to palms/soles")
    umbilical_infection: bool = Field(default=False)
    
    # Clinical Notes
    notes: Optional[str] = Field(None, max_length=2000)
    recommendations: Optional[str] = Field(None, max_length=1000)
    nutrition_advice: Optional[str] = Field(None, max_length=1000)
    medications: Optional[str] = Field(None, max_length=1000)
    next_visit_date: Optional[date] = None

    # Risk & Referral
    overall_risk_level: Optional[str] = Field(None, description="low, medium, high, critical")
    referral_needed: bool = Field(default=False)
    referral_reason: Optional[str] = Field(None, max_length=500)
    referral_facility: Optional[str] = Field(None, max_length=200)
    
    # Assessor Info
    assessor_id: Optional[int] = None
    assessor_role: Optional[str] = None
    
    @validator('assessment_date')
    def validate_assessment_date(cls, v):
        """Ensure assessment date is not in the future"""
        if v > date.today():
            raise ValueError("Assessment date cannot be in the future")
        return v
    
    @validator('weight_kg', 'length_cm', 'head_circumference_cm')
    def validate_positive_measurements(cls, v):
        """Ensure measurements are positive"""
        if v is not None and v <= 0:
            raise ValueError("Measurement must be positive")
        return v
    
    class Config:
        use_enum_values = True


class ChildHealthAssessmentResponse(ChildHealthAssessmentCreate):
    """Model for child health assessment response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== CHILD REGISTRATION ====================

class ChildCreate(BaseModel):
    """Model for registering a new child"""
    name: str = Field(..., min_length=2, max_length=100)
    mother_id: str
    birth_date: date
    gender: str = Field(..., description="male, female, other")
    birth_weight_kg: Optional[float] = Field(None, ge=0.5, le=10.0)
    asha_worker_id: Optional[int] = None
    doctor_id: Optional[int] = None
    
    @validator('birth_date')
    def validate_birth_date(cls, v):
        if v > date.today():
            raise ValueError("Birth date cannot be in the future")
        return v


class ChildResponse(ChildCreate):
    """Response model for child registration"""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== QUERY MODELS ====================

class PostnatalMothersQuery(BaseModel):
    """Query parameters for fetching postnatal mothers"""
    asha_worker_id: Optional[int] = None
    doctor_id: Optional[int] = None
    status: str = Field(default="postnatal")
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class PostnatalChildrenQuery(BaseModel):
    """Query parameters for fetching children"""
    mother_id: Optional[str] = None
    asha_worker_id: Optional[int] = None
    doctor_id: Optional[int] = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


# ==================== RESPONSE MODELS ====================

class PostnatalMothersResponse(BaseModel):
    """Response model for postnatal mothers list"""
    success: bool = True
    mothers: List[dict]
    total: int
    has_more: bool
    cached: bool = False


class PostnatalChildrenResponse(BaseModel):
    """Response model for children list"""
    success: bool = True
    children: List[dict]
    total: int
    has_more: bool
    cached: bool = False


class AssessmentHistoryResponse(BaseModel):
    """Response model for assessment history"""
    success: bool = True
    assessments: List[dict]
    total: int
    mother_info: Optional[dict] = None
    child_info: Optional[dict] = None
    cached: bool = False


# ==================== VACCINATION MODELS ====================

class VaccinationStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    MISSED = "missed"
    OVERDUE = "overdue"
    CONTRAINDICATED = "contraindicated"


class VaccinationCreate(BaseModel):
    """Model for creating/updating a vaccination record"""
    
    child_id: str
    vaccine_name: str = Field(..., min_length=2, max_length=100)
    dose_number: int = Field(ge=1, le=10, description="Dose number (1, 2, 3...)")
    scheduled_date: date
    status: VaccinationStatus = Field(default=VaccinationStatus.SCHEDULED)
    
    # If administered
    administered_date: Optional[date] = None
    administered_by: Optional[str] = Field(None, max_length=100)
    batch_number: Optional[str] = Field(None, max_length=50)
    site: Optional[str] = Field(None, description="Injection site")
    
    # Reaction tracking
    adverse_reaction: bool = Field(default=False)
    reaction_details: Optional[str] = Field(None, max_length=500)
    
    # Notes
    notes: Optional[str] = Field(None, max_length=1000)
    next_dose_date: Optional[date] = None
    
    @validator('administered_date')
    def validate_administered_date(cls, v, values):
        if v and values.get('scheduled_date'):
            if v < values['scheduled_date'] - timedelta(days=7):
                raise ValueError("Administered date cannot be more than 7 days before scheduled date")
        return v
    
    class Config:
        use_enum_values = True


class VaccinationResponse(VaccinationCreate):
    """Response model for vaccination"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class VaccinationSchedule(BaseModel):
    """Standard vaccination schedule"""
    vaccine_name: str
    dose_number: int
    recommended_age_weeks: int = Field(description="Age in weeks when vaccine is recommended")
    description: Optional[str] = None


# ==================== MILESTONE MODELS ====================

class MilestoneCategory(str, Enum):
    MOTOR_GROSS = "motor_gross"
    MOTOR_FINE = "motor_fine"
    COGNITIVE = "cognitive"
    LANGUAGE = "language"
    SOCIAL = "social"


class MilestoneStatus(str, Enum):
    NOT_ASSESSED = "not_assessed"
    ACHIEVED = "achieved"
    EMERGING = "emerging"
    NOT_ACHIEVED = "not_achieved"
    CONCERN = "concern"


class DevelopmentalMilestoneCreate(BaseModel):
    """Model for tracking developmental milestones"""
    
    child_id: str
    assessment_date: date = Field(default_factory=date.today)
    age_months: int = Field(ge=0, le=72, description="Age in months")
    
    # Milestone details
    milestone_name: str = Field(..., min_length=2, max_length=200)
    category: MilestoneCategory
    expected_age_months: int = Field(ge=0, le=72)
    status: MilestoneStatus = Field(default=MilestoneStatus.NOT_ASSESSED)
    
    # Assessment details
    achieved_date: Optional[date] = None
    assessor_notes: Optional[str] = Field(None, max_length=1000)
    concerns: Optional[str] = Field(None, max_length=500)
    follow_up_needed: bool = Field(default=False)
    referral_made: bool = Field(default=False)
    
    # Assessor info
    assessor_id: Optional[int] = None
    assessor_role: Optional[str] = None
    
    class Config:
        use_enum_values = True


class DevelopmentalMilestoneResponse(DevelopmentalMilestoneCreate):
    """Response model for developmental milestone"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MilestoneChecklistItem(BaseModel):
    """Individual milestone checklist item"""
    name: str
    category: MilestoneCategory
    expected_age_months: int
    description: str
    red_flags: Optional[str] = None


# ==================== VACCINATION RESPONSE MODELS ====================

class VaccinationListResponse(BaseModel):
    """Response for vaccination list"""
    success: bool = True
    vaccinations: List[dict]
    total: int
    completed: int
    pending: int
    overdue: int
    cached: bool = False


class MilestoneListResponse(BaseModel):
    """Response for milestone list"""
    success: bool = True
    milestones: List[dict]
    total: int
    achieved: int
    concerns: int
    cached: bool = False


# ==================== GROWTH MODELS ====================

class GrowthRecordCreate(BaseModel):
    """Model for creating a growth record"""
    child_id: str
    measurement_date: date = Field(default_factory=date.today)
    
    # Measurements
    weight_kg: float = Field(..., ge=0.5, le=50.0)
    height_cm: Optional[float] = Field(None, ge=30.0, le=150.0)
    head_circumference_cm: Optional[float] = Field(None, ge=25.0, le=60.0)
    muac_cm: Optional[float] = Field(None, description="Mid-Upper Arm Circumference")
    
    # Calculated Z-scores (optional input, usually calculated by backend)
    weight_for_age_z: Optional[float] = None
    height_for_age_z: Optional[float] = None
    weight_for_height_z: Optional[float] = None
    bmi_for_age_z: Optional[float] = None
    
    notes: Optional[str] = Field(None, max_length=1000)
    measured_by: Optional[str] = None
    
    @validator('measurement_date')
    def validate_date(cls, v):
        if v > date.today():
             raise ValueError("Measurement date cannot be in the future")
        return v


class GrowthRecordResponse(GrowthRecordCreate):
    """Response model for growth record"""
    id: int
    created_at: datetime
    age_months: Optional[int] = None
    
    class Config:
        from_attributes = True


class GrowthHistoryResponse(BaseModel):
    """Response model for growth history"""
    success: bool = True
    records: List[dict]
    total: int
    child_info: Optional[dict] = None
    cached: bool = False
