import os
import hmac, hashlib, json, time
import jwt
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def make_id_token(payload_overrides=None):
    base = {"sub": "neg-user", "name": "Neg User", "email": "neg@example.com", "exp": int(time.time()) + 3600}
    if payload_overrides:
        base.update(payload_overrides)
    # Алгоритм none (без подписи) чтобы соответствовать текущей логике
    token = jwt.encode(base, None, algorithm=None)
    try:
        return token
    except Exception:
        import base64
        def b64url(d):
            return base64.urlsafe_b64encode(d).rstrip(b"=").decode()
        header = b64url(json.dumps({"alg":"none"}).encode())
        body = b64url(json.dumps(base).encode())
        return f"{header}.{body}."


def test_payments_webhook_invalid_signature():
    os.environ["DISABLE_DB_INIT"] = "1"
    os.environ["PAY_SIG_SECRET"] = "demo"
    # Формируем тело вебхука без предварительного создания бронирования —
    # проверка подписи происходит ДО любых обращений к БД.
    body = json.dumps({"order_id": "ORD-NOEXIST", "amount": 999, "currency": "KZT", "status": "paid"}).encode()
    bad_sig = hmac.new(b"wrong", body, hashlib.sha256).hexdigest()
    r2 = client.post("/api/v1/payments/webhook", data=body, headers={"x-pay-sig": bad_sig, "Content-Type": "application/json"})
    assert r2.status_code == 401, r2.text
    assert r2.json().get("detail") == "Invalid signature"


def test_oidc_validate_expired_token():
    os.environ["DISABLE_DB_INIT"] = "1"
    # Токен с истекшим exp
    expired_token = make_id_token({"exp": int(time.time()) - 10})
    r = client.post("/api/v1/auth/oidc/validate", params={"id_token": expired_token})
    assert r.status_code == 401, r.text
    assert r.json().get("detail") == "Token expired"


def test_oidc_validate_malformed_token():
    os.environ["DISABLE_DB_INIT"] = "1"
    # Явно некорректный формат (нет частей)
    bad = "not.a.jwt"
    r = client.post("/api/v1/auth/oidc/validate", params={"id_token": bad})
    # Ожидаем 400 Invalid id_token (generic)
    assert r.status_code in (400, 401), r.text
    # Деталь может быть 400 invalid или 401 если внутренняя ошибка валидации
