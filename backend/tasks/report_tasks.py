"""
Report Generation Background Tasks
"""
import os
import io
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from celery import shared_task

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=2, time_limit=300)
def generate_postnatal_report_async(self, mother_id: str) -> Dict[str, Any]:
    """Generate postnatal care PDF report"""
    task_id = self.request.id
    logger.info(f"📄 Generating report for {mother_id}")
    
    try:
        from supabase import create_client
        supabase = create_client(os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_KEY", ""))
        
        mother_result = supabase.table("mothers").select("*").eq("id", mother_id).single().execute()
        mother = mother_result.data
        
        if not mother:
            return {"status": "failed", "error": "Mother not found"}
        
        # Generate simple report data
        report_data = {
            "mother_id": mother_id,
            "name": mother.get("name"),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        from services.cache_service import cache
        if cache:
            cache.set(f"report:{mother_id}:{task_id}", report_data, ttl_seconds=3600)
        
        logger.info(f"✅ Report generated for {mother_id}")
        return {"status": "success", "task_id": task_id, "mother_id": mother_id}
        
    except Exception as e:
        logger.error(f"❌ Report failed: {e}")
        return {"status": "failed", "error": str(e)}

@shared_task(bind=True, max_retries=2)
def generate_analytics_report_async(self, report_type: str = "daily") -> Dict[str, Any]:
    """Generate analytics report"""
    task_id = self.request.id
    logger.info(f"📊 Generating {report_type} analytics")
    
    try:
        from supabase import create_client
        supabase = create_client(os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_KEY", ""))
        
        mothers = supabase.table("mothers").select("id, status").execute().data or []
        
        report = {
            "report_type": report_type,
            "total_mothers": len(mothers),
            "pregnant": sum(1 for m in mothers if m.get("status") == "pregnant"),
            "postnatal": sum(1 for m in mothers if m.get("status") == "postnatal"),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Analytics report generated")
        return {"status": "success", "task_id": task_id, **report}
        
    except Exception as e:
        logger.error(f"❌ Analytics failed: {e}")
        return {"status": "failed", "error": str(e)}
