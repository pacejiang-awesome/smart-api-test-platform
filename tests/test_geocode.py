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


def test_geocode_empty_address():
    # 空地址应被接口识别为非法参数，不应静默返回空结果
    params = {"address": ""}
    response = client.get("/geocode/geo", params=params)
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "0"
    assert data["infocode"] == "20000"


def test_geocode_gibberish_address():
    # 无法识别的乱码地址应返回引擎错误，而非假装成功
    params = {"address": "xyzabc这个地方根本不存在"}
    response = client.get("/geocode/geo", params=params)
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "0"
    assert data["infocode"] == "30001"
