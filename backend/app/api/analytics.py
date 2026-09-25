from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, require_roles
from app.models import Role
from app.schemas.analytics import AnalyticsResponse
from app.services.analytics import dashboard

router = APIRouter(tags=["Management analytics"], dependencies=[Depends(require_roles(Role.ADMIN))])


@router.get("/analytics/summary", response_model=AnalyticsResponse)
def summary(db: Annotated[Session, Depends(get_db)]):
    return dashboard(db)
