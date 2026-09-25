from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
import jwt
from pydantic import ValidationError
import pytest
from sqlalchemy import event, select

from app.config import Settings
from app.models import AuditLog, Request, RequestStatus
from app.services import requests, sla
from test_requests import actors, headers, submit, decide, PAYLOAD


def test_idor_rejects_all_request_id_endpoints_without_side_effects(client, actors, db):
    request = submit(client, actors).json()
    path = f'/requests/{request["id"]}'
    before = db.scalars(select(AuditLog.id)).all()
    for role in ('OTHER', 'OTHER_MANAGER'):
        auth = headers(actors[role])
        for method, endpoint, payload in [('GET',path,None),('GET',path+'/audit',None),('PATCH',path+'/cancel',None),
            ('POST',path+'/manager-approval',{'decision':'APPROVE'}),('POST',path+'/finance-approval',{'decision':'APPROVE'}),
            ('POST',path+'/start-processing',{}),('POST',path+'/complete',{})]:
            assert client.request(method, endpoint, headers=auth, **({'json':payload} if payload is not None else {})).status_code == 404
    assert db.get(Request, request['id']).status == RequestStatus.PENDING_MANAGER_APPROVAL
    assert db.scalars(select(AuditLog.id)).all() == before


def test_cross_role_decisions_are_denied_at_visible_stages(client, actors):
    request = submit(client, actors, estimated_cost='10000000').json()
    decide(client, actors, request['id'])
    assert decide(client, actors, request['id'], 'FINANCE', 'manager').status_code == 403
    decide(client, actors, request['id'], 'FINANCE', 'finance')
    for stage in ('manager','finance'):
        assert decide(client, actors, request['id'], 'PROCUREMENT', stage).status_code == 403
        assert decide(client, actors, request['id'], 'ADMIN', stage).status_code == 403


def test_payload_limits_and_malformed_identifiers(client, actors):
    auth = headers(actors['EMPLOYEE'])
    for override in ({'title':''},{'description':'x'*10001},{'business_justification':'x'*5001},
                     {'estimated_cost':'10000000000000'},{'estimated_cost':True}, {'estimated_cost':'Infinity'}):
        assert client.post('/requests',headers=auth,json={**PAYLOAD,**override}).status_code == 422
    assert client.post('/requests',headers=auth,json={}).status_code == 422
    for identifier in ('abc','0','-1','2147483648','1.5'):
        assert client.get('/requests/'+identifier,headers=auth).status_code == 422
        assert client.get('/requests/'+identifier+'/audit',headers=auth).status_code == 422
    for query in ('limit=0','limit=101','offset=-1'):
        assert client.get('/requests?'+query,headers=auth).status_code == 422


def test_zero_and_fractional_money_skip_finance(client, actors):
    for cost in ('0','0.01','4999999.99'):
        request = submit(client,actors,estimated_cost=cost).json()
        result = decide(client,actors,request['id']).json()
        assert result['status'] == 'APPROVED' and len(result['approvals']) == 1
        assert not result['finance_required']


def test_just_inside_due_soon_boundary():
    now=datetime(2026,9,25,tzinfo=timezone.utc)
    assert sla.calculate(RequestStatus.APPROVED,now+timedelta(hours=24)-timedelta(microseconds=1),now=now) == 'DUE_SOON'


def test_response_headers_validation_redaction_and_safe_server_error(client, actors, monkeypatch):
    for path in ('/requests','/analytics/summary'):
        response=client.get(path,headers=headers(actors['ADMIN']))
        assert response.headers['cache-control']=='no-store'
        assert response.headers['x-content-type-options']=='nosniff'
    secret='do-not-echo-this-password'
    response=client.post('/auth/login',json={'email':'invalid','password':secret,'unexpected':secret})
    assert response.status_code == 422
    assert secret not in response.text and 'input' not in response.json()['detail'][0]
    def fail(*args,**kwargs):
        raise RuntimeError('internal-db-host-secret')
    monkeypatch.setattr(requests,'list_requests',fail)
    with TestClient(client.app,raise_server_exceptions=False) as safe_client:
        response=safe_client.get('/requests',headers=headers(actors['EMPLOYEE']))
    assert response.status_code==500
    assert response.json()=={'detail':'The service could not complete your request. Please try again.'}
    assert 'internal-db-host-secret' not in response.text
    assert response.headers['cache-control']=='no-store'


def test_cors_and_secret_configuration(client):
    for origin in ('*','https://*.example.com','https://example.com/path','https://user:password@example.com','null'):
        with pytest.raises(ValidationError):
            Settings(cors_origins=[origin])
    settings=Settings(cors_origins=['https://requestflow.example','https://requestflow.example'])
    assert settings.cors_origins==['https://requestflow.example']
    for secret in ('short','replace-'+'x'*40):
        with pytest.raises(ValidationError):
            Settings(jwt_secret=secret)
    response=client.options('/requests',headers={'Origin':'https://attacker.example','Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'authorization,content-type'})
    assert response.status_code==400 and 'access-control-allow-origin' not in response.headers


def test_deployment_database_and_cors_aliases(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'postgresql://demo:secret@database.internal:5432/requestflow')
    monkeypatch.setenv('CORS_ALLOWED_ORIGINS', '["https://requestflow.example"]')
    settings = Settings(postgres_password='unused', jwt_secret='x' * 32, environment='production')
    url = settings.sqlalchemy_url()
    assert url.drivername == 'postgresql+psycopg'
    assert url.host == 'database.internal'
    assert settings.cors_origins == ['https://requestflow.example']
    assert settings.environment == 'production'


def test_auth_rejects_wrong_audience_issuer_and_future_tokens(client, actors):
    now=datetime.now(timezone.utc)
    claims={'sub':str(actors['EMPLOYEE'].id),'iat':now,'exp':now+timedelta(hours=1),'iss':'requestflow-api','aud':'requestflow-web'}
    for override in ({'aud':'another-app'},{'iss':'another-issuer'},{'iat':now+timedelta(hours=1)},{'sub':'1 OR 1=1'}):
        token=jwt.encode({**claims,**override},Settings().jwt_secret.get_secret_value(),algorithm='HS256')
        assert client.get('/requests',headers={'Authorization':'Bearer '+token}).status_code==401


def test_query_count_does_not_grow_with_request_or_audit_rows(client, actors, db):
    auth=headers(actors['ADMIN'])
    request=submit(client,actors).json()
    @contextmanager
    def queries():
        statements=[]
        def collect(conn,cursor,statement,parameters,context,executemany):
            if statement.lstrip().upper().startswith('SELECT'):
                statements.append(statement)
        connection=db.connection()
        event.listen(connection,'before_cursor_execute',collect)
        try:
            yield statements
        finally:
            event.remove(connection,'before_cursor_execute',collect)
    db.expire_all()
    with queries() as initial:
        assert client.get('/requests',headers=auth).status_code==200
    for i in range(8):
        submit(client,actors,title=f'Query test {i}')
    db.expire_all()
    with queries() as larger:
        response=client.get('/requests',headers=auth)
    assert response.json()['total']==9
    assert len(larger) <= len(initial) and len(larger)<=5
    db.expire_all()
    with queries() as audit_queries:
        assert client.get(f'/requests/{request["id"]}/audit',headers=auth).status_code==200
    assert len(audit_queries)<=4
    db.expire_all()
    with queries() as dashboard_queries:
        assert client.get('/analytics/summary',headers=auth).status_code==200
    assert len(dashboard_queries)<=2
