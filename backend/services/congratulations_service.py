"""
Congratulations Message Service
Generates personalized congratulations when delivery is completed
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import Gemini
gemini_client = None
try:
    from google import genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
    else:
        GEMINI_AVAILABLE = False
except Exception as e:
    logger.warning(f"Gemini not available: {e}")
    GEMINI_AVAILABLE = False


async def generate_congratulations_message(
    mother_name: str,
    child_name: Optional[str] = None,
    child_gender: Optional[str] = None,
    delivery_type: Optional[str] = None,
    language: str = "en"
) -> str:
    """
    Generate warm congratulations message using AI
    
    Args:
        mother_name: Mother's name
        child_name: Baby's name (optional)
        child_gender: 'male', 'female', or None
        delivery_type: Type of delivery
        language: Language code ('en', 'hi', 'mr', etc.)
    
    Returns:
        Personalized congratulations message
    """
    if not GEMINI_AVAILABLE or not gemini_client:
        logger.info("Gemini not available, using default message")
        return get_default_congratulations(mother_name, language)
    
    try:
        # Prepare child description
        child_desc = child_name or 'Baby'
        if child_gender == 'male':
            child_desc += ' (baby boy)'
        elif child_gender == 'female':
            child_desc += ' (baby girl)'
        
        # Delivery description
        delivery_desc = delivery_type or 'safe delivery'
        
        # Language instruction
        lang_instruction = ""
        if language == "hi":
            lang_instruction = "Respond in Hindi (Devanagari script)."
        elif language == "mr":
            lang_instruction = "Respond in Marathi (Devanagari script)."
        elif language == "ta":
            lang_instruction = "Respond in Tamil."
        else:
            lang_instruction = "Respond in English."
        
        prompt = f"""
You are a caring maternal health assistant. Generate a warm, heartfelt 
congratulations message for {mother_name} who just delivered her baby.

Child: {child_desc}
Delivery: {delivery_desc}

{lang_instruction}

Include these 4 elements (keep brief, warm, supportive):
1. 🎉 Warm congratulations (1-2 sentences)
2. 🍼 Transition message: "You're now part of SantanRaksha - our postnatal & child care program"
3. 💚 What's available: postnatal recovery support, breastfeeding help, baby health monitoring, vaccinations
4. ✨ Encouraging note about the beautiful journey ahead

Keep it to 3-4 short paragraphs. Be warm and encouraging but concise.
Use emojis appropriately (🎉👶💚).
"""

        response = gemini_client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt
        )
        
        message = response.text.strip()
        logger.info(f"✅ Generated congratulations message for {mother_name}")
        return message
        
    except Exception as e:
        logger.error(f"AI congratulations generation failed: {e}")
        return get_default_congratulations(mother_name, language)


def get_default_congratulations(mother_name: str, language: str = "en") -> str:
    """
    Fallback congratulations message if AI unavailable
    
    Args:
        mother_name: Mother's name
        language: Language code
    
    Returns:
        Default congratulations message
    """
    if language == "hi":
        return f"""
🎉 बधाई हो {mother_name}! 🎉

आपका शिशु सुरक्षित रूप से जन्म ले चुका है। यह एक नई और खूबसूरत यात्रा की शुरुआत है!

अब आप **SantanRaksha** (संतान रक्षा) का हिस्सा हैं - जहां हम आपके प्रसवोत्तर स्वास्थ्य और आपके बच्चे की देखभाल करते हैं। हम आपके साथ हैं - स्तनपान सलाह, शिशु स्वास्थ्य निगरानी, टीकाकरण, और बहुत कुछ के लिए!

आपको और आपके नन्हे मेहमान को ढेर सारी शुभकामनाएं! 💚👶
"""
    elif language == "mr":
        return f"""
🎉 अभिनंदन {mother_name}! 🎉

तुमचे बाळ सुरक्षितपणे जन्माला आले आहे. ही एक नवीन आणि सुंदर प्रवासाची सुरुवात आहे!

आता तुम्ही **SantanRaksha** (संतान रक्षा) चा भाग आहात - जिथे आम्ही तुमच्या प्रसूतीनंतरच्या आरोग्याची आणि तुमच्या बाळाची काळजी घेतो. आम्ही तुमच्यासोबत आहोत - स्तनपान सल्ला, बाळ आरोग्य, लसीकरण आणि बरेच काही!

तुम्हाला आणि तुमच्या नन्ह्या पाहुण्याला खूप खूप शुभेच्छा! 💚👶
"""
    else:  # English (default)
        return f"""
🎉 Congratulations {mother_name}! 🎉

Your baby has arrived safely! This is the beginning of a beautiful journey filled with precious moments.

You're now part of **SantanRaksha** - our comprehensive postnatal and child care program. We're here to support you every step of the way with postnatal recovery guidance, breastfeeding support, baby health monitoring, vaccination schedules, and so much more!

Wishing you and your little one all the health, happiness, and joy in the world! 💚👶
"""


def get_sms_congratulations(mother_name: str, language: str = "en") -> str:
    """
    Short congratulations for SMS (160 chars)
    
    Args:
        mother_name: Mother's name
        language: Language code
    
    Returns:
        Short congratulations message for SMS
    """
    if language == "hi":
        return f"बधाई हो {mother_name}! आप SantanRaksha का हिस्सा हैं। हम आपके और बच्चे के स्वास्थ्य की देखभाल करेंगे। 💚👶"
    elif language == "mr":
        return f"अभिनंदन {mother_name}! तुम्ही SantanRaksha चा भाग आहात. आम्ही तुमची आणि बाळाची काळजी घेऊ. 💚👶"
    else:
        return f"Congratulations {mother_name}! Welcome to SantanRaksha. We'll support you & baby's health journey. 💚👶"
