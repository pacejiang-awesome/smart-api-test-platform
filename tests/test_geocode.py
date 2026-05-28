import pytest
import allure
from core.http_client import client


@allure.feature("地理编码接口")
@allure.story("正常场景")
@allure.title("合法地址返回有效坐标")
@pytest.mark.integration
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


@allure.feature("地理编码接口")
@allure.story("异常场景")
@allure.title("空地址返回参数错误")
@pytest.mark.integration
def test_geocode_empty_address():
    # 空地址应被接口识别为非法参数，不应静默返回空结果
    params = {"address": ""}
    response = client.get("/geocode/geo", params=params)
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "0"
    assert data["infocode"] == "20000"


@allure.feature("地理编码接口")
@allure.story("异常场景")
@allure.title("乱码地址返回引擎错误")
@pytest.mark.integration
def test_geocode_gibberish_address():
    # 无法识别的乱码地址应返回引擎错误，而非假装成功
    params = {"address": "xyzabc这个地方根本不存在"}
    response = client.get("/geocode/geo", params=params)
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "0"
    assert data["infocode"] == "30001"


@allure.feature("地理编码接口")
@allure.story("边界场景")
@allure.title("邮政编码作为地址输入")
@pytest.mark.integration
def test_geocode_postal_code():
    # 纯数字邮编应被识别为有效地址输入，而非被当作非法参数拒绝
    params = {"address": "100000"}
    response = client.get("/geocode/geo", params=params)
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    assert int(data["count"]) >= 1


@allure.feature("地理编码接口")
@allure.story("边界场景")
@allure.title("超长地址不导致接口报错")
@pytest.mark.integration
def test_geocode_oversized_address():
    # 超长地址不应导致接口报错，验证接口有基本的容错能力
    params = {"address": "北京市" * 100}
    response = client.get("/geocode/geo", params=params)
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"


@allure.feature("地理编码接口")
@allure.story("边界场景")
@allure.title("含特殊字符的地址被过滤后正常返回")
@pytest.mark.integration
def test_geocode_special_characters():
    # 含特殊符号的地址应被过滤处理，不应导致请求失败
    params = {"address": "北京市@#¥%天安门"}
    response = client.get("/geocode/geo", params=params)
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    assert int(data["count"]) >= 1


@allure.feature("地理编码接口")
@allure.story("参数化场景")
@pytest.mark.integration
@pytest.mark.parametrize("address", [
    "北京市朝阳区",
    "上海市浦东新区",
    "广州市天河区",
    "成都市武侯区",
])
def test_geocode_valid_cities(address):
    # 接口应对全国主要城市地址普遍返回有效坐标，而非仅对特定城市有效
    response = client.get("/geocode/geo", params={"address": address})
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    assert int(data["count"]) >= 1


@allure.feature("地理编码接口")
@allure.story("参数化场景")
@pytest.mark.integration
@pytest.mark.parametrize("address", [
    "",
    "   ",
    "xyzabc这个地方根本不存在",
])
def test_geocode_invalid_inputs(address):
    # 各类非法输入均应被拒绝，确保接口错误处理的一致性
    response = client.get("/geocode/geo", params={"address": address})
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "0"
