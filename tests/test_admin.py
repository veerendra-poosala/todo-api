from fastapi import status

from app.core.constants import INSUFFICIENT_PERMISSIONS, ROLE_USER, TODO_NOT_FOUND
from app.db.models import Todos, Users
from app.dependencies import get_current_user
from app.main import app

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
    assert response.json() == {"detail": TODO_NOT_FOUND.format(todo_id=999)}


def test_non_admin_is_forbidden(monkeypatch, test_todo):
    # monkeypatch restores the original override after the test.
    monkeypatch.setitem(
        app.dependency_overrides,
        get_current_user,
        lambda: Users(id=2, username="regular", role=ROLE_USER),
    )
    response = client.get("/admin/todo")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": INSUFFICIENT_PERMISSIONS}
    assert client.delete(f"/admin/todo/{test_todo.id}").status_code == status.HTTP_403_FORBIDDEN
