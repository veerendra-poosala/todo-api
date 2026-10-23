from fastapi import status

from app.core.constants import HEALTH_PATH, HEALTHY_STATUS


async def test_return_health_check(client):
    response = await client.get(HEALTH_PATH)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": HEALTHY_STATUS}
