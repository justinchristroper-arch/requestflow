from datetime import datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import func, select

from app.models import AuditLog, Category, Priority, Request, RequestStatus, Role
from app.services import analytics, sla
from app.services.seed_analytics import seed_analytics
from test_requests import actors, headers

NOW = datetime(2026, 9, 25, 12, tzinfo=timezone.utc)


def item(db, actors, *, status='APPROVED', due=None, created=None, completed=None, priority='MEDIUM', category='HARDWARE', number='TEST-SLA'):
    created = created or NOW - timedelta(days=3)
    request = Request(request_number=number, requester_id=actors['EMPLOYEE'].id, category=Category(category),
        title='Synthetic SLA test', description='Fixture', business_justification='Test', estimated_cost=Decimal('100'),
        priority=Priority(priority), status=RequestStatus(status), created_at=created, updated_at=created,
        due_date=due or NOW + timedelta(days=2), completed_at=completed)
    if status in ('PROCESSING', 'COMPLETED'):
        request.processing_owner_id = actors['PROCUREMENT'].id
        request.processing_started_at = created + timedelta(hours=1)
    db.add(request)
    db.flush()
    return request


@pytest.mark.parametrize('status,remaining,completion,expected', [
    ('APPROVED', 90000, None, 'ON_TRACK'),
    ('PENDING_MANAGER_APPROVAL', 3600, None, 'DUE_SOON'),
    ('PENDING_FINANCE_APPROVAL', -1, None, 'BREACHED'),
    ('PROCESSING', -3600, None, 'BREACHED'),
    ('APPROVED', 86400.000001, None, 'ON_TRACK'),
    ('APPROVED', 86400, None, 'DUE_SOON'),
    ('APPROVED', 0, None, 'DUE_SOON'),
    ('APPROVED', -0.000001, None, 'BREACHED'),
    ('COMPLETED', 0, -1, 'COMPLETED_ON_TIME'),
    ('COMPLETED', 0, 0, 'COMPLETED_ON_TIME'),
    ('COMPLETED', 0, 0.000001, 'COMPLETED_LATE'),
    ('CANCELLED', -86400, None, 'NOT_APPLICABLE'),
    ('REJECTED', -86400, None, 'NOT_APPLICABLE'),
    ('DRAFT', -86400, None, 'NOT_APPLICABLE'),
])
def test_frozen_sla_boundaries_match_sql(db, actors, status, remaining, completion, expected):
    due = NOW + timedelta(seconds=remaining)
    completed = due + timedelta(seconds=completion) if completion is not None else None
    request = item(db, actors, status=status, due=due, completed=completed)
    assert sla.calculate(request.status, due, completed, now=NOW) == expected
    assert db.scalar(select(sla.sql_status(NOW)).where(Request.id == request.id)) == expected
    jakarta = ZoneInfo('Asia/Jakarta')
    assert sla.calculate(request.status, due.astimezone(jakarta), completed.astimezone(jakarta) if completed else None, now=NOW.astimezone(jakarta)) == expected


def test_sla_rejects_naive_time_and_missing_completion():
    with pytest.raises(ValueError, match='timezone-aware'):
        sla.calculate(RequestStatus.APPROVED, NOW.replace(tzinfo=None), now=NOW)
    with pytest.raises(ValueError, match='completed_at'):
        sla.calculate(RequestStatus.COMPLETED, NOW, now=NOW)


def test_dashboard_zero_data(client, actors, monkeypatch):
    monkeypatch.setattr(sla, 'utc_now', lambda: NOW)
    response = client.get('/analytics/summary', headers=headers(actors['ADMIN']))
    assert response.status_code == 200
    data = response.json()
    assert data['kpis'] == dict(total_requests=0, pending_approval=0, processing=0, completed=0, rejected=0,
        completed_on_time=0, sla_compliance_percent=None, average_resolution_hours=None)
    assert len(data['monthly_trend']) == 6
    assert [x['key'] for x in data['monthly_trend']] == ['2026-04','2026-05','2026-06','2026-07','2026-08','2026-09']
    assert all(x['count'] == 0 for field in ('by_category','by_priority','by_status','by_sla','monthly_trend') for x in data[field])


@pytest.mark.parametrize('role', ['EMPLOYEE','MANAGER','FINANCE','PROCUREMENT'])
def test_analytics_denies_non_admin(client, actors, role):
    assert client.get('/analytics/summary', headers=headers(actors[role])).status_code == 403


def test_analytics_denies_unauthenticated_and_inactive(client, actors, db):
    assert client.get('/analytics/summary').status_code == 401
    actors['ADMIN'].is_active = False
    db.commit()
    assert client.get('/analytics/summary', headers=headers(actors['ADMIN'])).status_code == 401


