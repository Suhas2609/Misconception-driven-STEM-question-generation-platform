"""Admin routes for data management (misconception seeding, system maintenance)."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..models.user import UserModel
from ..routes.auth import get_current_user
from ..services.misconception_service import get_misconception_service

router = APIRouter()
logger = logging.getLogger(__name__)


class SeedMisconceptionsRequest(BaseModel):
    """Request to seed misconceptions from CSV files."""
    csv_files: list[str]  # List of CSV filenames in data/misconceptions/


@router.post("/seed-misconceptions")
async def seed_misconceptions_from_csv(
    payload: SeedMisconceptionsRequest,
    current_user: UserModel = Depends(get_current_user),
):
    """
    Load misconceptions from CSV files into MongoDB + ChromaDB.
    
    **Admin only** - In production, add role-based access control!
    
    CSV files should be in: data/misconceptions/*.csv
    
    CSV Format:
    ```
    pattern,correct_concept,subject_area,topic,difficulty
    "Students think force is needed to maintain motion","Objects maintain constant velocity without force (Newton's 1st law)","physics","Newton's Laws","medium"
    ```
    """
    logger.info(f"🔐 Admin misconception seeding requested by {current_user.email}")
    
    misconception_service = get_misconception_service()
    misconceptions_dir = Path("data/misconceptions")
    
    if not misconceptions_dir.exists():
        misconceptions_dir.mkdir(parents=True, exist_ok=True)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Misconceptions directory not found: {misconceptions_dir}"
        )
    
    total_seeded = 0
    results = []
    
    for csv_filename in payload.csv_files:
        csv_path = misconceptions_dir / csv_filename
        
        if not csv_path.exists():
            logger.warning(f"⚠️ CSV file not found: {csv_path}")
            results.append({
                "file": csv_filename,
                "status": "not_found",
                "count": 0
            })
            continue
        
        try:
            count = await misconception_service.seed_from_csv(csv_path)
            total_seeded += count
            results.append({
                "file": csv_filename,
                "status": "success",
                "count": count
            })
            logger.info(f"✅ Seeded {count} misconceptions from {csv_filename}")
            
        except Exception as e:
            logger.error(f"❌ Failed to seed from {csv_filename}: {e}")
            results.append({
                "file": csv_filename,
                "status": "error",
                "count": 0,
                "error": str(e)
            })
    
    return {
        "total_seeded": total_seeded,
        "files_processed": len(payload.csv_files),
        "results": results
    }


@router.get("/misconception-stats")
async def get_misconception_stats(
    current_user: UserModel = Depends(get_current_user),
):
    """Get statistics about stored misconceptions."""
    from ..db.mongo import get_collection
    
    misconceptions_col = get_collection("misconceptions")
    ai_misconceptions_col = get_collection("ai_generated_misconceptions")
    
    # Count by source
    total_validated = await misconceptions_col.count_documents({"validated": True})
    total_csv = await misconceptions_col.count_documents({"source": "csv_seed"})
    total_ai_generated = await misconceptions_col.count_documents({"source": "gpt4o_synthesis"})
    total_from_feedback = await ai_misconceptions_col.count_documents({"source": "user_feedback"})
    
    # Count by subject
    pipeline = [
        {"$group": {"_id": "$subject_area", "count": {"$sum": 1}}}
    ]
    by_subject = []
    async for doc in misconceptions_col.aggregate(pipeline):
        by_subject.append({
            "subject": doc["_id"],
            "count": doc["count"]
        })
    
    return {
        "total_validated": total_validated,
        "total_csv_seeded": total_csv,
        "total_ai_generated": total_ai_generated,
        "total_from_user_feedback": total_from_feedback,
        "by_subject": by_subject
    }
