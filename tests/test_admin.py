from beanie import PydanticObjectId
from fastapi import status

from app.core.constants import INSUFFICIENT_PERMISSIONS, ROLE_USER, TODO_NOT_FOUND
from app.db.models import Todos, Users
from app.dependencies import get_current_user
from app.main import app


async def test_read_all_authenticated(client, test_todo):
    response = await client.get("/admin/todo")
    assert response.status_code == status.HTTP_200_OK
    assert [todo["id"] for todo in response.json()] == [str(test_todo.id)]


async def test_delete_todo_authenticated(client, test_todo):
    response = await client.delete(f"/admin/todo/{test_todo.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert await Todos.get(test_todo.id) is None


async def test_delete_todo_not_found(client, test_user):
    missing_id = str(PydanticObjectId())
    response = await client.delete(f"/admin/todo/{missing_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": TODO_NOT_FOUND.format(todo_id=missing_id)}


async def test_non_admin_is_forbidden(monkeypatch, client, test_todo):
    regular_user = Users(
        username="regular",
        email="regular@example.com",
        first_name="Regular",
        last_name="User",
        hashed_password="unused",
        role=ROLE_USER,
    )
    # monkeypatch restores the test_user override after the test.
    monkeypatch.setitem(app.dependency_overrides, get_current_user, lambda: regular_user)
    response = await client.get("/admin/todo")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": INSUFFICIENT_PERMISSIONS}
    assert (await client.delete(f"/admin/todo/{test_todo.id}")).status_code == status.HTTP_403_FORBIDDEN
