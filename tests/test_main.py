from fastapi import status

from app.core.constants import HEALTH_PATH, HEALTHY_STATUS

from .utils import client


def test_return_health_check():
    response = client.get(HEALTH_PATH)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": HEALTHY_STATUS}
