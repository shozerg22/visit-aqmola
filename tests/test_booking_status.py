import os
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_admin_update_booking_status_validation():
    os.environ["DISABLE_DB_INIT"] = "1"
    os.environ["ADMIN_TOKEN"] = "adm"
    # Невалидный статус — проверка схемы срабатывает до доступа к БД
    r_invalid = client.post("/api/v1/admin/bookings/1/status", json={"status": "WRONG"}, headers={"X-Admin-Token": "adm"})
    assert r_invalid.status_code == 422
