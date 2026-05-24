import pytest
from core.http_client import client


def test_geocode_valid_address():
    # 验证合法地址能返回有效坐标，确认接口基本链路通畅

    # Arrange
    params = {"address": "北京市天安门广场"}

    # Act
    response = client.get("/geocode/geo", params=params)
    data = response.json()

    # Assert
    assert response.status_code == 200
    assert data["status"] == "1"
    assert len(data["geocodes"]) > 0
    assert "location" in data["geocodes"][0]
