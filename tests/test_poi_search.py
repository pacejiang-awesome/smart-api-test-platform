import pytest
import allure
from core.http_client import client


@allure.feature("POI搜索接口")
@allure.story("正常场景")
@allure.title("关键词搜索返回匹配结果")
@pytest.mark.integration
def test_poi_search_valid_keywords():
    # 验证合法关键词能返回包含 name 和 location 的 POI 列表
    response = client.get("/place/text", params={
        "keywords": "星巴克",
        "city": "北京",
        "output": "json",
    })
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    assert int(data["count"]) > 0
    assert len(data["pois"]) > 0
    assert "name" in data["pois"][0]
    assert "location" in data["pois"][0]


@allure.feature("POI搜索接口")
@allure.story("异常场景")
@allure.title("空关键词返回参数非法错误")
@pytest.mark.integration
def test_poi_search_empty_keywords():
    # 空关键词应被识别为非法参数值，返回 20000 而非静默返回空列表
    response = client.get("/place/text", params={
        "keywords": "",
        "city": "北京",
        "output": "json",
    })
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "0"
    assert data["infocode"] == "20000"


@allure.feature("POI搜索接口")
@allure.story("异常场景")
@allure.title("缺少必填参数返回缺参数错误")
@pytest.mark.integration
def test_poi_search_missing_keywords():
    # 缺少 keywords 参数应返回 20001，与空值错误码 20000 区分
    response = client.get("/place/text", params={
        "city": "北京",
        "output": "json",
    })
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "0"
    assert data["infocode"] == "20001"


@allure.feature("POI搜索接口")
@allure.story("参数化场景")
@pytest.mark.integration
@pytest.mark.parametrize("keywords,city", [
    ("麦当劳", "上海"),
    ("地铁站", "广州"),
    ("加油站", "成都"),
])
def test_poi_search_multiple_keywords(keywords, city):
    # 不同城市和关键词组合均应返回有效结果，验证接口的普遍可用性
    response = client.get("/place/text", params={
        "keywords": keywords,
        "city": city,
        "output": "json",
    })
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    assert int(data["count"]) > 0
