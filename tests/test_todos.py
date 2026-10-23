from beanie import PydanticObjectId
from fastapi import status

from app.core.constants import TODO_NOT_FOUND
from app.db.models import Todos

MISSING_ID = str(PydanticObjectId())  # valid ObjectId that doesn't exist


def todo_to_dict(todo):
    return {
        "id": str(todo.id),
        "title": todo.title,
        "description": todo.description,
        "priority": todo.priority,
        "complete": todo.complete,
        "owner_id": str(todo.owner_id),
    }


async def test_read_all_authenticated(client, test_todo):
    response = await client.get("/todos")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [todo_to_dict(test_todo)]


async def test_read_one_authenticated(client, test_todo):
    response = await client.get(f"/todos/{test_todo.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == todo_to_dict(test_todo)


async def test_read_one_not_found(client, test_user):
    response = await client.get(f"/todos/{MISSING_ID}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": TODO_NOT_FOUND.format(todo_id=MISSING_ID)}


async def test_read_one_malformed_id(client, test_user):
    response = await client.get("/todos/not-an-object-id")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_create_todo(client, test_user):
    new_todo = {
        "title": "New Test Todo",
        "description": "This is a new test todo",
        "priority": 2,
        "complete": False
    }
    response = await client.post("/todos", json=new_todo)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == new_todo["title"]
    assert data["owner_id"] == str(test_user.id)

    stored = await Todos.get(PydanticObjectId(data["id"]))
    assert stored is not None
    assert stored.description == new_todo["description"]


async def test_create_todo_invalid_payload(client, test_user):
    invalid_todo = {
        "title": "No",  # too short (min 3)
        "description": "Valid description",
        "priority": 5,  # out of range (1-3)
    }
    response = await client.post("/todos", json=invalid_todo)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_update_todo(client, test_todo):
    updated_todo = {
        "title": "Updated Test Todo",
        "description": "This is an updated test todo",
        "priority": 3,
        "complete": True
    }
    response = await client.put(f"/todos/{test_todo.id}", json=updated_todo)
    assert response.status_code == status.HTTP_200_OK

    stored = await Todos.get(test_todo.id)
    assert stored.title == updated_todo["title"]
    assert stored.description == updated_todo["description"]
    assert stored.priority == updated_todo["priority"]
    assert stored.complete == updated_todo["complete"]


async def test_update_todo_not_found(client, test_user):
    updated_todo = {
        "title": "Updated Test Todo",
        "description": "This is an updated test todo",
        "priority": 3,
        "complete": True
    }
    response = await client.put(f"/todos/{MISSING_ID}", json=updated_todo)
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_todo(client, test_todo):
    response = await client.delete(f"/todos/{test_todo.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert await Todos.get(test_todo.id) is None


async def test_delete_todo_not_found(client, test_user):
    response = await client.delete(f"/todos/{MISSING_ID}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
