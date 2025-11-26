"""
MatruRaksha AI - Document Analyzer Service  
Analyzes images and PDFs using Google Gemini Vision
File: services/document_analyzer.py
"""

import os
import logging
import io
from typing import Dict, List, Optional
from PIL import Image
import PyPDF2
from pdf2image import convert_from_bytes
import google.generativeai as genai
import json

logger = logging.getLogger(__name__)

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


class DocumentAnalyzer:
    """Analyzes medical documents (images and PDFs) using Gemini"""
    
    def __init__(self):
        if not GEMINI_API_KEY:
            logger.warning("⚠️  GEMINI_API_KEY not set - document analysis will not work")
            self.model = None
        else:
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            logger.info("✅ Gemini model initialized")
    
    async def analyze_document(self, file_bytes: bytes, filename: str, mother_id: str) -> Dict:
        """
        Main entry point for document analysis
        Handles both images and PDFs
        """
        if not self.model:
            return {
                "success": False,
                "error": "Gemini API not configured. Please set GEMINI_API_KEY in .env file"
            }
        
        logger.info(f"📄 Analyzing document: {filename} for mother {mother_id}")
        
        file_extension = filename.lower().split('.')[-1]
        
        if file_extension == 'pdf':
            return await self.analyze_pdf(file_bytes, filename, mother_id)
        elif file_extension in ['jpg', 'jpeg', 'png', 'webp']:
            return await self.analyze_image(file_bytes, filename, mother_id)
        else:
            return {
                "success": False,
                "error": f"Unsupported file type: {file_extension}. Please send PDF, JPG, or PNG files."
            }
    
    async def analyze_pdf(self, pdf_bytes: bytes, filename: str, mother_id: str) -> Dict:
        """
        Analyze PDF medical report
        1. Extract text
        2. Convert pages to images
        3. Analyze with Gemini Vision
        """
        logger.info(f"📑 Analyzing PDF: {filename}")
        
        try:
            # Extract text from PDF
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
            
            logger.info(f"✅ Extracted {len(text_content)} characters of text")
            
            # Convert PDF first page to image for vision analysis
            images = convert_from_bytes(pdf_bytes, dpi=150, first_page=1, last_page=1)
            logger.info(f"✅ Converted PDF to image")
            
            if images:
                # Analyze first page with Gemini Vision
                img_bytes = io.BytesIO()
                images[0].save(img_bytes, format='PNG')
                img_bytes = img_bytes.getvalue()
                
                visual_analysis = await self.vision_analyze(img_bytes, "pdf_page_1", text_content)
            else:
                # Fall back to text-only analysis
                visual_analysis = await self.text_only_analyze(text_content, filename)
            
            return {
                "success": True,
                "filename": filename,
                "document_type": "pdf",
                "pages": len(pdf_reader.pages),
                "text_length": len(text_content),
                **visual_analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing PDF: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to analyze PDF: {str(e)}"
            }
    
    async def analyze_image(self, image_bytes: bytes, filename: str, mother_id: str) -> Dict:
        """
        Analyze image medical report using Gemini Vision
        """
        logger.info(f"🖼️ Analyzing image: {filename}")
        
        try:
            # Analyze with Gemini Vision
            visual_analysis = await self.vision_analyze(image_bytes, filename, None)
            
            return {
                "success": True,
                "filename": filename,
                "document_type": "image",
                **visual_analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to analyze image: {str(e)}"
            }
    
    async def vision_analyze(self, image_bytes: bytes, image_name: str, extracted_text: Optional[str]) -> Dict:
        """
        Use Gemini Vision API to analyze medical document image
        """
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Prepare comprehensive prompt for medical document analysis
            prompt = """You are a medical document analysis AI. Analyze this medical report image and extract ALL health information.

Extract and return in this EXACT JSON format:
{
    "document_type": "lab report/prescription/ultrasound/checkup report/etc",
    "date": "YYYY-MM-DD format or null if not visible",
    "health_metrics": {
        "blood_pressure": "systolic/diastolic (e.g., 120/80) or null",
        "hemoglobin": "value in g/dL (e.g., 12.5) or null",
        "glucose": "value in mg/dL or null",
        "weight": "value in kg or null",
        "hba1c": "value or null",
        "platelets": "value or null",
        "wbc": "value or null",
        "other_values": {}
    },
    "concerns": ["list any abnormal values or health concerns mentioned"],
    "recommendations": ["list any doctor recommendations or advice"],
    "summary": "brief 2-3 sentence summary of the report"
}

IMPORTANT:
- Return ONLY valid JSON, no other text
- Extract actual numerical values where visible
- If value not clearly visible, use null
- Be thorough - look for ALL health metrics
"""
            
            # Call Gemini Vision
            response = self.model.generate_content([prompt, image])
            result_text = response.text
            
            logger.info(f"Gemini response received: {len(result_text)} characters")
            
            # Parse JSON response
            try:
                # Clean the response - remove markdown code blocks
                result_text = result_text.strip()
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0].strip()
                
                result_json = json.loads(result_text)
                
                # Extract and format the data
                return {
                    "analysis_summary": result_json.get("summary", "Medical report analyzed"),
                    "health_metrics": result_json.get("health_metrics", {}),
                    "concerns": result_json.get("concerns", []),
                    "recommendations": result_json.get("recommendations", []),
                    "document_type": result_json.get("document_type", "medical_report"),
                    "date": result_json.get("date")
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}")
                logger.error(f"Raw response: {result_text}")
                
                # Fallback: extract what we can from raw text
                return {
                    "analysis_summary": result_text[:500],
                    "health_metrics": {},
                    "concerns": [],
                    "recommendations": [],
                    "raw_text": result_text
                }
                
        except Exception as e:
            logger.error(f"Gemini Vision API error: {e}", exc_info=True)
            return {
                "analysis_summary": f"Error analyzing image: {str(e)}",
                "health_metrics": {},
                "concerns": [],
                "recommendations": [],
                "error": str(e)
            }
    
    async def text_only_analyze(self, text_content: str, filename: str) -> Dict:
        """
        Analyze text content when image analysis is not possible
        """
        try:
            prompt = f"""Analyze this medical document text and extract health information.

TEXT CONTENT:
{text_content[:3000]}

Return in this EXACT JSON format:
{{
    "summary": "brief summary",
    "health_metrics": {{}},
    "concerns": [],
    "recommendations": []
}}

Return ONLY valid JSON."""
            
            response = self.model.generate_content(prompt)
            result_text = response.text
            
            # Clean and parse
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            result_json = json.loads(result_text)
            
            return {
                "analysis_summary": result_json.get("summary", ""),
                "health_metrics": result_json.get("health_metrics", {}),
                "concerns": result_json.get("concerns", []),
                "recommendations": result_json.get("recommendations", [])
            }
            
        except Exception as e:
            logger.error(f"Text analysis error: {e}")
            return {
                "analysis_summary": "Document processed",
                "health_metrics": {},
                "concerns": [],
                "recommendations": []
            }


    async def analyze_and_update_history(self, file: Dict[str, Any], mother_id: Any) -> Dict[str, Any]:
        if not self.model:
            return {"success": False, "error": "AI not available"}
        try:
            fb = file.get('bytes')
            fn = file.get('filename') or 'document'
            analysis = await self.analyze_document(fb, fn, str(mother_id))
            from services.supabase_service import supabase
            from utils.toon_helper import json_to_toon
            prof = supabase.table('mothers').select('medical_history').eq('id', mother_id).execute()
            old_hist = (prof.data[0].get('medical_history') if prof.data else {}) or {}
            old_toon = json_to_toon(old_hist)
            prompt = (
                "Compare the OLD medical history with the NEW report analysis. "
                "Return an updated JSON with keys: conditions, medications, trend_analysis. "
                "Focus on changes and trends."
            )
            payload = [prompt, f"OLD:\n{old_toon}", f"NEW:\n{analysis.get('analysis_summary','')}"]
            resp = self.model.generate_content(payload)
            txt = resp.text.strip()
            if "```json" in txt:
                txt = txt.split("```json")[1].split("```")[0].strip()
            elif "```" in txt:
                txt = txt.split("```")[1].split("```")[0].strip()
            import json as _json
            try:
                new_hist = _json.loads(txt)
            except Exception:
                new_hist = {
                    "conditions": old_hist.get("conditions", []),
                    "medications": old_hist.get("medications", []),
                    "trend_analysis": analysis.get("analysis_summary", "")
                }
            supabase.table('mothers').update({"medical_history": new_hist}).eq('id', mother_id).execute()
            return {"success": True, "medical_history": new_hist, "analysis": analysis}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Global instance
document_analyzer = DocumentAnalyzer()
