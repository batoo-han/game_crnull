"""
Тесты для админ-API.

Проверяем:
- Логин/логаут
- Проверку секрета маршрута
- CORS preflight
- Работу с настройками
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import AdminUser
from app.db.session import SessionLocal
from app.main import create_app
from app.core.security import hash_password


@pytest.fixture
def client():
    """Создаём тестовый клиент FastAPI."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def db():
    """Создаём тестовую сессию БД."""
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


@pytest.fixture
def admin_user(db: Session):
    """Создаём тестового администратора."""
    # Удаляем существующего, если есть
    existing = db.query(AdminUser).filter(AdminUser.username == "testadmin").first()
    if existing:
        db.delete(existing)
        db.commit()
    
    admin = AdminUser(
        username="testadmin",
        password_hash=hash_password("testpass123"),
        disabled=False,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    yield admin
    # Очистка после теста
    db.delete(admin)
    db.commit()


def test_admin_login_success(client: TestClient, admin_user: AdminUser):
    """Тест успешного логина администратора."""
    # Устанавливаем секрет маршрута для теста
    original_secret = settings.admin_route_secret
    settings.admin_route_secret = "sadmin"
    
    try:
        response = client.post(
            "/api/admin/login",
            json={"username": "testadmin", "password": "testpass123"},
            headers={"X-Admin-Route-Secret": "sadmin"},
        )
        
        assert response.status_code == 200
        assert response.json() == {"ok": "true"}
        # Проверяем, что cookie установлена
        assert "admin_token" in response.cookies
    finally:
        settings.admin_route_secret = original_secret


def test_admin_login_wrong_password(client: TestClient, admin_user: AdminUser):
    """Тест логина с неправильным паролем."""
    original_secret = settings.admin_route_secret
    settings.admin_route_secret = "sadmin"
    
    try:
        response = client.post(
            "/api/admin/login",
            json={"username": "testadmin", "password": "wrongpass"},
            headers={"X-Admin-Route-Secret": "sadmin"},
        )
        
        assert response.status_code == 401
        assert "Неверный логин или пароль" in response.json()["detail"]
    finally:
        settings.admin_route_secret = original_secret


def test_admin_login_wrong_username(client: TestClient, admin_user: AdminUser):
    """Тест логина с неправильным именем пользователя."""
    original_secret = settings.admin_route_secret
    settings.admin_route_secret = "sadmin"
    
    try:
        response = client.post(
            "/api/admin/login",
            json={"username": "wronguser", "password": "testpass123"},
            headers={"X-Admin-Route-Secret": "sadmin"},
        )
        
        assert response.status_code == 401
        assert "Неверный логин или пароль" in response.json()["detail"]
    finally:
        settings.admin_route_secret = original_secret


def test_admin_route_secret_required(client: TestClient):
    """Тест проверки секрета маршрута."""
    original_secret = settings.admin_route_secret
    settings.admin_route_secret = "sadmin"
    
    try:
        # Запрос без секрета
        response = client.post(
            "/api/admin/login",
            json={"username": "testadmin", "password": "testpass123"},
        )
        
        assert response.status_code == 404
        assert "Не найдено" in response.json()["detail"]
    finally:
        settings.admin_route_secret = original_secret


def test_admin_route_secret_wrong(client: TestClient):
    """Тест проверки неправильного секрета маршрута."""
    original_secret = settings.admin_route_secret
    settings.admin_route_secret = "sadmin"
    
    try:
        # Запрос с неправильным секретом
        response = client.post(
            "/api/admin/login",
            json={"username": "testadmin", "password": "testpass123"},
            headers={"X-Admin-Route-Secret": "wrongsecret"},
        )
        
        assert response.status_code == 404
        assert "Не найдено" in response.json()["detail"]
    finally:
        settings.admin_route_secret = original_secret


def test_admin_cors_preflight(client: TestClient):
    """Тест CORS preflight (OPTIONS запрос)."""
    original_secret = settings.admin_route_secret
    settings.admin_route_secret = "sadmin"
    
    try:
        # OPTIONS запрос должен проходить без секрета (для CORS)
        response = client.options(
            "/api/admin/login",
            headers={
                "Origin": "http://localhost:5174",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        
        assert response.status_code == 200
        # Проверяем CORS заголовки
        assert "access-control-allow-origin" in response.headers
    finally:
        settings.admin_route_secret = original_secret


def test_admin_me_unauthorized(client: TestClient):
    """Тест получения информации о себе без авторизации."""
    original_secret = settings.admin_route_secret
    settings.admin_route_secret = "sadmin"
    
    try:
        response = client.get(
            "/api/admin/me",
            headers={"X-Admin-Route-Secret": "sadmin"},
        )
        
        assert response.status_code == 401
    finally:
        settings.admin_route_secret = original_secret


def test_admin_me_authorized(client: TestClient, admin_user: AdminUser):
    """Тест получения информации о себе после авторизации."""
    original_secret = settings.admin_route_secret
    settings.admin_route_secret = "sadmin"
    
    try:
        # Сначала логинимся
        login_response = client.post(
            "/api/admin/login",
            json={"username": "testadmin", "password": "testpass123"},
            headers={"X-Admin-Route-Secret": "sadmin"},
        )
        
        assert login_response.status_code == 200
        cookie = login_response.cookies.get("admin_token")
        assert cookie is not None
        
        # Теперь получаем информацию о себе
        me_response = client.get(
            "/api/admin/me",
            headers={"X-Admin-Route-Secret": "sadmin"},
            cookies={"admin_token": cookie},
        )
        
        assert me_response.status_code == 200
        assert me_response.json() == {"username": "testadmin"}
    finally:
        settings.admin_route_secret = original_secret


def test_admin_logout(client: TestClient, admin_user: AdminUser):
    """Тест логаута."""
    original_secret = settings.admin_route_secret
    settings.admin_route_secret = "sadmin"
    
    try:
        # Сначала логинимся
        login_response = client.post(
            "/api/admin/login",
            json={"username": "testadmin", "password": "testpass123"},
            headers={"X-Admin-Route-Secret": "sadmin"},
        )
        
        assert login_response.status_code == 200
        cookie = login_response.cookies.get("admin_token")
        assert cookie is not None
        
        # Логаутимся
        logout_response = client.post(
            "/api/admin/logout",
            headers={"X-Admin-Route-Secret": "sadmin"},
            cookies={"admin_token": cookie},
        )
        
        assert logout_response.status_code == 200
        assert logout_response.json() == {"ok": "true"}
        
        # Проверяем, что cookie удалена (может быть в заголовках Set-Cookie)
        set_cookie_header = logout_response.headers.get("set-cookie", "")
        # Cookie должна быть удалена (max-age=0 или пустое значение)
        assert "admin_token" in set_cookie_header.lower() or "max-age=0" in set_cookie_header.lower()
    finally:
        settings.admin_route_secret = original_secret


def test_admin_login_pydantic_validation(client: TestClient):
    """Тест валидации Pydantic для логина (проверка, что проблема с forward references решена)."""
    import time
    original_secret = settings.admin_route_secret
    settings.admin_route_secret = "sadmin"
    
    try:
        # Ждем, чтобы избежать rate limit (5 запросов в минуту = минимум 12 сек между запросами)
        time.sleep(15)
        
        # Пустой body
        response = client.post(
            "/api/admin/login",
            json={},
            headers={"X-Admin-Route-Secret": "sadmin"},
        )
        
        # Должна быть ошибка валидации, а не 500
        assert response.status_code in (422, 400)  # 422 - validation error
        
        # Ждем, чтобы избежать rate limit
        time.sleep(15)
        
        # Неправильный тип данных
        response = client.post(
            "/api/admin/login",
            json={"username": 123, "password": "test"},
            headers={"X-Admin-Route-Secret": "sadmin"},
        )
        
        # Должна быть ошибка валидации, а не 500
        assert response.status_code in (422, 400)
    finally:
        settings.admin_route_secret = original_secret


def test_admin_login_body_parsing(client: TestClient, admin_user: AdminUser):
    """Тест парсинга body для логина - проверяем, что FastAPI правильно распарсивает JSON."""
    import time
    original_secret = settings.admin_route_secret
    settings.admin_route_secret = "sadmin"
    
    try:
        # Ждем, чтобы избежать rate limit (5 запросов в минуту = минимум 12 сек между запросами)
        time.sleep(15)
        
        # Правильный запрос с JSON body
        response = client.post(
            "/api/admin/login",
            json={"username": "testadmin", "password": "testpass123"},
            headers={"X-Admin-Route-Secret": "sadmin"},
        )
        
        # Должен быть успешный ответ, а не 422
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        assert response.json() == {"ok": "true"}
    finally:
        settings.admin_route_secret = original_secret

