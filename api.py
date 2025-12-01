from fastapi import APIRouter, Depends, HTTPException, Request, Header
import os, hmac, hashlib, json
import httpx
import time
import base64
import jwt as JWT
from jwt import PyJWKClient
from typing import List
import schemas, crud
from database import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from ai_service import ai_service
from auth import admin_required, roles_required
from auth import revoke_jwt
from config import settings
from metrics import RAG_SEARCH_TOTAL, RAG_FALLBACK_TOTAL, ADMIN_ACTIONS_TOTAL
import models
from rag_service import RAGService
from config import settings

router = APIRouter(prefix="/api/v1")
# OIDC login: validate id_token, link/create user by sub
@router.post("/auth/oidc/login", response_model=schemas.UserOut, tags=["integrations", "auth"])
async def oidc_login(id_token: str, db: AsyncSession = Depends(get_session)):
    # validate id_token using existing validator
    try:
        jwks_url = os.getenv('OIDC_JWKS_URL')
        audience = os.getenv('OIDC_AUDIENCE')
        issuer = os.getenv('OIDC_ISSUER')
        if jwks_url:
            jwk_client = PyJWKClient(jwks_url)
            signing_key = jwk_client.get_signing_key_from_jwt(id_token).key
            claims = JWT.decode(id_token, signing_key, algorithms=["RS256"], audience=audience, issuer=issuer)
        else:
            claims = jwt.decode(id_token, options={"verify_signature": False, "verify_exp": True, "verify_aud": False, "verify_iss": False})
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid id_token")

    sub = str(claims.get('sub') or '')
    if not sub:
        raise HTTPException(status_code=400, detail="Missing sub in token")
    # find-or-create user by external_id=sub
    user = await crud.get_user_by_external_id(db, sub)
    if not user:
        name = claims.get('name') or claims.get('preferred_username') or 'User'
        email = claims.get('email')
        user_in = schemas.UserCreate(external_id=sub, name=name, email=email)
        user = await crud.create_user(db, user_in)
    return user


@router.post("/users", response_model=schemas.UserOut, tags=["users"])
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_session)):
    return await crud.create_user(db, user)


@router.post("/auth/jwt/issue", tags=["auth"])
async def auth_jwt_issue(user_id: int | None = None, email: str | None = None, db: AsyncSession = Depends(get_session)):
    # Ищем пользователя по id или email (приоритет id)
    u = None
    if user_id:
        u = await crud.get_user(db, user_id)
    elif email:
        from sqlalchemy.future import select
        res = await db.execute(select(models.User).where(models.User.email == email))
        u = res.scalars().first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    from auth import issue_jwt
    token = issue_jwt(u)
    return {"access_token": token, "token_type": "bearer", "role": u.role}

@router.post("/auth/jwt/revoke", tags=["auth"])
async def auth_jwt_revoke(token: str):
    ok = revoke_jwt(token)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid or already revoked token")
    return {"revoked": True}


