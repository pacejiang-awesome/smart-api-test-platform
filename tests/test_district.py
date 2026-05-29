import pytest
import allure
from core.http_client import client


@allure.feature("行政区域查询接口")
@allure.story("正常场景")
@allure.title("省名查询返回 name 和 adcode")
@pytest.mark.integration
def test_district_province_query():
    # 验证基本链路通畅，结果包含 name 和 adcode 两个核心标识字段
    response = client.get("/config/district", params={"keywords": "北京市"})
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    assert data["infocode"] == "10000"
    top = data["districts"][0]
    assert top["name"] == "北京市"
    assert top["adcode"] == "110000"


@allure.feature("行政区域查询接口")
@allure.story("正常场景")
@allure.title("subdistrict=2 返回省下两级区划")
@pytest.mark.integration
def test_district_subdistrict_2():
    # 广东省有 21 个地市，subdistrict=2 应在 L2 返回 >=21 条——验证层级下钻参数生效
    response = client.get("/config/district", params={
        "keywords": "广东省",
        "subdistrict": "2",
    })
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    top = data["districts"][0]
    level1 = top["districts"]
    level2 = [d for city in level1 for d in city.get("districts", [])]
    assert len(level2) >= 21


@allure.feature("行政区域查询接口")
@allure.story("边界场景")
@allure.title("不存在的地名返回空列表")
@pytest.mark.integration
def test_district_nonexistent():
    # 不存在的关键词应返回 districts=[]，接口不崩溃且行为明确
    response = client.get("/config/district", params={"keywords": "火星第一省"})
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    assert data["districts"] == []


@allure.feature("行政区域查询接口")
@allure.story("边界场景")
@allure.title("subdistrict=3 下钻到街道级")
@pytest.mark.integration
def test_district_subdistrict_3():
    # 最深层级应返回街道/乡镇数据，验证接口层级支持的上限
    response = client.get("/config/district", params={
        "keywords": "北京市",
        "subdistrict": "3",
    })
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    top = data["districts"][0]
    level1 = top["districts"]
    level2 = level1[0]["districts"] if level1 else []
    level3 = level2[0]["districts"] if level2 else []
    assert len(level3) > 0


@allure.feature("行政区域查询接口")
@allure.story("参数化场景")
@pytest.mark.integration
@pytest.mark.parametrize("keywords", [
    "北京市",
    "广东省",
    "四川省",
])
def test_district_multiple_provinces(keywords):
    # 多个省份均应返回有效 name 和 adcode，验证接口覆盖的地域普遍性
    response = client.get("/config/district", params={"keywords": keywords})
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    top = data["districts"][0]
    assert len(top["name"]) > 0
    assert len(top["adcode"]) > 0
