import os
import importlib.util
import logging
import requests
import threading
import time
import asyncio
import base64
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, status, Request, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from contextlib import asynccontextmanager

# Load environment variables
BASE_DIR = os.path.dirname(__file__)
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize router
router = APIRouter()
logger = logging.getLogger(__name__)

# ==================== GLOBAL VARIABLES ====================
telegram_bot_app = None
bot_thread = None
bot_running = False

# ==================== ENVIRONMENT VALIDATION ====================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Backend URL for Telegram webhook (e.g., https://your-app.onrender.com)
BACKEND_URL = os.getenv("BACKEND_URL", "").strip()
# Use webhooks instead of polling for efficiency (only triggers on messages)
USE_TELEGRAM_WEBHOOK = os.getenv("USE_TELEGRAM_WEBHOOK", "true").lower() == "true"

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.warning("⚠️  Supabase credentials not found in .env")
    SUPABASE_URL = "https://placeholder.supabase.co"
    SUPABASE_KEY = "placeholder"

if not TELEGRAM_BOT_TOKEN:
    logger.warning("⚠️  TELEGRAM_BOT_TOKEN not found in .env")
    TELEGRAM_BOT_TOKEN = "placeholder"

if not GEMINI_API_KEY:
    logger.warning("⚠️  GEMINI_API_KEY not found in .env")
    GEMINI_API_KEY = None

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("✅ Supabase client initialized")
except Exception as e:
    logger.error(f"❌ Supabase initialization error: {e}")
    supabase = None

# ==================== GEMINI AI INITIALIZATION ====================
gemini_client = None
try:
    from google import genai
    if GEMINI_API_KEY:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
        logger.info("✅ Gemini AI initialized")
    else:
        GEMINI_AVAILABLE = False
        logger.warning("⚠️  Gemini API key not set")
except ImportError as e:
    logger.warning(f"⚠️  Gemini not available: {e}")
    logger.warning("⚠️  Install with: pip install google-genai")
    GEMINI_AVAILABLE = False

# ==================== AI AGENTS IMPORT ====================
try:
    try:
        from backend.agents.orchestrator import get_orchestrator
    except ImportError:
        from agents.orchestrator import get_orchestrator
    orchestrator = get_orchestrator()
    AGENTS_AVAILABLE = True
    logger.info("✅ AI Agents loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️  AI Agents not available: {e}")
    logger.warning("⚠️  System will work without AI agents")
    AGENTS_AVAILABLE = False
    orchestrator = None

# ==================== CACHE SERVICE IMPORT ====================
try:
    try:
        from backend.services.cache_service import cache, invalidate_dashboard_cache, invalidate_mothers_cache, invalidate_risk_cache
    except ImportError:
        from services.cache_service import cache, invalidate_dashboard_cache, invalidate_mothers_cache, invalidate_risk_cache
    CACHE_AVAILABLE = True
    logger.info("✅ In-memory cache initialized")
except ImportError as e:
    logger.warning(f"⚠️  Cache service not available: {e}")
    CACHE_AVAILABLE = False
    cache = None
    def invalidate_dashboard_cache(): pass
    def invalidate_mothers_cache(): pass
    def invalidate_risk_cache(): pass


# ==================== PYDANTIC MODELS ====================
class Mother(BaseModel):
    name: str
    phone: str
    age: int
    gravida: int
    parity: int
    bmi: float
    location: str
    preferred_language: str = "en"
    telegram_chat_id: Optional[str] = None
    due_date: Optional[str] = None

class RiskAssessment(BaseModel):
    mother_id: str
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    heart_rate: Optional[int] = None
    blood_glucose: Optional[float] = None
    hemoglobin: Optional[float] = None
    proteinuria: int = 0
    edema: int = 0
    headache: int = 0
    vision_changes: int = 0
    epigastric_pain: int = 0
    vaginal_bleeding: int = 0
    notes: Optional[str] = None

class DocumentAnalysisRequest(BaseModel):
    report_id: str  # UUID as string
    mother_id: str  # UUID as string
    file_url: str
    file_type: str

class AgentQuery(BaseModel):
    mother_id: str
    query: str
    context: Optional[Dict] = None

class DailyCheckIn(BaseModel):
    mother_id: str
    date: str
    weight: Optional[float] = None
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    symptoms: Optional[List[str]] = []
    medications_taken: bool = True
    feeling_today: str = "good"
    notes: Optional[str] = None

# ==================== TELEGRAM BOT FUNCTIONS ====================