@router.get("/users/{user_id}", response_model=schemas.UserOut, tags=["users"])
async def read_user(user_id: int, db: AsyncSession = Depends(get_session)):
    u = await crud.get_user(db, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return u


@router.post("/objects", response_model=schemas.ObjectOut, tags=["objects"])
async def create_object(obj: schemas.ObjectCreate, db: AsyncSession = Depends(get_session)):
    return await crud.create_object(db, obj)


@router.get("/objects", response_model=List[schemas.ObjectOut], tags=["objects"])
async def get_objects(db: AsyncSession = Depends(get_session)):
    return await crud.list_objects(db)


@router.post("/bookings", response_model=schemas.BookingOut, tags=["bookings"])
async def create_booking(booking: schemas.BookingCreate, db: AsyncSession = Depends(get_session)):
    # Автогенерация payment_order_id если отсутствует
    if not booking.payment_order_id:
        import uuid, datetime
        booking.payment_order_id = f"PO-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    return await crud.create_booking(db, booking)


@router.get("/bookings", response_model=List[schemas.BookingOut], tags=["bookings"])
async def list_bookings(user_id: int, db: AsyncSession = Depends(get_session)):
    return await crud.list_bookings_by_user(db, user_id)


@router.post("/reviews", response_model=schemas.ReviewOut, tags=["reviews"])
async def create_review(review: schemas.ReviewCreate, db: AsyncSession = Depends(get_session)):
    return await crud.create_review(db, review)


# --- Интеграции: eGov / Платежи / Freedom Travel (заглушки) ---

@router.post("/auth/oidc/verify", tags=["integrations"])
async def oidc_verify(code: str):
    # Если заданы ENV — выполняем реальный обмен; иначе — заглушка
    token_url = os.getenv("OIDC_TOKEN_URL")
    client_id = os.getenv("OIDC_CLIENT_ID")
    client_secret = os.getenv("OIDC_CLIENT_SECRET")
    redirect_uri = os.getenv("OIDC_REDIRECT_URI")
    if token_url and client_id and client_secret and redirect_uri:
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.post(token_url, data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                })
                if resp.status_code != 200:
                    raise HTTPException(status_code=401, detail="Token exchange failed")
                data = resp.json()
                # Возвращаем базовую часть токенов
                return {
                    "access_token": data.get("access_token"),
                    "id_token": data.get("id_token"),
                    "token_type": data.get("token_type"),
                    "expires_in": data.get("expires_in"),
                }
            except Exception:
                raise HTTPException(status_code=401, detail="Token exchange error")
    # Заглушка
    if code in {"test", "mock"}:
        return {"sub": "egov:user:123", "name": "Test User", "acr": "low"}
    raise HTTPException(status_code=401, detail="Invalid authorization code")

# Валидация id_token (упрощённо без проверки подписи): проверка exp/iss/aud
@router.post("/auth/oidc/validate", tags=["integrations"])
async def oidc_validate(id_token: str):
    jwks_url = os.getenv('OIDC_JWKS_URL')
    audience = os.getenv('OIDC_AUDIENCE')
    issuer = os.getenv('OIDC_ISSUER')
    options = {"verify_signature": bool(jwks_url), "verify_exp": True, "verify_aud": bool(audience), "verify_iss": bool(issuer)}
    try:
        if jwks_url:
            jwk_client = PyJWKClient(jwks_url)
            signing_key = jwk_client.get_signing_key_from_jwt(id_token).key
            claims = JWT.decode(id_token, signing_key, algorithms=["RS256"], audience=audience, issuer=issuer, options=options)
        else:
            # Без подписи: только базовые проверки
            claims = jwt.decode(id_token, options={"verify_signature": False, "verify_exp": True, "verify_aud": False, "verify_iss": False})
        return {"valid": True, "claims": claims}
    except JWT.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWT.InvalidAudienceError:
        raise HTTPException(status_code=401, detail="Invalid audience")
    except JWT.InvalidIssuerError:
        raise HTTPException(status_code=401, detail="Invalid issuer")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id_token")

# Реалистичный OIDC callback с проверкой обязательного заголовка подписи (заглушка)
@router.post("/integrations/egov/oidc/callback", tags=["integrations"])
async def egov_oidc_callback(code: str, state: str | None = None, x_egov_sig: str | None = Header(default=None)):
    if not x_egov_sig:
        raise HTTPException(status_code=400, detail="Missing signature header")
    # Проверка HMAC подписи (заглушка): x-egov-sig = HMAC-SHA256(secret, code|state)
    secret = os.getenv("EGOV_SIG_SECRET", "")
    if secret:
        msg = (code or "") + "|" + (state or "")
        dig = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(dig, x_egov_sig):
            raise HTTPException(status_code=401, detail="Invalid signature")
    # TODO: обмен кода на токен, проверка JWT
    return {"status": "ok", "sub": "egov:user:mock", "code": code, "state": state}


