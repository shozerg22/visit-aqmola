import os
import hmac, hashlib, json
import jwt
from fastapi.testclient import TestClient
from app import app


client = TestClient(app)


def make_id_token(sub="user-oidc-1", name="Test User", email="user@example.com"):
    # Без подписи: только payload
    payload = {"sub": sub, "name": name, "email": email, "exp": 9999999999}
    token = jwt.encode(payload, None, algorithm=None)  # PyJWT вернет payload как токен без подписи
    # PyJWT>=2 требует алгоритм; fallback: вручную составить JWT
    try:
        return token
    except Exception:
        import base64
        def b64url(d):
            return base64.urlsafe_b64encode(d).rstrip(b"=").decode()
        header = b64url(json.dumps({"alg":"none"}).encode())
        body = b64url(json.dumps(payload).encode())
        return f"{header}.{body}."


def test_oidc_login_creates_or_links_user():
    os.environ["DISABLE_DB_INIT"] = "1"
    # Без JWKS: базовая проверка
    token = make_id_token()
    r = client.post("/api/v1/auth/oidc/login", params={"id_token": token})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["external_id"] == "user-oidc-1"
    assert data["name"] == "Test User"


def test_payments_webhook_updates_booking_status():
    os.environ["DISABLE_DB_INIT"] = "1"
    os.environ["PAY_SIG_SECRET"] = "demo"
    # Создаем бронирование c payment_order_id
    booking_body = {"user_id": 1, "object_id": 1, "payment_order_id": "ORD-xyz", "start_date": None, "end_date": None}
    r = client.post("/api/v1/bookings", json=booking_body)
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["payment_order_id"]

    # Готовим вебхук
    body = json.dumps({"order_id": b["payment_order_id"], "amount": 1000, "currency": "KZT", "status": "paid"}).encode()
    sig = hmac.new(os.environ["PAY_SIG_SECRET"].encode(), body, hashlib.sha256).hexdigest()
    r2 = client.post("/api/v1/payments/webhook", data=body, headers={"x-pay-sig": sig, "Content-Type": "application/json"})
    assert r2.status_code == 200, r2.text
