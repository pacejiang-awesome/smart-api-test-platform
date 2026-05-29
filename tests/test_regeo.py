import pytest
import allure
from core.http_client import client


@allure.feature("逆地理编码接口")
@allure.story("正常场景")
@allure.title("合法坐标返回完整地址")
@pytest.mark.integration
def test_regeo_valid_location():
    # 验证合法坐标能解析出非空字符串地址，确认接口基本链路通畅
    response = client.get("/geocode/regeo", params={"location": "116.397428,39.90923"})
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    assert data["infocode"] == "10000"
    assert isinstance(data["regeocode"]["formatted_address"], str)
    assert len(data["regeocode"]["formatted_address"]) > 0


@allure.feature("逆地理编码接口")
@allure.story("正常场景")
@allure.title("extensions=all 返回道路和 POI 扩展字段")
@pytest.mark.integration
def test_regeo_extensions_all():
    # extensions=all 应额外返回 roads/pois/aois，验证扩展参数被接口正确识别
    response = client.get("/geocode/regeo", params={
        "location": "116.397428,39.90923",
        "extensions": "all",
    })
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    assert "roads" in data["regeocode"]
    assert "pois" in data["regeocode"]


@allure.feature("逆地理编码接口")
@allure.story("边界场景")
@allure.title("越界坐标被容错处理，返回空地址而非报错")
@pytest.mark.integration
def test_regeo_out_of_range():
    # regeo 不拒绝越界坐标，而是 status=1 + 空列表——验证接口不崩溃且行为一致
    response = client.get("/geocode/regeo", params={"location": "200,100"})
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    assert data["regeocode"]["formatted_address"] == []


@allure.feature("逆地理编码接口")
@allure.story("边界场景")
@allure.title("非数字格式坐标被容错处理，返回空地址而非报错")
@pytest.mark.integration
def test_regeo_invalid_format():
    # 同 out_of_range：非数字输入也走容错路径，不触发 status=0
    response = client.get("/geocode/regeo", params={"location": "abc,xyz"})
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    assert data["regeocode"]["formatted_address"] == []


@allure.feature("逆地理编码接口")
@allure.story("边界场景")
@allure.title("服务区外的海洋坐标返回空地址")
@pytest.mark.integration
def test_regeo_ocean_coordinates():
    # 太平洋坐标超出高德服务区，验证接口返回空结果而非异常
    response = client.get("/geocode/regeo", params={"location": "150,30"})
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    assert data["regeocode"]["formatted_address"] == []


@allure.feature("逆地理编码接口")
@allure.story("参数化场景")
@pytest.mark.integration
@pytest.mark.parametrize("location,city_hint", [
    ("116.397428,39.90923", "北京"),
    ("121.490317,31.234679", "上海"),
    ("113.324329,23.107449", "广州"),
])
def test_regeo_major_cities(location, city_hint):
    # 各主要城市坐标均应解析出有效字符串地址，验证接口的地理覆盖普遍性
    response = client.get("/geocode/regeo", params={"location": location})
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    assert isinstance(data["regeocode"]["formatted_address"], str)
    assert len(data["regeocode"]["formatted_address"]) > 0