@router.post("/payments/webhook", tags=["integrations"])
async def payments_webhook(request: Request, x_pay_sig: str | None = Header(default=None), db: AsyncSession = Depends(get_session)):
    # Принимаем webhooks от eGov Pay / Kaspi QR (заглушка валидации подписи)
    payload = await request.body()
    if not x_pay_sig:
        raise HTTPException(status_code=400, detail="Missing payment signature")
    # Проверка HMAC подписи: x-pay-sig = HMAC-SHA256(secret, raw_body)
    secret = os.getenv("PAY_SIG_SECRET", "")
    if secret:
        dig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(dig, x_pay_sig):
            raise HTTPException(status_code=401, detail="Invalid signature")
    data = json.loads(payload.decode())
    order_id = data.get("order_id")
    status = data.get("status", "paid")
    # Привязываем к бронированию: искать по payment_order_id
    if order_id:
        from sqlalchemy.future import select
        from models import Booking
        res = await db.execute(select(Booking).where(Booking.payment_order_id == str(order_id)))
        b = res.scalars().first()
        if b:
            await crud.update_booking_status(db, b.id, status)
    return {"received": True, "ok": True}


@router.get("/freedom/mock/tours", tags=["integrations"])
async def freedom_mock_tours():
    # Демонстрационный список туров как заглушка интеграции Freedom Travel
    return [
        {"id": "FT-001", "title": "Burabay Weekend", "price": 35000, "currency": "KZT"},
        {"id": "FT-002", "title": "Kokshetau City Tour", "price": 15000, "currency": "KZT"},
    ]


# --- AI assistant ---

@router.post("/ai/chat", response_model=schemas.AIResponse, tags=["ai"])
async def ai_chat(req: schemas.AIRequest):
    reply = ai_service.chat(req.prompt, req.lang)
    return {"reply": reply}


# --- RAG: документы и поиск ---

@router.post("/rag/documents", tags=["ai", "rag"])
async def rag_add_document(body: schemas.RAGDocumentIn, db: AsyncSession = Depends(get_session), _perm: bool = Depends(roles_required({"admin","content-manager"}))):
    # Лимит размера
    if len(body.text) > settings.MAX_RAG_DOC_CHARS:
        raise HTTPException(status_code=400, detail="Document too large")
    service = RAGService()
    doc = await service.ingest(title=body.title, text=body.text, lang=body.lang, tags=body.tags, session=db if service.backend=='pgvector' else None)
    return {"ok": True, "id": doc["id"], "title": doc["title"]}


@router.get("/rag/search", tags=["ai", "rag"])
async def rag_search(q: str, k: int = 3, mode: str | None = None, db: AsyncSession = Depends(get_session)):
    service = RAGService(mode=mode)
    fallback_used = False
    if service.backend == 'pgvector':
        try:
            results = await service.search(q, k=k, session=db)
        except Exception:
            # Fallback на файловый если ошибка
            fallback_used = True
            fs = RAGService(store=None, mode=mode)
            results = fs.store.search(q, k=k)
    else:
        # Файловый backend
        results = service.store.search(q, k=k)
        if service.store.mode == 'embeddings' and not service.store._embeddings_enabled:
            fallback_used = True
    if RAG_SEARCH_TOTAL:
        RAG_SEARCH_TOTAL.inc()
        if fallback_used and RAG_FALLBACK_TOTAL:
            RAG_FALLBACK_TOTAL.inc()
    return {"query": q, "mode": service.store.mode, "results": results}


@router.post("/rag/documents/batch", tags=["ai", "rag"])
async def rag_add_documents_batch(body: schemas.RAGDocumentsBatch, db: AsyncSession = Depends(get_session), _perm: bool = Depends(roles_required({"admin","content-manager"}))):
    for item in body.items:
        if len(item.text) > settings.MAX_RAG_DOC_CHARS:
            raise HTTPException(status_code=400, detail=f"Document too large: {item.title}")
    service = RAGService()
    res = await service.ingest_batch([item.dict() for item in body.items], session=db if service.backend=='pgvector' else None)
    return res


@router.post("/rag/index/objects", tags=["ai", "rag"])
async def rag_index_objects(db: AsyncSession = Depends(get_session)):
    # Индексация каталога объектов как RAG документов
    objs = await crud.list_objects(db)
    service = RAGService()
    items = []
    for o in objs:
        items.append({
            "title": getattr(o, "name", "Object"),
            "text": getattr(o, "description", ""),
            "lang": None,
            "tags": ["object"],
        })
    res = await service.ingest_batch(items, session=db if service.backend=='pgvector' else None)
    return {"count": len(items), **res}


# --- Complaints & Events ---

