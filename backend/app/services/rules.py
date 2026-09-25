from datetime import datetime, timedelta
from decimal import Decimal

from app.models import Priority

FINANCE_APPROVAL_THRESHOLD = Decimal("5000000.00")
PRIORITY_DAYS = {Priority.HIGH: 1, Priority.MEDIUM: 3, Priority.LOW: 5}


def finance_required(cost: Decimal) -> bool:
    return cost >= FINANCE_APPROVAL_THRESHOLD


def calculate_due_date(created_at: datetime, priority: Priority) -> datetime:
    return created_at + timedelta(days=PRIORITY_DAYS[priority])
