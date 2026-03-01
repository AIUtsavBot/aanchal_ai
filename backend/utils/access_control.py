"""
MatruRaksha - Access Control Utilities
Helper functions for role-based access control and data filtering
"""

import logging
from typing import Optional, List, Dict, Any
from fastapi import HTTPException

logger = logging.getLogger(__name__)


async def get_authorized_mothers(
    supabase_client,
    user_id: str,
    user_role: str,
    mother_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get list of mothers authorized for the current user based on their role
    
    Args:
        supabase_client: Supabase client instance
        user_id: Current user's ID
        user_role: User's role (DOCTOR, ASHA_WORKER, ADMIN)
        mother_id: Optional specific mother ID to check access for
    
    Returns:
        List of mother records the user is authorized to access
    
    Raises:
        HTTPException: If user has no access or mother not found
    """
    try:
        logger.info(f"🔐 get_authorized_mothers: user_id={user_id}, role={user_role}, mother_id={mother_id}")
        
        # Admins can access all mothers
        if user_role == "ADMIN":
            query = supabase_client.table("mothers").select("*")
            if mother_id:
                query = query.eq("id", mother_id)
            result = query.execute()
            return result.data or []
        
        # For doctors and ASHA workers, filter by assignment
        if user_role == "DOCTOR":
            # Get doctor record
            doctor_result = supabase_client.table("doctors") \
                .select("id") \
                .eq("user_profile_id", user_id) \
                .execute()
            
            logger.info(f"🔐 Doctor lookup for user_profile_id={user_id}: {doctor_result.data}")
            
            if not doctor_result.data:
                logger.warning(f"Doctor profile not found for user_profile_id: {user_id}, granting full access")
                # Fallback: allow access to all mothers if doctor record not linked
                query = supabase_client.table("mothers").select("*")
                if mother_id:
                    query = query.eq("id", mother_id)
                result = query.execute()
                return result.data or []
            
            doctor_id = doctor_result.data[0]["id"]
            
            # Get mothers assigned to this doctor
            query = supabase_client.table("mothers") \
                .select("*") \
                .eq("doctor_id", doctor_id)
            
            if mother_id:
                query = query.eq("id", mother_id)
            
            result = query.execute()
            logger.info(f"🔐 Mothers for doctor_id={doctor_id}: found {len(result.data or [])} mothers")
            if mother_id and not result.data:
                raise HTTPException(
                    status_code=403,
                    detail="You don't have access to this mother's records"
                )
            
            return result.data or []
        
        elif user_role == "ASHA_WORKER":
            # Get ASHA worker record
            asha_result = supabase_client.table("asha_workers") \
                .select("id") \
                .eq("user_profile_id", user_id) \
                .execute()
            
            if not asha_result.data:
                logger.warning(f"ASHA worker profile not found for user_profile_id: {user_id}, granting full access")
                # Fallback: allow access to all mothers if ASHA record not linked
                query = supabase_client.table("mothers").select("*")
                if mother_id:
                    query = query.eq("id", mother_id)
                result = query.execute()
                return result.data or []
            
            asha_worker_id = asha_result.data[0]["id"]
            
            # Get mothers assigned to this ASHA worker
            query = supabase_client.table("mothers") \
                .select("*") \
                .eq("asha_worker_id", asha_worker_id)
            
            if mother_id:
                query = query.eq("id", mother_id)
            
            result = query.execute()
            if mother_id and not result.data:
                raise HTTPException(
                    status_code=403,
                    detail="You don't have access to this mother's records"
                )
            
            return result.data or []
        
        elif user_role == "MOTHER":
            # Assume user_id from auth maps to mother's id
            query = supabase_client.table("mothers").select("*").eq("id", user_id)
            if mother_id:
                query = query.eq("id", mother_id)
            result = query.execute()
            if mother_id and not result.data:
                raise HTTPException(status_code=403, detail="You can only access your own records")
            return result.data or []
            
        else:
            raise HTTPException(
                status_code=403,
                detail=f"Invalid role: {user_role}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting authorized mothers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_authorized_children(
    supabase_client,
    user_id: str,
    user_role: str,
    child_id: Optional[str] = None, 
    mother_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get list of children authorized for the current user based on mother assignments
    
    Args:
        supabase_client: Supabase client instance
        user_id: Current user's ID
        user_role: User's role (DOCTOR, ASHA_WORKER, ADMIN)
        child_id: Optional specific child ID to check access for
        mother_id: Optional filter by specific mother ID
    
    Returns:
        List of child records the user is authorized to access
    
    Raises:
        HTTPException: If user has no access or child not found
    """
    try:
        # First, get authorized mother IDs for this user
        authorized_mothers = await get_authorized_mothers(
            supabase_client=supabase_client,
            user_id=user_id,
            user_role=user_role,
            mother_id=mother_id
        )
        
        if not authorized_mothers:
            logger.warning(f"🔐 No authorized mothers for user {user_id} (role={user_role})")
            return []
        
        authorized_mother_ids = [m["id"] for m in authorized_mothers]
        logger.info(f"🔐 Authorized mother IDs: {authorized_mother_ids}")
        
        # Get children belonging to authorized mothers
        query = supabase_client.table("children") \
            .select("*") \
            .in_("mother_id", authorized_mother_ids)
        
        if child_id:
            query = query.eq("id", child_id)
        
        result = query.execute()
        logger.info(f"🔐 Children query result: found {len(result.data or [])} children (child_id filter={child_id})")
        
        if child_id and not result.data:
            raise HTTPException(
                status_code=403,
                detail=f"Child {child_id} not found among mothers {authorized_mother_ids}"
            )
        
        return result.data or []
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting authorized children: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def verify_mother_access(
    supabase_client,
    user_id: str,
    user_role: str,
    mother_id: str
) -> Dict[str, Any]:
    """
    Verify user has access to a specific mother and return mother data
    
    Raises HTTPException if access denied
    """
    mothers = await get_authorized_mothers(
        supabase_client=supabase_client,
        user_id=user_id,
        user_role=user_role,
        mother_id=mother_id
    )
    
    if not mothers:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied to mother ID: {mother_id}"
        )
    
    return mothers[0]


async def verify_child_access(
    supabase_client,
    user_id: str,
    user_role: str,
    child_id: str
) -> Dict[str, Any]:
    """
    Verify user has access to a specific child and return child data
    
    Raises HTTPException if access denied
    """
    children = await get_authorized_children(
        supabase_client=supabase_client,
        user_id=user_id,
        user_role=user_role,
        child_id=child_id
    )
    
    if not children:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied to child ID: {child_id}"
        )
    
    return children[0]
