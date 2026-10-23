
from fastapi import status

from main import app
from models import Todos, Users
from routers.auth import get_current_user

from .utils import client, TestingSessionLocal


def test_read_all_authenticated(test_todo):
    response = client.get("/admin/todo")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{
        "id": test_todo.id,
        "title": test_todo.title,
        "description": test_todo.description,
        "priority": test_todo.priority,
        "complete": test_todo.complete,
        "owner_id": test_todo.owner_id
    }]


def test_delete_todo_authenticated(test_todo):
    response = client.delete(f"/admin/todo/{test_todo.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    db = TestingSessionLocal()
    deleted_todo = db.query(Todos).filter(Todos.id == test_todo.id).first()
    db.close()
    assert deleted_todo is None


def test_delete_todo_not_found():
    response = client.delete("/admin/todo/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Todo not found"}


def test_non_admin_is_rejected(monkeypatch, test_todo):
    # monkeypatch restores the original override after the test.
    monkeypatch.setitem(
        app.dependency_overrides,
        get_current_user,
        lambda: Users(id=2, username="regular", role="user"),
    )
    assert client.get("/admin/todo").status_code == status.HTTP_401_UNAUTHORIZED
    assert client.delete(f"/admin/todo/{test_todo.id}").status_code == status.HTTP_401_UNAUTHORIZED