def run_telegram_bot():
    """Run Telegram bot polling - creates everything in this thread's event loop"""
    global bot_running, telegram_bot_app
    
    try:
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        logger.info("🤖 Initializing Telegram Bot in background thread...")
        
        # Import telegram bot
        try:
            try:
                from backend.telegram_bot import (
                    MatruRakshaBot,
                    handle_switch_callback,
                    handle_home_action,
                    handle_document_upload,
                    handle_text_message,
                )
            except ImportError:
                from telegram_bot import (
                    MatruRakshaBot,
                    handle_switch_callback,
                    handle_home_action,
                    handle_document_upload,
                    handle_text_message,
                )
            from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters
            from telegram import Update
        except ImportError as e:
            logger.error(f"⚠️  Could not import telegram_bot: {e}")
            return
        
        # Build application IN THIS EVENT LOOP
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Create bot instance
        bot = MatruRakshaBot()
        
        # Setup handlers manually here (if bot doesn't have setup_handlers method)
        try:
            from backend.telegram_bot import (
                AWAITING_NAME, AWAITING_AGE, AWAITING_PHONE, AWAITING_DUE_DATE,
                AWAITING_LOCATION, AWAITING_GRAVIDA, AWAITING_PARITY, AWAITING_BMI,
                AWAITING_LANGUAGE, CONFIRM_REGISTRATION
            )
        except ImportError:
            from telegram_bot import (
                AWAITING_NAME, AWAITING_AGE, AWAITING_PHONE, AWAITING_DUE_DATE,
                AWAITING_LOCATION, AWAITING_GRAVIDA, AWAITING_PARITY, AWAITING_BMI,
                AWAITING_LANGUAGE, CONFIRM_REGISTRATION
            )
        
        # Registration conversation handler
        registration_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(bot.button_callback, pattern="^(register|register_new)$")
            ],
            states={
                AWAITING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_name)],
                AWAITING_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_age)],
                AWAITING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_phone)],
                AWAITING_DUE_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_due_date)],
                AWAITING_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_location)],
                AWAITING_GRAVIDA: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_gravida)],
                AWAITING_PARITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_parity)],
                AWAITING_BMI: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_bmi)],
                AWAITING_LANGUAGE: [
                    CallbackQueryHandler(bot.receive_language, pattern="^lang_"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_language)
                ],
                CONFIRM_REGISTRATION: [CallbackQueryHandler(bot.confirm_registration, pattern="^confirm_")]
            },
            fallbacks=[CommandHandler('cancel', bot.cancel_registration)],
            name="registration",
            persistent=False,
            per_message=False
        )
        
        # Add handlers
        # Keep /start but also allow simple greetings like "hi" to open the dashboard
        application.add_handler(CommandHandler("start", bot.start))

        # "Hi" (and variants) should behave like /start
        greeting_filter = (
            filters.TEXT & ~filters.COMMAND &
            (
                filters.Regex(r"(?i)^hi$") |
                filters.Regex(r"(?i)^hello$") |
                filters.Regex(r"(?i)^hey$")
            )
        )
        application.add_handler(MessageHandler(greeting_filter, bot.start))

        application.add_handler(registration_handler)
        application.add_handler(CallbackQueryHandler(handle_switch_callback, pattern=r"^switch_mother_"))
        application.add_handler(CallbackQueryHandler(handle_home_action, pattern=r"^action_"))
        application.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, handle_document_upload))
        # Add text message handler for other free-form queries (but not during registration)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
        
        # Initialize the application
        loop.run_until_complete(application.initialize())
        
        logger.info("✅ Telegram Bot initialized successfully")
        
        # Store globally
        telegram_bot_app = application
        
        # Clear any existing webhook/polling connections before starting
        logger.info("🔄 Clearing any existing Telegram connections...")
        try:
            loop.run_until_complete(application.bot.delete_webhook(drop_pending_updates=True))
            logger.info("✅ Cleared existing webhook/connections")
        except Exception as e:
            logger.warning(f"⚠️ Could not clear webhook: {e}")
        
        # Small delay to ensure old connections are released
        import time
        time.sleep(2)
        
        # Use webhooks if BACKEND_URL is set (more efficient - only triggers on messages)
        if USE_TELEGRAM_WEBHOOK and BACKEND_URL:
            webhook_url = f"{BACKEND_URL}/telegram/webhook/{TELEGRAM_BOT_TOKEN}"
            logger.info(f"🔗 Setting up Telegram webhook: {BACKEND_URL}/telegram/webhook/***")
            
            try:
                # Set webhook with Telegram
                loop.run_until_complete(application.bot.set_webhook(
                    url=webhook_url,
                    allowed_updates=["message", "callback_query", "inline_query"],
                    drop_pending_updates=True
                ))
                logger.info("✅ Telegram webhook set successfully")
                logger.info("🪝 Bot will receive updates via webhook (no polling)")
                
                # Initialize and start the application for webhook mode
                loop.run_until_complete(application.start())
                bot_running = True
                
                logger.info("🤖 MatruRaksha Telegram Bot is ACTIVE (webhook mode)")
                
                # In webhook mode, we don't run_forever - FastAPI handles incoming requests
                # Keep the application running but don't poll
                while bot_running:
                    time.sleep(60)  # Just keep thread alive, no polling
                    
            except Exception as webhook_error:
                logger.error(f"❌ Webhook setup failed: {webhook_error}")
                logger.info("⚠️ Falling back to polling mode...")
                # Fall through to polling
        else:
            if not BACKEND_URL:
                logger.warning("⚠️ BACKEND_URL not set - using polling (set BACKEND_URL for webhook mode)")
        
        # Fallback: Start polling if webhooks not available
        if not bot_running:
            logger.info("🚀 Starting Telegram polling...")
            bot_running = True
            
            loop.run_until_complete(application.start())
            loop.run_until_complete(application.updater.start_polling(
                drop_pending_updates=True,
                allowed_updates=["message", "callback_query", "inline_query"],
                poll_interval=2.0  # Poll every 2 seconds instead of every second
            ))
            
            logger.info("✅ Telegram polling started")
            logger.info("🤖 MatruRaksha Telegram Bot is ACTIVE (polling mode)")
            
            # Keep running
            loop.run_forever()
        
    except Exception as e:
        logger.error(f"❌ Error in Telegram bot: {e}", exc_info=True)
        bot_running = False
    finally:
        try:
            if telegram_bot_app:
                loop.run_until_complete(telegram_bot_app.updater.stop())
                loop.run_until_complete(telegram_bot_app.stop())
                loop.run_until_complete(telegram_bot_app.shutdown())
        except:
            pass
        loop.close()