def test_analytics_known_counts_compliance_resolution_and_groupings(client, actors, db, monkeypatch):
    monkeypatch.setattr(sla, 'utc_now', lambda: NOW)
    # Two completed: 24 and 48 hours, one on time, one late.
    item(db, actors, number='A', status='COMPLETED', created=NOW-timedelta(hours=72), completed=NOW-timedelta(hours=48), due=NOW-timedelta(hours=48), priority='HIGH')
    item(db, actors, number='B', status='COMPLETED', created=NOW-timedelta(hours=72), completed=NOW-timedelta(hours=24), due=NOW-timedelta(hours=30), category='SOFTWARE', priority='LOW')
    item(db, actors, number='C', status='PENDING_MANAGER_APPROVAL', due=NOW+timedelta(hours=12))
    item(db, actors, number='D', status='PENDING_FINANCE_APPROVAL', due=NOW-timedelta(hours=1))
    item(db, actors, number='E', status='PROCESSING', due=NOW+timedelta(days=2), category='ACCESS')
    item(db, actors, number='F', status='REJECTED')
    item(db, actors, number='G', status='CANCELLED')
    data = client.get('/analytics/summary', headers=headers(actors['ADMIN'])).json()
    assert data['kpis'] == dict(total_requests=7,pending_approval=2,processing=1,completed=2,rejected=1,
        completed_on_time=1,sla_compliance_percent=50.0,average_resolution_hours=36.0)
    assert {x['key']:x['count'] for x in data['by_category']} == dict(HARDWARE=5,SOFTWARE=1,ACCESS=1,REPAIR_MAINTENANCE=0,OTHER=0)
    assert {x['key']:x['count'] for x in data['by_priority']} == dict(LOW=1,MEDIUM=5,HIGH=1)
    assert {x['key']:x['count'] for x in data['by_sla']} == dict(ON_TRACK=1,DUE_SOON=1,BREACHED=1,COMPLETED_ON_TIME=1,COMPLETED_LATE=1,NOT_APPLICABLE=2)
    assert data['monthly_trend'][-1] == {'key':'2026-09','count':7}
    assert sum(x['count'] for x in data['by_status']) == 7


def test_month_grouping_uses_jakarta_and_zero_fills_across_year(db, actors):
    item(db, actors, number='JAN', created=datetime(2025,12,31,18,tzinfo=timezone.utc))  # Jan 1 Jakarta
    item(db, actors, number='DEC', created=datetime(2025,12,31,16,tzinfo=timezone.utc))
    item(db, actors, number='OLD', created=datetime(2025,1,1,tzinfo=timezone.utc))
    data = analytics.dashboard(db, now=datetime(2026,1,15,tzinfo=timezone.utc))
    assert data['kpis']['total_requests'] == 3
    assert data['monthly_trend'] == [dict(key=key,count=count) for key,count in [('2025-08',0),('2025-09',0),('2025-10',0),('2025-11',0),('2025-12',1),('2026-01',1)]]


def test_queue_urgency_precedes_priority_and_api_sla(client, actors, db, monkeypatch):
    monkeypatch.setattr(sla, 'utc_now', lambda: NOW)
    ontrack = item(db, actors, number='TRACK', priority='HIGH', due=NOW+timedelta(days=2))
    soon = item(db, actors, number='SOON', priority='LOW', due=NOW+timedelta(hours=24))
    breached = item(db, actors, number='BREACH', priority='LOW', due=NOW-timedelta(seconds=1))
    data = client.get('/procurement/queue', headers=headers(actors['PROCUREMENT'])).json()
    assert [x['id'] for x in data['items']] == [breached.id,soon.id,ontrack.id]
    assert [x['sla_status'] for x in data['items']] == ['BREACHED','DUE_SOON','ON_TRACK']
    detail = client.get(f'/requests/{soon.id}', headers=headers(actors['EMPLOYEE'])).json()
    assert detail['sla_status'] == 'DUE_SOON'
    monkeypatch.setattr(sla, 'utc_now', lambda: NOW + timedelta(days=2))
    assert client.get(f'/requests/{soon.id}', headers=headers(actors['EMPLOYEE'])).json()['sla_status'] == 'BREACHED'
    assert db.get(Request, soon.id).status == RequestStatus.APPROVED


def test_seed_is_additive_idempotent_and_auditable(db, actors):
    original = item(db, actors, number='USER-DATA')
    assert seed_analytics(db, as_of=NOW) == 30
    first = analytics.dashboard(db, now=NOW)
    audits = db.scalar(select(func.count()).select_from(AuditLog))
    assert seed_analytics(db, as_of=NOW+timedelta(days=30)) == 0
    assert analytics.dashboard(db, now=NOW) == first
    assert db.scalar(select(func.count()).select_from(AuditLog)) == audits
    assert db.get(Request, original.id).title == 'Synthetic SLA test'
    assert first['kpis']['total_requests'] == 31
    assert first['kpis']['completed'] == 12
    assert first['kpis']['sla_compliance_percent'] == 50
    assert first['kpis']['pending_approval'] == 6
    assert first['kpis']['processing'] == 3
    assert all(x['count'] > 0 for x in first['by_category'])
    assert all(x['count'] > 0 for x in first['by_sla'])
    for request in db.scalars(select(Request).where(Request.id != original.id)):
        history = db.scalars(select(AuditLog).where(AuditLog.request_id==request.id).order_by(AuditLog.created_at,AuditLog.id)).all()
        assert history[0].created_at == request.created_at
        assert history[-1].new_status == request.status or history[-1].action.value == 'FINANCE_APPROVAL_REQUIRED'
        for approval in request.approvals:
            assert approval.decided_at is None or approval.created_at <= approval.decided_at
