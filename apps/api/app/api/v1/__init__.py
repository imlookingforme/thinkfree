from fastapi import APIRouter

from app.api.v1.ai_settings import router as ai_settings_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.auth import router as auth_router
from app.api.v1.collaboration import router as collaboration_router
from app.api.v1.health import router as health_router
from app.api.v1.institutional import router as institutional_router
from app.api.v1.planner import router as planner_router
from app.api.v1.problems import router as problems_router
from app.api.v1.sessions import router as sessions_router
from app.api.v1.validations import router as validations_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health_router, prefix="/health", tags=["Health"])
api_v1_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_v1_router.include_router(problems_router, prefix="/problems", tags=["Problems"])
api_v1_router.include_router(sessions_router, prefix="/sessions", tags=["Sessions"])
api_v1_router.include_router(validations_router, prefix="/validations", tags=["Validations"])
api_v1_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
api_v1_router.include_router(planner_router, prefix="/planner", tags=["Planner & Fairness"])
api_v1_router.include_router(institutional_router, prefix="/institutional", tags=["Institutional & Badges"])
api_v1_router.include_router(collaboration_router, prefix="/collab", tags=["Projects & Privacy"])
api_v1_router.include_router(ai_settings_router, prefix="/ai", tags=["AI Settings & Model Switching"])
