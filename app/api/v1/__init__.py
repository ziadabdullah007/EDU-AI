"""EduCore AI Platform — API v1 Router Registry

Aggregates all module routers into a single v1 router mounted at /api/v1.
"""

from fastapi import APIRouter

from app.api.v1.attendance import router as attendance_router
from app.api.v1.auth import router as auth_router
from app.api.v1.classes import router as classes_router
from app.api.v1.documents import router as documents_router
from app.api.v1.enrollments import router as enrollments_router
from app.api.v1.grades import router as grades_router
from app.api.v1.payments import router as payments_router
from app.api.v1.schools import router as schools_router
from app.api.v1.students import router as students_router
from app.api.v1.teachers import router as teachers_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(schools_router)
api_router.include_router(students_router)
api_router.include_router(teachers_router)
api_router.include_router(classes_router)
api_router.include_router(enrollments_router)
api_router.include_router(attendance_router)
api_router.include_router(grades_router)
api_router.include_router(payments_router)
api_router.include_router(documents_router)
