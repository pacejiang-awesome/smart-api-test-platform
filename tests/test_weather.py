import pytest
import allure
from core.http_client import client


@allure.feature("天气查询接口")
@allure.story("正常场景")
@allure.title("实况天气返回温度和天气描述")
@pytest.mark.integration
def test_weather_base():
    # 验证 extensions=base 返回 lives 数组，且首条包含 weather/temperature/city 字段
    response = client.get("/weather/weatherInfo", params={
        "city": "110000",
        "extensions": "base",
    })
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    assert data["infocode"] == "10000"
    live = data["lives"][0]
    assert "weather" in live
    assert "temperature" in live
    assert "city" in live


@allure.feature("天气查询接口")
@allure.story("正常场景")
@allure.title("预报天气返回 4 天预报数据")
@pytest.mark.integration
def test_weather_forecast():
    # extensions=all 应返回 forecasts，且 casts 包含 4 天——验证扩展参数生效
    response = client.get("/weather/weatherInfo", params={
        "city": "110000",
        "extensions": "all",
    })
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    assert len(data["forecasts"][0]["casts"]) == 4


@allure.feature("天气查询接口")
@allure.story("异常场景")
@allure.title("非法 extensions 值返回参数错误")
@pytest.mark.integration
def test_weather_invalid_extensions():
    # extensions 只接受 base/all，传其他值触发协议层校验返回 status=0
    response = client.get("/weather/weatherInfo", params={
        "city": "110000",
        "extensions": "xyz",
    })
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "0"
    assert data["infocode"] == "20000"


@allure.feature("天气查询接口")
@allure.story("边界场景")
@allure.title("无效 adcode 返回嵌套空列表而非报错")
@pytest.mark.integration
def test_weather_invalid_adcode():
    # 无效 adcode 的容错结构特殊：lives=[[]]，不是 [] 也不触发 status=0
    response = client.get("/weather/weatherInfo", params={"city": "9999999"})
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    assert data["lives"] == [[]]


@allure.feature("天气查询接口")
@allure.story("边界场景")
@allure.title("县级 adcode 返回有效天气数据")
@pytest.mark.integration
def test_weather_county_adcode():
    # 验证接口支持到县区级 adcode，而非只对省市级有效
    response = client.get("/weather/weatherInfo", params={
        "city": "110117",
        "extensions": "base",
    })
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    assert "weather" in data["lives"][0]


@allure.feature("天气查询接口")
@allure.story("参数化场景")
@pytest.mark.integration
@pytest.mark.parametrize("city", [
    "110000",
    "310000",
    "440100",
])
def test_weather_multiple_cities(city):
    # 北京/上海/广州均应返回实况天气，验证接口地域覆盖的普遍性
    response = client.get("/weather/weatherInfo", params={
        "city": city,
        "extensions": "base",
    })
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    assert "weather" in data["lives"][0]
