
from fastapi import status

from models import Todos

from .utils import client, TestingSessionLocal, TEST_USER_ID


def todo_to_dict(todo):
    return {
        "id": todo.id,
        "title": todo.title,
        "description": todo.description,
        "priority": todo.priority,
        "complete": todo.complete,
        "owner_id": todo.owner_id,
    }


def test_read_all_authenticated(test_todo):
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [todo_to_dict(test_todo)]


def test_read_one_authenticated(test_todo):
    response = client.get(f"/todo/{test_todo.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == todo_to_dict(test_todo)


def test_read_one_not_found():
    response = client.get("/todo/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Todo with id 999 not found"}


def test_create_todo():
    new_todo = {
        "title": "New Test Todo",
        "description": "This is a new test todo",
        "priority": 2,
        "complete": False
    }
    response = client.post("/todo", json=new_todo)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == new_todo["title"]
    assert data["description"] == new_todo["description"]
    assert data["priority"] == new_todo["priority"]
    assert data["complete"] == new_todo["complete"]
    assert data["owner_id"] == TEST_USER_ID

    db = TestingSessionLocal()
    model_todo = db.query(Todos).filter(Todos.id == data["id"]).first()
    db.close()
    assert model_todo is not None


def test_create_todo_invalid_payload():
    invalid_todo = {
        "title": "No",  # too short (min 3)
        "description": "Valid description",
        "priority": 5,  # out of range (1-3)
    }
    response = client.post("/todo", json=invalid_todo)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_update_todo(test_todo):
    updated_todo = {
        "title": "Updated Test Todo",
        "description": "This is an updated test todo",
        "priority": 3,
        "complete": True
    }
    response = client.put(f"/todo/{test_todo.id}", json=updated_todo)
    assert response.status_code == status.HTTP_200_OK

    db = TestingSessionLocal()
    model_todo = db.query(Todos).filter(Todos.id == test_todo.id).first()
    db.close()
    assert model_todo.title == updated_todo["title"]
    assert model_todo.description == updated_todo["description"]
    assert model_todo.priority == updated_todo["priority"]
    assert model_todo.complete == updated_todo["complete"]


def test_update_todo_not_found():
    updated_todo = {
        "title": "Updated Test Todo",
        "description": "This is an updated test todo",
        "priority": 3,
        "complete": True
    }
    response = client.put("/todo/999", json=updated_todo)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_todo(test_todo):
    response = client.delete(f"/todo/{test_todo.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    db = TestingSessionLocal()
    model_todo = db.query(Todos).filter(Todos.id == test_todo.id).first()
    db.close()
    assert model_todo is None


def test_delete_todo_not_found():
    response = client.delete("/todo/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