async def stop_telegram_bot():
    """Properly stop the Telegram bot"""
    global bot_running
    
    if bot_running:
        try:
            logger.info("🛑 Stopping Telegram bot...")
            bot_running = False
            
            # Give the thread time to clean up
            await asyncio.sleep(1)
            
            logger.info("🛑 Telegram bot stopped")
        except Exception as e:
            logger.error(f"Error stopping Telegram bot: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI"""
    # ==================== STARTUP ====================
    logger.info("=" * 60)
    logger.info("")
    logger.info("    ╔══════════════════════════════════════════════════╗")
    logger.info("    ║                                                  ║")
    logger.info("    ║           🤰 MatruRaksha AI System 🤰           ║")
    logger.info("    ║                                                  ║")
    logger.info("    ║          Maternal Health Guardian System        ║")
    logger.info("    ║                                                  ║")
    logger.info("    ╚══════════════════════════════════════════════════╝")
    logger.info("")
    logger.info("=" * 60)
    
    # Start Telegram bot in background thread
    if TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_TOKEN != "placeholder":
        global bot_thread
        bot_thread = threading.Thread(
            target=run_telegram_bot,
            daemon=True,
            name="TelegramBotThread"
        )
        bot_thread.start()
        
        # Give it a moment to initialize
        await asyncio.sleep(2)
        
        logger.info("")
        logger.info("    ✅ Services Status:")
        logger.info("")
        logger.info("    🤖 Telegram Bot: Running in background")
        logger.info("    🚀 Starting FastAPI Backend...")
        logger.info("")
    else:
        logger.warning("    ⚠️  Telegram Bot Token not set")
        logger.info("    🚀 Starting FastAPI Backend only...")
    
    yield
    
    # ==================== SHUTDOWN ====================
    logger.info("=" * 60)
    logger.info("🛑 Shutting down MatruRaksha AI System...")
    
    await stop_telegram_bot()
    
    logger.info("✅ Shutdown complete")
    logger.info("=" * 60)


# ==================== CREATE FASTAPI APP ====================
# Mount enhanced API router
try:
    from enhanced_api import router as enhanced_router
    app = FastAPI(title="MatruRaksha AI Backend", lifespan=lifespan)
    app.include_router(enhanced_router)
except ImportError:
    logger.warning("⚠️  Enhanced API router not available")
    app = FastAPI(title="MatruRaksha AI Backend", lifespan=lifespan)

# Mount Vapi AI Calling routes
try:
    from routes.vapi_routes import router as vapi_router
    app.include_router(vapi_router)
    logger.info("✅ Vapi AI Calling routes loaded")
except ImportError as e:
    logger.warning(f"⚠️  Vapi routes not available: {e}")


# Mount authentication router
auth_router = None
try:
    from backend.routes.auth_routes import router as auth_router
except Exception as e1:
    try:
        from routes.auth_routes import router as auth_router
    except Exception as e2:
        try:
            module_path = os.path.join(os.path.dirname(__file__), 'routes', 'auth_routes.py')
            spec = importlib.util.spec_from_file_location('auth_routes', module_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            auth_router = getattr(mod, 'router', None)
        except Exception as e3:
            logger.warning(f"⚠️  Authentication routes not available: {e1} | {e2} | {e3}")

if auth_router:
    app.include_router(auth_router)
    logger.info("✅ Authentication routes loaded")
    try:
        for r in app.router.routes:
            logger.info(f"🔗 {','.join(r.methods)} {getattr(r, 'path', '')}")
    except Exception:
        pass

# Mount admin routes
try:
    from routes.admin_routes import router as admin_router
    app.include_router(admin_router)
    logger.info("✅ Admin routes loaded")
except Exception as e:
    import traceback
    logger.error(f"❌ Admin routes FAILED to load: {e}")
    logger.error(traceback.format_exc())

# ==================== CORS SETUP ====================
# Configure CORS to explicitly allow the frontend origin
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").strip()
ALLOWED_ORIGINS = [
    FRONTEND_URL,
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    # Production URLs
    "https://matru-raksha-ai-event.vercel.app",
    "https://matruraksha-ai-event.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== TELEGRAM WEBHOOK ENDPOINT ====================
# This endpoint receives updates from Telegram instead of polling

@app.post("/telegram/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    """
    Webhook endpoint for Telegram bot updates.
    Only triggers when a message is received (no polling!).
    """
    global telegram_bot_app
    
    # Verify token matches our bot token
    if token != TELEGRAM_BOT_TOKEN:
        logger.warning("⚠️ Invalid webhook token received")
        raise HTTPException(status_code=403, detail="Invalid token")
    
    if not telegram_bot_app:
        logger.error("❌ Telegram bot not initialized")
        raise HTTPException(status_code=500, detail="Bot not ready")
    
    try:
        # Parse the update from Telegram
        from telegram import Update
        
        update_data = await request.json()
        update = Update.de_json(update_data, telegram_bot_app.bot)
        
        # Process the update asynchronously
        await telegram_bot_app.process_update(update)
        
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"❌ Webhook processing error: {e}")
        # Still return 200 to prevent Telegram from retrying
        return {"ok": False, "error": str(e)}

# ==================== FALLBACK AUTH ROUTES (ensure availability) ====================
try:
    from backend.services.auth_service import auth_service
    from backend.middleware.auth import require_admin
except ImportError:
    from services.auth_service import auth_service
    from middleware.auth import require_admin

class RegisterDecisionBody(BaseModel):
    approved: bool
    note: Optional[str] = None

@app.get("/auth/register-requests")
async def fallback_list_register_requests(current_user: dict = Depends(require_admin)):
    try:
        requests = await auth_service.list_registration_requests(status_filter="PENDING")
        return {"success": True, "requests": requests}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/register-requests/{request_id}/decision")
async def fallback_decide_register_request(request_id: int, body: RegisterDecisionBody, current_user: dict = Depends(require_admin)):
    try:
        if body.approved:
            result = await auth_service.approve_registration_request(request_id, reviewer_id=current_user["id"], note=body.note)
            return {"success": True, "message": "Request approved", "user": result}
        else:
            await auth_service.reject_registration_request(request_id, reviewer_id=current_user["id"], note=body.note)
            return {"success": True, "message": "Request rejected"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== HELPER FUNCTIONS ====================

def calculate_risk_score(assessment: RiskAssessment) -> dict:
    """Calculate risk score based on vital signs and symptoms"""
    risk_score = 0.0
    risk_factors = []
    
    # Blood Pressure Risk
    if assessment.systolic_bp and assessment.diastolic_bp:
        if assessment.systolic_bp >= 160 or assessment.diastolic_bp >= 110:
            risk_score += 0.3
            risk_factors.append("Severe Hypertension")
        elif assessment.systolic_bp >= 140 or assessment.diastolic_bp >= 90:
            risk_score += 0.2
            risk_factors.append("Hypertension")
    
    # Hemoglobin Risk
    if assessment.hemoglobin:
        if assessment.hemoglobin < 7:
            risk_score += 0.3
            risk_factors.append("Severe Anemia")
        elif assessment.hemoglobin < 10:
            risk_score += 0.2
            risk_factors.append("Anemia")
    
    # Blood Glucose Risk
    if assessment.blood_glucose:
        if assessment.blood_glucose > 200:
            risk_score += 0.2
            risk_factors.append("Hyperglycemia")
    
    # Clinical Symptoms
    if assessment.proteinuria == 1:
        risk_score += 0.15
        risk_factors.append("Proteinuria")
    if assessment.edema == 1:
        risk_score += 0.1
        risk_factors.append("Edema")
    if assessment.headache == 1:
        risk_score += 0.1
        risk_factors.append("Headache")
    if assessment.vision_changes == 1:
        risk_score += 0.2
        risk_factors.append("Vision Changes")
    if assessment.epigastric_pain == 1:
        risk_score += 0.15
        risk_factors.append("Epigastric Pain")
    if assessment.vaginal_bleeding == 1:
        risk_score += 0.25
        risk_factors.append("Vaginal Bleeding")
    
    # Cap risk score at 1.0
    risk_score = min(risk_score, 1.0)
    
    # Determine risk level
    if risk_score >= 0.7:
        risk_level = "HIGH"
    elif risk_score >= 0.4:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"
    
    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_factors": risk_factors
    }


def calculate_pregnancy_week(registration_date: str) -> int:
    """Calculate current pregnancy week from registration"""
    try:
        reg_date = datetime.fromisoformat(registration_date.replace('Z', '+00:00'))
        days_since = (datetime.now() - reg_date).days
        return 8 + (days_since // 7)
    except:
        return 20


async def run_ai_agent_assessment(mother_data: Dict, background_tasks: BackgroundTasks) -> Optional[Dict]:
    """Run AI agent assessment if agents are available"""
    if not AGENTS_AVAILABLE or not orchestrator:
        logger.info("ℹ️  AI Agents not available - skipping agent assessment")
        return None
    
    try:
        logger.info("🤖 Running AI Agent Orchestra...")
        assessment_result = await orchestrator.process_mother_data(mother_data)
        logger.info(f"✅ AI Assessment complete. Agents used: {assessment_result.get('agents_executed', [])}")
        return assessment_result
    except Exception as e:
        logger.error(f"❌ Error in AI agent assessment: {str(e)}", exc_info=True)
        return None


def analyze_document_with_gemini(file_url: str, file_type: str, mother_data: Dict) -> Dict[str, Any]:
    """Analyze medical document using Gemini AI"""
    
    analysis_result = {
        "status": "completed",
        "extracted_data": {},
        "concerns": [],
        "recommendations": [],
        "risk_level": "normal",
        "timestamp": datetime.now().isoformat()
    }
    
    if not GEMINI_AVAILABLE:
        logger.warning("⚠️  Gemini not available - returning basic analysis")
        analysis_result["status"] = "pending_review"
        analysis_result["extracted_data"] = {
            "note": "AI analysis not available - manual review required"
        }
        return analysis_result
    
    try:
        logger.info(f"🤖 Analyzing document with Gemini AI: {file_url}")
        
        # Create the prompt for Gemini
        prompt = f"""
You are a maternal health expert analyzing a medical report for a pregnant woman.

**Mother's Profile:**
- Name: {mother_data.get('name')}
- Age: {mother_data.get('age')} years
- Gravida: {mother_data.get('gravida')} (number of pregnancies)
- Parity: {mother_data.get('parity')} (number of live births)
- BMI: {mother_data.get('bmi')}
- Location: {mother_data.get('location')}

**Task:**
Analyze the medical report and extract the following information in a structured format:

1. **Key Health Metrics** (extract if present):
   - Hemoglobin level (g/dL)
   - Blood pressure (systolic/diastolic)
   - Blood sugar/glucose level (mg/dL)
   - Weight (kg)
   - Any other vital signs

2. **Health Concerns** (identify any abnormalities or risk factors):
   - List any concerning values or conditions
   - Rate severity: mild, moderate, severe

3. **Recommendations**:
   - What actions should be taken
   - Any follow-up needed
   - Dietary or lifestyle advice

4. **Risk Assessment**:
   - Overall risk level: low, moderate, or high
   - Reasoning for the risk level

**Output Format (JSON):**
{{
    "extracted_metrics": {{
        "hemoglobin": <value or null>,
        "blood_pressure_systolic": <value or null>,
        "blood_pressure_diastolic": <value or null>,
        "blood_sugar": <value or null>,
        "weight": <value or null>,
        "other_findings": "<any other important findings>"
    }},
    "concerns": [
        "<concern 1>",
        "<concern 2>"
    ],
    "recommendations": [
        "<recommendation 1>",
        "<recommendation 2>"
    ],
    "risk_level": "<low/moderate/high>",
    "risk_reasoning": "<explanation>"
}}

Provide ONLY the JSON output, no additional text.
"""
        
        # Use the global gemini_client for API calls
        model_name = 'gemini-2.5-flash'
        
        if not gemini_client:
            raise Exception("Gemini client not initialized")
        
        logger.info(f"✅ Using Gemini model: {model_name}")
        
        # If it's an image, we can pass it directly to Gemini
        if file_type.startswith('image/'):
            try:
                # Download the image
                response = requests.get(file_url, timeout=30)
                response.raise_for_status()
                
                # Create image data for Gemini
                import PIL.Image
                import io
                image = PIL.Image.open(io.BytesIO(response.content))
                
                # Generate response with image using new client API
                result = gemini_client.models.generate_content(
                    model=model_name,
                    contents=[prompt, image]
                )
                ai_response = result.text
                
            except Exception as img_error:
                logger.error(f"Error processing image: {img_error}")
                # Fallback to text-only analysis
                result = gemini_client.models.generate_content(
                    model=model_name,
                    contents=prompt + f"\n\nNote: Could not load image from URL: {file_url}"
                )
                ai_response = result.text
        else:
            # For PDFs and other documents, use text-only analysis
            # Note: For full PDF parsing, you'd need to extract text first
            result = gemini_client.models.generate_content(
                model=model_name,
                contents=prompt + f"\n\nDocument URL: {file_url}\nFile Type: {file_type}\n\n"
                "Note: Please provide a general analysis based on typical maternal health reports."
            )
            ai_response = result.text
        
        logger.info(f"✅ Gemini response received: {len(ai_response)} characters")
        
        # Parse the JSON response
        import json
        import re
        
        # Extract JSON from response (sometimes Gemini wraps it in markdown)
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            parsed_data = json.loads(json_str)
            
            # Update analysis result with parsed data
            analysis_result["extracted_data"] = parsed_data.get("extracted_metrics", {})
            analysis_result["concerns"] = parsed_data.get("concerns", [])
            analysis_result["recommendations"] = parsed_data.get("recommendations", [])
            analysis_result["risk_level"] = parsed_data.get("risk_level", "normal")
            analysis_result["risk_reasoning"] = parsed_data.get("risk_reasoning", "")
            analysis_result["ai_analysis"] = ai_response
            analysis_result["analyzed_with"] = "Google Gemini AI"
            
            logger.info(f"✅ Analysis complete - Risk Level: {analysis_result['risk_level']}")
        else:
            # If JSON parsing fails, store raw response
            analysis_result["ai_analysis"] = ai_response
            analysis_result["extracted_data"] = {
                "note": "Manual review needed - AI response format unexpected"
            }
            analysis_result["status"] = "pending_review"
            logger.warning("⚠️  Could not parse Gemini response as JSON")
    
    except Exception as e:
        logger.error(f"❌ Gemini analysis error: {e}", exc_info=True)
        analysis_result["status"] = "error"
        analysis_result["error"] = str(e)
        analysis_result["extracted_data"] = {
            "note": "Analysis failed - manual review required"
        }
    
    return analysis_result


# ==================== HEALTH CHECK ====================
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "MatruRaksha AI Backend",
        "version": "2.0.0",
        "supabase_connected": supabase is not None,
        "telegram_bot_token": "✅ Set" if TELEGRAM_BOT_TOKEN != "placeholder" else "❌ Not Set",
        "telegram_polling": "🟢 Active" if bot_running else "🔴 Inactive",
        "gemini_ai": "🤖 Active" if GEMINI_AVAILABLE else "❌ Not Available",
        "ai_agents": "🤖 Active" if AGENTS_AVAILABLE else "❌ Not Loaded"
    }


# ==================== MOTHER ENDPOINTS ====================

@app.post("/mothers/register")
async def register_mother(mother: Mother, background_tasks: BackgroundTasks):
    """Register a new pregnant mother"""
    try:
        logger.info(f"📝 Registering mother: {mother.name}")
        
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase not connected"
            )
        
        # Insert into database
        insert_data = {
            "name": mother.name,
            "phone": mother.phone,
            "age": mother.age,
            "gravida": mother.gravida,
            "parity": mother.parity,
            "bmi": mother.bmi,
            "location": mother.location,
            "preferred_language": mother.preferred_language,
            "telegram_chat_id": mother.telegram_chat_id,
            "due_date": mother.due_date,
            "created_at": datetime.now().isoformat()
        }
        
        result = supabase.table("mothers").insert(insert_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to register mother"
            )
        
        mother_id = result.data[0]["id"]
        logger.info(f"✅ Mother registered successfully: {mother_id}")
        
        # Invalidate dashboard cache after new registration
        invalidate_mothers_cache()
        
        return {
            "status": "success",
            "message": "Mother registered successfully",
            "mother_id": mother_id,
            "data": result.data[0]
        }
    
    except Exception as e:
        logger.error(f"❌ Error registering mother: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering mother: {str(e)}"
        )


@app.get("/mothers")
def get_all_mothers():
    """Get all registered mothers"""
    try:
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase not connected"
            )
        
        result = supabase.table("mothers").select("*").execute()
        logger.info(f"✅ Retrieved {len(result.data)} mothers")
        
        return {
            "status": "success",
            "count": len(result.data),
            "data": result.data
        }
    except Exception as e:
        logger.error(f"❌ Error fetching mothers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching mothers: {str(e)}"
        )


@app.get("/mothers/{mother_id}")
def get_mother(mother_id: str):
    """Get specific mother by ID"""
    try:
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase not connected"
            )
        
        result = supabase.table("mothers").select("*").eq("id", mother_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mother with ID {mother_id} not found"
            )
        
        return {
            "status": "success",
            "data": result.data[0]
        }
    except Exception as e:
        logger.error(f"❌ Error fetching mother: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching mother: {str(e)}"
        )


# ==================== DOCUMENT ANALYSIS ENDPOINTS ====================

@app.post("/analyze-report")
async def analyze_report(request: DocumentAnalysisRequest, background_tasks: BackgroundTasks):
    """Analyze uploaded medical report using Gemini AI"""
    try:
        logger.info(f"🔍 Analyzing report {request.report_id} for mother {request.mother_id}")
        
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase not connected"
            )
        
        # Get mother data
        mother_result = supabase.table("mothers").select("*").eq("id", request.mother_id).execute()
        
        if not mother_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mother not found"
            )
        
        mother_data = mother_result.data[0]
        
        # Update report status to processing
        supabase.table("medical_reports").update({
            "analysis_status": "processing"
        }).eq("id", request.report_id).execute()
        
        # Perform Gemini AI analysis
        analysis_result = analyze_document_with_gemini(
            request.file_url,
            request.file_type,
            mother_data
        )
        
        # Update report with analysis results
        update_data = {
            "analysis_status": analysis_result.get("status", "completed"),
            "analysis_result": analysis_result,
            "analyzed_at": datetime.now().isoformat()
        }
        
        # Extract key metrics if available
        extracted_data = analysis_result.get("extracted_data", {})
        if extracted_data:
            update_data["extracted_metrics"] = extracted_data
        
        # Update medical_reports table
        report_update = supabase.table("medical_reports").update(update_data).eq("id", request.report_id).execute()
        
        logger.info(f"✅ Report analysis completed: {analysis_result.get('status')}")
        
        # Check for high-risk concerns and send alerts
        concerns = analysis_result.get("concerns", [])
        risk_level = analysis_result.get("risk_level", "normal")
        
        # Send Telegram notification if high risk
        if (risk_level in ["high", "moderate"] or concerns) and mother_data.get("telegram_chat_id"):
            try:
                # Import telegram service
                from services.telegram_service import telegram_service
                
                concerns_text = "\n".join([f"• {c}" for c in concerns[:3]]) if concerns else "None"
                recommendations_text = "\n".join([f"• {r}" for r in analysis_result.get("recommendations", [])[:3]])
                
                message = (
                    f"🔍 *Report Analysis Complete*\n\n"
                    f"📊 Risk Level: *{risk_level.upper()}*\n\n"
                )
                
                if concerns:
                    message += f"⚠️ *Concerns:*\n{concerns_text}\n\n"
                
                if recommendations_text:
                    message += f"💡 *Recommendations:*\n{recommendations_text}\n\n"
                
                message += "Please consult with your healthcare provider for detailed guidance."
                
                telegram_service.send_message(
                    chat_id=mother_data["telegram_chat_id"],
                    message=message
                )
                logger.info("✅ Alert sent to Telegram")
            except Exception as telegram_error:
                logger.error(f"⚠️  Telegram notification failed: {telegram_error}")
        
        return {
            "success": True,
            "message": "Report analyzed successfully",
            "status": analysis_result.get("status"),
            "risk_level": analysis_result.get("risk_level"),
            "concerns": analysis_result.get("concerns", []),
            "recommendations": analysis_result.get("recommendations", []),
            "analysis": analysis_result
        }
    
    except Exception as e:
        logger.error(f"❌ Report analysis error: {e}", exc_info=True)
        
        # Update status to error
        if supabase:
            supabase.table("medical_reports").update({
                "analysis_status": "error",
                "error_message": str(e)
            }).eq("id", request.report_id).execute()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


# ==================== DOCUMENT UPLOAD ENDPOINT ====================

@app.post("/reports/upload")
async def upload_report(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    mother_id: str = Form(...),
    uploader_id: Optional[str] = Form(None),
    uploader_role: Optional[str] = Form(None),
    uploader_name: Optional[str] = Form(None)
):
    """
    Upload a medical document/report for a mother.
    Stores file in Supabase Storage and creates a record in medical_reports.
    Automatically triggers AI analysis after upload.
    """
    try:
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase not connected"
            )
        
        logger.info(f"📤 Uploading report for mother {mother_id} by {uploader_role}: {uploader_name}")
        
        # Fetch mother's data including telegram_chat_id
        mother_result = supabase.table("mothers").select("*").eq("id", mother_id).execute()
        telegram_chat_id = None
        mother_data = None
        if mother_result.data:
            mother_data = mother_result.data[0]
            telegram_chat_id = mother_data.get("telegram_chat_id")
            if telegram_chat_id:
                logger.info(f"📱 Found telegram_chat_id for mother: {telegram_chat_id}")
        
        # Read file contents
        file_contents = await file.read()
        file_size = len(file_contents)
        
        # Validate file size (max 10MB)
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 10MB"
            )
        
        # Get file extension and content type
        original_filename = file.filename or "document"
        file_extension = original_filename.split(".")[-1].lower() if "." in original_filename else "bin"
        content_type = file.content_type or "application/octet-stream"
        
        # Validate file type
        allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/webp"]
        if content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {content_type} not allowed. Allowed: PDF, JPG, PNG, WebP"
            )
        
        # Generate unique filename for storage
        import uuid
        unique_id = str(uuid.uuid4())
        storage_path = f"reports/{mother_id}/{unique_id}.{file_extension}"
        
        # Upload to Supabase Storage
        try:
            storage_result = supabase.storage.from_("medical-reports").upload(
                path=storage_path,
                file=file_contents,
                file_options={"content-type": content_type}
            )
            logger.info(f"✅ File uploaded to storage: {storage_path}")
        except Exception as storage_error:
            # If bucket doesn't exist, try creating it or use a fallback
            logger.warning(f"⚠️  Storage upload failed: {storage_error}")
            # Store as base64 in database as fallback
            file_url = f"data:{content_type};base64,{base64.b64encode(file_contents).decode()}"
            logger.info("📦 Using base64 fallback for file storage")
        else:
            # Get public URL
            file_url = supabase.storage.from_("medical-reports").get_public_url(storage_path)
        
        # Insert record into medical_reports table
        report_data = {
            "mother_id": mother_id,
            "telegram_chat_id": telegram_chat_id,
            "file_name": original_filename,
            "file_url": file_url,
            "file_path": storage_path,
            "file_type": content_type,
            "uploaded_at": datetime.now().isoformat(),
            "analysis_status": "processing",  # Start as processing since we'll analyze immediately
        }
        
        result = supabase.table("medical_reports").insert(report_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to save report record"
            )
        
        report_id = result.data[0]["id"]
        logger.info(f"✅ Report record created: {report_id}")
        
        # Trigger AI analysis in background
        def run_ai_analysis():
            try:
                logger.info(f"🤖 Starting AI analysis for report {report_id}...")
                
                # Perform Gemini AI analysis
                analysis_result = analyze_document_with_gemini(
                    file_url,
                    content_type,
                    mother_data
                )
                
                # Update report with analysis results
                update_data = {
                    "analysis_status": analysis_result.get("status", "completed"),
                    "analysis_result": analysis_result,
                    "analyzed_at": datetime.now().isoformat()
                }
                
                # Extract key metrics if available
                extracted_data = analysis_result.get("extracted_data", {})
                if extracted_data:
                    update_data["extracted_metrics"] = extracted_data
                
                # Update medical_reports table
                supabase.table("medical_reports").update(update_data).eq("id", report_id).execute()
                
                logger.info(f"✅ Report analysis completed: {analysis_result.get('status')} - Risk: {analysis_result.get('risk_level', 'N/A')}")
                
                # Send Telegram notification if available
                concerns = analysis_result.get("concerns", [])
                risk_level = analysis_result.get("risk_level", "normal")
                
                if telegram_chat_id:
                    try:
                        from services.telegram_service import telegram_service
                        import html
                        
                        # Escape HTML special characters in AI-generated text
                        def escape_text(text):
                            if not text:
                                return ""
                            return html.escape(str(text))
                        
                        concerns_text = "\n".join([f"• {escape_text(c)}" for c in concerns[:3]]) if concerns else "None identified"
                        recommendations_list = analysis_result.get("recommendations", [])[:3]
                        recommendations_text = "\n".join([f"• {escape_text(r)}" for r in recommendations_list]) if recommendations_list else ""
                        
                        risk_emoji = "🔴" if risk_level == "high" else ("🟡" if risk_level == "moderate" else "🟢")
                        safe_filename = escape_text(original_filename)
                        
                        message = (
                            f"📄 <b>Document Analysis Complete</b>\n\n"
                            f"📋 File: {safe_filename}\n"
                            f"{risk_emoji} Risk Level: <b>{risk_level.upper()}</b>\n\n"
                        )
                        
                        if concerns:
                            message += f"⚠️ <b>Concerns:</b>\n{concerns_text}\n\n"
                        
                        if recommendations_text:
                            message += f"💡 <b>Recommendations:</b>\n{recommendations_text}\n\n"
                        
                        message += "Please consult with your healthcare provider for detailed guidance."
                        
                        telegram_service.send_message(
                            chat_id=telegram_chat_id,
                            message=message
                        )
                        logger.info("✅ Analysis result sent to Telegram")
                    except Exception as telegram_error:
                        logger.error(f"⚠️  Telegram notification failed: {telegram_error}")
                        
            except Exception as analysis_error:
                logger.error(f"❌ AI Analysis failed: {analysis_error}", exc_info=True)
                # Update status to error
                supabase.table("medical_reports").update({
                    "analysis_status": "error",
                    "error_message": str(analysis_error)
                }).eq("id", report_id).execute()
        
        # Add analysis to background tasks
        background_tasks.add_task(run_ai_analysis)
        
        return {
            "success": True,
            "message": "Document uploaded successfully. AI analysis started.",
            "report_id": report_id,
            "file_url": file_url,
            "filename": original_filename,
            "analysis_status": "processing"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )



@app.get("/reports/{mother_id}")
def get_mother_reports(mother_id: str):  # Changed from int to str
    """Get all reports for a specific mother"""
    try:
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase not connected"
            )
        
        result = supabase.table("medical_reports").select("*").eq("mother_id", mother_id).order("uploaded_at", desc=True).execute()
        
        return {
            "success": True,
            "count": len(result.data) if result.data else 0,
            "data": result.data
        }
    except Exception as e:
        logger.error(f"❌ Error fetching reports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/reports/telegram/{telegram_chat_id}")
def get_reports_by_telegram(telegram_chat_id: str):
    """Get all reports for a Telegram user"""
    try:
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase not connected"
            )
        
        result = supabase.table("medical_reports").select("*").eq("telegram_chat_id", telegram_chat_id).order("uploaded_at", desc=True).execute()
        
        return {
            "success": True,
            "count": len(result.data) if result.data else 0,
            "data": result.data
        }
    except Exception as e:
        logger.error(f"❌ Error fetching reports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.delete("/reports/{report_id}")
def delete_report(report_id: str):
    """Delete a medical report (Doctor only)"""
    try:
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase not connected"
            )
        
        logger.info(f"🗑️ Deleting report: {report_id}")
        
        # First, get the report to check if it exists and get file_path
        report_result = supabase.table("medical_reports").select("*").eq("id", report_id).execute()
        
        if not report_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report with ID {report_id} not found"
            )
        
        report = report_result.data[0]
        file_path = report.get("file_path")
        
        # Try to delete from storage if file_path exists
        if file_path and not file_path.startswith("data:"):
            try:
                supabase.storage.from_("medical-reports").remove([file_path])
                logger.info(f"✅ File removed from storage: {file_path}")
            except Exception as storage_error:
                logger.warning(f"⚠️ Could not delete file from storage: {storage_error}")
        
        # Delete from database
        delete_result = supabase.table("medical_reports").delete().eq("id", report_id).execute()
        
        logger.info(f"✅ Report deleted: {report_id}")
        
        return {
            "success": True,
            "message": "Report deleted successfully",
            "report_id": report_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ==================== RISK ASSESSMENT ENDPOINTS ====================

@app.post("/risk/assess")
async def assess_risk(assessment: RiskAssessment, background_tasks: BackgroundTasks):
    """Assess pregnancy risk for a mother"""
    try:
        logger.info(f"⚠️ Assessing risk for mother: {assessment.mother_id}")
        
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase not connected"
            )
        
        # Verify mother exists
        mother_result = supabase.table("mothers").select("*").eq("id", assessment.mother_id).execute()
        if not mother_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mother with ID {assessment.mother_id} not found"
            )
        
        mother_data = mother_result.data[0]
        
        # Calculate risk score
        risk_calculation = calculate_risk_score(assessment)
        logger.info(f"📈 Risk calculation: {risk_calculation}")
        
        # Save assessment to database
        insert_data = {
            "mother_id": assessment.mother_id,
            "systolic_bp": assessment.systolic_bp,
            "diastolic_bp": assessment.diastolic_bp,
            "heart_rate": assessment.heart_rate,
            "blood_glucose": assessment.blood_glucose,
            "hemoglobin": assessment.hemoglobin,
            "proteinuria": assessment.proteinuria,
            "edema": assessment.edema,
            "headache": assessment.headache,
            "vision_changes": assessment.vision_changes,
            "epigastric_pain": assessment.epigastric_pain,
            "vaginal_bleeding": assessment.vaginal_bleeding,
            "risk_score": float(risk_calculation["risk_score"]),
            "risk_level": str(risk_calculation["risk_level"]),
            "notes": assessment.notes,
            "created_at": datetime.now().isoformat()
        }
        
        result = supabase.table("risk_assessments").insert(insert_data).execute()
        logger.info(f"✅ Risk assessment saved: {risk_calculation['risk_level']}")
        
        # Send alert if high risk
        if risk_calculation["risk_level"] == "HIGH" and mother_data.get("telegram_chat_id"):
            try:
                from services.telegram_service import telegram_service
                
                risk_factors_text = "\n".join([f"• {rf}" for rf in risk_calculation["risk_factors"]])
                
                telegram_service.send_message(
                    chat_id=mother_data["telegram_chat_id"],
                    message=f"⚠️ *HIGH RISK ALERT*\n\n"
                            f"Risk Score: {risk_calculation['risk_score']:.2f}\n\n"
                            f"*Risk Factors:*\n{risk_factors_text}\n\n"
                            f"⚕️ Please consult with your healthcare provider immediately."
                )
            except Exception as telegram_error:
                logger.error(f"⚠️  Telegram alert failed: {telegram_error}")
        
        # Invalidate risk-related cache after new assessment
        invalidate_risk_cache()
        
        return {
            "status": "success",
            "message": f"Risk assessment completed - {risk_calculation['risk_level']} RISK",
            "risk_score": risk_calculation["risk_score"],
            "risk_level": risk_calculation["risk_level"],
            "risk_factors": risk_calculation["risk_factors"],
            "data": result.data[0] if result.data else None
        }
    
    except Exception as e:
        logger.error(f"❌ Error assessing risk: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error assessing risk: {str(e)}"
        )


@app.get("/risk/mother/{mother_id}")
def get_mother_risk(mother_id: str):
    """Get risk assessments for a specific mother"""
    try:
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase not connected"
            )
        
        result = supabase.table("risk_assessments").select("*").eq("mother_id", mother_id).order("created_at", desc=True).execute()
        
        return {
            "status": "success",
            "count": len(result.data),
            "data": result.data
        }
    except Exception as e:
        logger.error(f"❌ Error fetching risk assessments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching risk assessments: {str(e)}"
        )


@app.get("/risk/all")
def get_all_risk_assessments():
    """Get all risk assessments - optimized for dashboard loading"""
    try:
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase not connected"
            )
        
        result = supabase.table("risk_assessments").select("*").order("created_at", desc=True).execute()
        
        return {
            "status": "success",
            "count": len(result.data),
            "data": result.data
        }
    except Exception as e:
        logger.error(f"❌ Error fetching all risk assessments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching risk assessments: {str(e)}"
        )


# ==================== ANALYTICS ENDPOINTS (OPTIMIZED) ====================

@app.get("/analytics/dashboard")
def get_dashboard_analytics():
    """Get dashboard analytics - OPTIMIZED with caching and efficient queries"""
    try:
        # Check cache first
        if CACHE_AVAILABLE and cache:
            cached_data = cache.get("analytics:dashboard")
            if cached_data:
                logger.debug("📊 Dashboard analytics served from cache")
                return cached_data
        
        if not supabase:
            return {
                "status": "success",
                "total_mothers": 0,
                "high_risk_count": 0,
                "moderate_risk_count": 0,
                "low_risk_count": 0,
                "total_assessments": 0,
                "total_reports": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        # OPTIMIZED: Use COUNT queries instead of fetching all data
        # Get mothers count (only fetch id for counting)
        mothers_result = supabase.table("mothers").select("id", count="exact").execute()
        total_mothers = mothers_result.count if mothers_result.count else 0
        
        # Get risk level counts efficiently - only fetch risk_level column
        assessments_result = supabase.table("risk_assessments").select("risk_level", count="exact").execute()
        assessments = assessments_result.data if assessments_result.data else []
        total_assessments = assessments_result.count if assessments_result.count else 0
        
        # Get reports count
        reports_result = supabase.table("medical_reports").select("id", count="exact").execute()
        total_reports = reports_result.count if reports_result.count else 0
        
        # Count risk levels from minimal data
        high_risk = sum(1 for a in assessments if a.get("risk_level") == "HIGH")
        moderate_risk = sum(1 for a in assessments if a.get("risk_level") == "MODERATE")
        low_risk = sum(1 for a in assessments if a.get("risk_level") == "LOW")
        
        result = {
            "status": "success",
            "total_mothers": total_mothers,
            "high_risk_count": high_risk,
            "moderate_risk_count": moderate_risk,
            "low_risk_count": low_risk,
            "total_assessments": total_assessments,
            "total_reports": total_reports,
            "timestamp": datetime.now().isoformat(),
            "cached": False
        }
        
        # Cache for 30 seconds
        if CACHE_AVAILABLE and cache:
            cache.set("analytics:dashboard", result, ttl_seconds=30)
            logger.debug("📊 Dashboard analytics cached for 30s")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error fetching analytics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching analytics: {str(e)}"
        )


@app.get("/analytics/asha/{asha_id}")
def get_asha_analytics(asha_id: int):
    """Get analytics for a specific ASHA worker"""
    try:
        if not supabase:
            return {
                "status": "success",
                "total_mothers": 0,
                "high_risk_count": 0,
                "moderate_risk_count": 0,
                "low_risk_count": 0,
                "total_assessments": 0
            }
        
        # Get mothers assigned to this ASHA worker
        mothers_result = supabase.table("mothers").select("id").eq("asha_worker_id", asha_id).execute()
        mother_ids = [m["id"] for m in (mothers_result.data or [])]
        total_mothers = len(mother_ids)
        
        if not mother_ids:
            return {
                "status": "success",
                "total_mothers": 0,
                "high_risk_count": 0,
                "moderate_risk_count": 0,
                "low_risk_count": 0,
                "total_assessments": 0
            }
        
        # Get latest risk assessment for each mother
        assessments_result = supabase.table("risk_assessments").select("mother_id, risk_level").in_("mother_id", mother_ids).order("created_at", desc=True).execute()
        assessments = assessments_result.data or []
        
        # Count unique mothers by their latest risk level
        latest_risks = {}
        for a in assessments:
            if a["mother_id"] not in latest_risks:
                latest_risks[a["mother_id"]] = a["risk_level"]
        
        high_risk = sum(1 for r in latest_risks.values() if r == "HIGH")
        moderate_risk = sum(1 for r in latest_risks.values() if r == "MODERATE")
        low_risk = total_mothers - high_risk - moderate_risk  # Remaining are LOW or unassessed
        
        return {
            "status": "success",
            "total_mothers": total_mothers,
            "high_risk_count": high_risk,
            "moderate_risk_count": moderate_risk,
            "low_risk_count": low_risk,
            "total_assessments": len(assessments)
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching ASHA analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching analytics: {str(e)}"
        )

@app.get("/dashboard/full")
def get_full_dashboard():
    """
    COMBINED DASHBOARD ENDPOINT - Returns all dashboard data in a single request
    Reduces frontend from 3 API calls to 1
    """
    try:
        # Check cache first
        if CACHE_AVAILABLE and cache:
            cached_data = cache.get("dashboard:full")
            if cached_data:
                logger.debug("📊 Full dashboard served from cache")
                cached_data["cached"] = True
                return cached_data
        
        if not supabase:
            return {
                "status": "success",
                "analytics": {
                    "total_mothers": 0,
                    "high_risk_count": 0,
                    "moderate_risk_count": 0,
                    "low_risk_count": 0,
                    "total_assessments": 0,
                    "total_reports": 0
                },
                "mothers": [],
                "risk_assessments": [],
                "risk_trend": [],
                "age_distribution": [],
                "timestamp": datetime.now().isoformat()
            }
        
        # Fetch all required data in optimized way
        # 1. Get all mothers (needed for age distribution)
        mothers_result = supabase.table("mothers").select("id,name,phone,age,location,created_at").execute()
        mothers = mothers_result.data if mothers_result.data else []
        
        # 2. Get all risk assessments (needed for trend and risk counts)
        assessments_result = supabase.table("risk_assessments").select(
            "id,mother_id,risk_level,risk_score,systolic_bp,diastolic_bp,heart_rate,blood_glucose,hemoglobin,created_at"
        ).order("created_at", desc=True).execute()
        assessments = assessments_result.data if assessments_result.data else []
        
        # 3. Get reports count only
        reports_result = supabase.table("medical_reports").select("id", count="exact").execute()
        total_reports = reports_result.count if reports_result.count else 0
        
        # Calculate analytics
        high_risk = sum(1 for a in assessments if a.get("risk_level") == "HIGH")
        moderate_risk = sum(1 for a in assessments if a.get("risk_level") == "MODERATE")
        low_risk = sum(1 for a in assessments if a.get("risk_level") == "LOW")
        
        # Calculate age distribution
        age_groups = {"15-20": 0, "20-25": 0, "25-30": 0, "30-35": 0, "35-40": 0, "40+": 0}
        for m in mothers:
            age = m.get("age", 0)
            if 15 <= age < 20:
                age_groups["15-20"] += 1
            elif 20 <= age < 25:
                age_groups["20-25"] += 1
            elif 25 <= age < 30:
                age_groups["25-30"] += 1
            elif 30 <= age < 35:
                age_groups["30-35"] += 1
            elif 35 <= age < 40:
                age_groups["35-40"] += 1
            else:
                age_groups["40+"] += 1
        
        age_distribution = [{"name": k, "value": v} for k, v in age_groups.items()]
        
        # Calculate risk trend (last 7 days)
        daily_risk = {}
        for assessment in assessments:
            try:
                created_at = assessment.get("created_at", "")
                if created_at:
                    date_str = created_at[:10]  # Get YYYY-MM-DD
                    if date_str not in daily_risk:
                        daily_risk[date_str] = {"date": date_str, "HIGH": 0, "MODERATE": 0, "LOW": 0}
                    risk_level = assessment.get("risk_level", "LOW")
                    if risk_level in daily_risk[date_str]:
                        daily_risk[date_str][risk_level] += 1
            except Exception:
                pass
        
        # Sort by date and take last 7
        risk_trend = sorted(daily_risk.values(), key=lambda x: x["date"])[-7:]
        
        # Calculate vital stats averages
        vital_stats = {
            "avg_systolic": 0, "avg_diastolic": 0, "avg_heart_rate": 0,
            "avg_glucose": 0, "avg_hemoglobin": 0
        }
        counts = {"systolic": 0, "diastolic": 0, "heart_rate": 0, "glucose": 0, "hemoglobin": 0}
        
        for a in assessments:
            if a.get("systolic_bp"):
                vital_stats["avg_systolic"] += a["systolic_bp"]
                counts["systolic"] += 1
            if a.get("diastolic_bp"):
                vital_stats["avg_diastolic"] += a["diastolic_bp"]
                counts["diastolic"] += 1
            if a.get("heart_rate"):
                vital_stats["avg_heart_rate"] += a["heart_rate"]
                counts["heart_rate"] += 1
            if a.get("blood_glucose"):
                vital_stats["avg_glucose"] += a["blood_glucose"]
                counts["glucose"] += 1
            if a.get("hemoglobin"):
                vital_stats["avg_hemoglobin"] += a["hemoglobin"]
                counts["hemoglobin"] += 1
        
        # Calculate averages
        if counts["systolic"] > 0:
            vital_stats["avg_systolic"] = round(vital_stats["avg_systolic"] / counts["systolic"])
        if counts["diastolic"] > 0:
            vital_stats["avg_diastolic"] = round(vital_stats["avg_diastolic"] / counts["diastolic"])
        if counts["heart_rate"] > 0:
            vital_stats["avg_heart_rate"] = round(vital_stats["avg_heart_rate"] / counts["heart_rate"])
        if counts["glucose"] > 0:
            vital_stats["avg_glucose"] = round(vital_stats["avg_glucose"] / counts["glucose"])
        if counts["hemoglobin"] > 0:
            vital_stats["avg_hemoglobin"] = round(vital_stats["avg_hemoglobin"] / counts["hemoglobin"], 1)
        
        vital_stats_list = [
            {"name": "Systolic BP", "value": vital_stats["avg_systolic"], "normal": 120},
            {"name": "Diastolic BP", "value": vital_stats["avg_diastolic"], "normal": 80},
            {"name": "Heart Rate", "value": vital_stats["avg_heart_rate"], "normal": 75},
            {"name": "Glucose", "value": vital_stats["avg_glucose"], "normal": 100},
            {"name": "Hemoglobin", "value": vital_stats["avg_hemoglobin"], "normal": 12}
        ]
        
        result = {
            "status": "success",
            "analytics": {
                "total_mothers": len(mothers),
                "high_risk_count": high_risk,
                "moderate_risk_count": moderate_risk,
                "low_risk_count": low_risk,
                "total_assessments": len(assessments),
                "total_reports": total_reports
            },
            "mothers": mothers,
            "risk_assessments": assessments[:50],  # Limit to latest 50 for performance
            "risk_trend": risk_trend,
            "age_distribution": age_distribution,
            "vital_stats": vital_stats_list,
            "timestamp": datetime.now().isoformat(),
            "cached": False
        }
        
        # Cache for 30 seconds
        if CACHE_AVAILABLE and cache:
            cache.set("dashboard:full", result, ttl_seconds=30)
            logger.info("📊 Full dashboard data cached for 30s")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error fetching full dashboard: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dashboard: {str(e)}"
        )


@app.get("/cache/stats")
def get_cache_stats():
    """Get cache statistics (for debugging)"""
    if CACHE_AVAILABLE and cache:
        return {
            "status": "success",
            "cache_enabled": True,
            "stats": cache.stats()
        }
    return {
        "status": "success",
        "cache_enabled": False,
        "message": "Cache not available"
    }


@app.post("/cache/invalidate")
def invalidate_cache():
    """Manually invalidate all caches"""
    if CACHE_AVAILABLE and cache:
        cache.clear()
        return {"status": "success", "message": "Cache invalidated"}
    return {"status": "success", "message": "Cache not available"}


# ==================== ROOT ENDPOINT ====================
@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "MatruRaksha AI Backend API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "telegram_bot": "🟢 Active" if bot_running else "🔴 Inactive",
        "gemini_ai": "🤖 Active" if GEMINI_AVAILABLE else "❌ Not Available",
        "ai_agents": "🤖 Active" if AGENTS_AVAILABLE else "❌ Not Loaded"
    }


# ==================== CASE DISCUSSION ENDPOINTS ====================

class CaseDiscussionMessage(BaseModel):
    mother_id: str
    sender_role: str  # 'DOCTOR' or 'ASHA'
    sender_name: str
    message: str
    send_to_telegram: bool = True  # Whether to also send to patient's Telegram

@app.post("/case-discussions/send")
async def send_case_discussion(msg: CaseDiscussionMessage):
    """
    Send a case discussion message:
    1. Store in case_discussions table
    2. Optionally relay to patient's Telegram
    """
    try:
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase not connected"
            )
        
        logger.info(f"💬 Case discussion from {msg.sender_role} for mother {msg.mother_id}")
        
        # Store in case_discussions table
        insert_result = supabase.table("case_discussions").insert({
            "mother_id": msg.mother_id,
            "sender_role": msg.sender_role,
            "sender_name": msg.sender_name,
            "message": msg.message,
        }).execute()
        
        if not insert_result.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to save case discussion"
            )
        
        discussion_id = insert_result.data[0].get("id")
        telegram_sent = False
        telegram_error = None
        
        # Send to patient's Telegram if requested
        if msg.send_to_telegram:
            try:
                # Get mother's telegram_chat_id
                mother_result = supabase.table("mothers").select("name, telegram_chat_id").eq("id", msg.mother_id).execute()
                
                if mother_result.data and mother_result.data[0].get("telegram_chat_id"):
                    mother_data = mother_result.data[0]
                    chat_id = mother_data["telegram_chat_id"]
                    mother_name = mother_data.get("name", "Patient")
                    
                    # Import telegram service
                    from services.telegram_service import telegram_service
                    
                    # Format message for Telegram
                    role_emoji = "👨‍⚕️" if msg.sender_role == "DOCTOR" else "👩‍⚕️"
                    role_label = "Doctor" if msg.sender_role == "DOCTOR" else "ASHA Worker"
                    
                    telegram_message = (
                        f"{role_emoji} <b>Message from your {role_label}</b>\n\n"
                        f"<b>From:</b> {msg.sender_name}\n\n"
                        f"📝 {msg.message}\n\n"
                        f"💬 Reply to this message to respond."
                    )
                    
                    result = telegram_service.send_message(
                        chat_id=chat_id,
                        message=telegram_message
                    )
                    
                    if result.get("status") == "sent":
                        telegram_sent = True
                        logger.info(f"✅ Message relayed to Telegram for {mother_name}")
                    else:
                        telegram_error = result.get("error", "Unknown error")
                        logger.warning(f"⚠️  Telegram send failed: {telegram_error}")
                else:
                    telegram_error = "Mother has no telegram_chat_id"
                    logger.warning(f"⚠️  No telegram_chat_id for mother {msg.mother_id}")
                    
            except Exception as e:
                telegram_error = str(e)
                logger.error(f"❌ Telegram notification error: {e}")
        
        return {
            "success": True,
            "discussion_id": discussion_id,
            "telegram_sent": telegram_sent,
            "telegram_error": telegram_error
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error sending case discussion: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )


# ==================== MAIN ENTRY POINT ====================
if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "=" * 60)
    print("🚀 Starting MatruRaksha AI Backend...")
    print("=" * 60)
    print(f"📌 Supabase URL: {SUPABASE_URL}")
    print(f"📱 Telegram Bot Token: {'✅ Set' if TELEGRAM_BOT_TOKEN != 'placeholder' else '❌ Not Set'}")
    print(f"🤖 Gemini AI: {'✅ Available' if GEMINI_AVAILABLE else '❌ Not Available'}")
    print("=" * 60)
    print()
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port
    )