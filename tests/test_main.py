import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_read_root():
    """Тест кореневого endpoint /"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, Photoshare!"}


@pytest.mark.asyncio
async def test_healthchecker(monkeypatch):
    """Тест /api/healthchecker із моком бази даних"""
    from app.main import healthchecker
    from app.database.connect_db import get_db
    from fastapi import HTTPException

    class FakeSession:
        def execute(self, stmt):
            class Result:
                def fetchone(self):
                    return (1,)
            return Result()

    async def fake_get_db():
        return FakeSession()

    # Використовуємо мок get_db
    monkeypatch.setattr("app.main.get_db", fake_get_db)

    # Викликаємо healthchecker напряму
    db = await fake_get_db()
    response = healthchecker(db)
    assert response == {"message": "Welcome to Photoshare!"}
