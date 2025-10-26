"""API route registrations."""

from fastapi import APIRouter

from . import assessment, auth, pdf, pdf_upload, question, response, user

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(assessment.router, prefix="/assessment", tags=["assessment"])
api_router.include_router(user.router, prefix="/user", tags=["user"])
api_router.include_router(question.router, prefix="/question", tags=["question"])
api_router.include_router(response.router, prefix="/response", tags=["response"])
api_router.include_router(pdf.router, prefix="/pdf", tags=["pdf"])
api_router.include_router(pdf_upload.router, prefix="/pdf-v2", tags=["pdf-upload"])  # New modern upload API

__all__ = ["api_router"]