@router.post("/complaints", response_model=schemas.ComplaintOut, tags=["complaints"])
async def create_complaint(comp: schemas.ComplaintCreate, db: AsyncSession = Depends(get_session)):
    return await crud.create_complaint(db, comp)


@router.get("/complaints", response_model=List[schemas.ComplaintOut], tags=["complaints"])
async def get_complaints(db: AsyncSession = Depends(get_session)):
    return await crud.list_complaints(db)


@router.post("/complaints/{complaint_id}/status", response_model=schemas.ComplaintOut, tags=["complaints", "admin"])
async def update_complaint_status(
    complaint_id: int,
    body: schemas.ComplaintStatusUpdate,
    db: AsyncSession = Depends(get_session),
    _perm: bool = Depends(roles_required({"admin","moderator"})),
):
    c = await crud.set_complaint_status(db, complaint_id, body.status)
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if ADMIN_ACTIONS_TOTAL:
        ADMIN_ACTIONS_TOTAL.inc()
    return c


@router.post("/events", response_model=schemas.EventOut, tags=["events"])
async def create_event(event: schemas.EventCreate, db: AsyncSession = Depends(get_session)):
    return await crud.create_event(db, event)


@router.get("/events", response_model=List[schemas.EventOut], tags=["events"])
async def get_events(db: AsyncSession = Depends(get_session)):
    return await crud.list_events(db)

# --- Admin endpoints ---

@router.get("/admin/complaints", response_model=List[schemas.ComplaintOut], tags=["admin"])
async def admin_list_complaints(status: str | None = None, db: AsyncSession = Depends(get_session), _admin_ok: bool = Depends(admin_required)):
    items = await crud.list_complaints(db)
    if status:
        items = [c for c in items if getattr(c, 'status', None) == status]
    return items

@router.get("/admin/events", response_model=List[schemas.EventOut], tags=["admin"])
async def admin_list_events(db: AsyncSession = Depends(get_session), _admin_ok: bool = Depends(admin_required)):
    return await crud.list_events(db)

@router.post("/admin/bookings/{booking_id}/status", tags=["admin"])
async def admin_update_booking_status(booking_id: int, body: schemas.BookingStatusUpdate, db: AsyncSession = Depends(get_session), _perm: bool = Depends(roles_required({"admin","moderator"}))):
    b = await crud.update_booking_status(db, booking_id, body.status)
    if not b:
        raise HTTPException(status_code=404, detail="Booking not found")
    if ADMIN_ACTIONS_TOTAL:
        ADMIN_ACTIONS_TOTAL.inc()
    return {"ok": True, "id": b.id, "status": b.status}

@router.get("/admin/bookings", response_model=List[schemas.BookingOut], tags=["admin"])
async def admin_list_bookings(status: str | None = None, db: AsyncSession = Depends(get_session), _admin_ok: bool = Depends(admin_required)):
    items = await crud.list_all_bookings(db)
    if status:
        items = [b for b in items if getattr(b, 'status', None) == status]
    return items


# --- Object scoring (simplified) ---

@router.get("/objects/{object_id}/score", tags=["objects"])
async def object_score(object_id: int, db: AsyncSession = Depends(get_session)):
    # Простая версия: учитываем кол-во жалоб и средний рейтинг
    from sqlalchemy import func
    from models import Review, Complaint

    # avg rating
    res_r = await db.execute(
        func.coalesce(func.avg(Review.rating), 0.0).where(Review.object_id == object_id)
    )
    avg_rating = float(res_r.scalar() or 0.0)

    # complaints count
    res_c = await db.execute(
        func.count(Complaint.id).where(Complaint.object_id == object_id)
    )
    complaints = int(res_c.scalar() or 0)

    # простая формула [0..100]
    base = avg_rating / 5 * 100
    penalty = min(complaints * 3, 30)
    score = max(0, int(base - penalty))
    return {"object_id": object_id, "avg_rating": avg_rating, "complaints": complaints, "score": score}


# --- Metrics ingest (stub) ---

@router.post("/metrics/ingest", tags=["integrations"])
async def metrics_ingest(payload: dict):
    # Заглушка для сбора метрик. В дальнейшем — запись в хранилище и агрегации.
    return {"ok": True, "received": True}
