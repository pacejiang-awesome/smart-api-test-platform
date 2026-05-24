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


def test_geocode_postal_code():
    # 纯数字邮编应被识别为有效地址输入，而非被当作非法参数拒绝
    params = {"address": "100000"}
    response = client.get("/geocode/geo", params=params)
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    assert int(data["count"]) >= 1


def test_geocode_oversized_address():
    # 超长地址不应导致接口报错，验证接口有基本的容错能力
    params = {"address": "北京市" * 100}
    response = client.get("/geocode/geo", params=params)
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"


def test_geocode_special_characters():
    # 含特殊符号的地址应被过滤处理，不应导致请求失败
    params = {"address": "北京市@#¥%天安门"}
    response = client.get("/geocode/geo", params=params)
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    assert int(data["count"]) >= 1
