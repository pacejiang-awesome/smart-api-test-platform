import pytest
import allure
from core.http_client import client


@allure.feature("IP定位接口")
@allure.story("正常场景")
@allure.title("国内 IP 返回省市信息")
@pytest.mark.integration
def test_ip_domestic():
    # CI runner 在境外，不传 ip 时高德无法定位返回空列表，用已知有归属数据的国内 IP 替代
    # 新浪北京 202.108.33.32：实测返回 province='北京市'，骨干网 DNS（如 114.114.114.114）反而无归属数据
    response = client.get("/ip", params={"ip": "202.108.33.32"})
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    assert data["infocode"] == "10000"
    assert isinstance(data["province"], str)
    assert len(data["province"]) > 0


@allure.feature("IP定位接口")
@allure.story("边界场景")
@allure.title('私有 IP 返回"局域网"标识')
@pytest.mark.integration
def test_ip_private():
    # 192.168.x.x 是高德明确识别的私有 IP，应返回 province='局域网' 而非空列表
    response = client.get("/ip", params={"ip": "192.168.1.1"})
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    assert data["province"] == "局域网"


@allure.feature("IP定位接口")
@allure.story("边界场景")
@allure.title("非法格式 IP 被容错，返回空省市")
@pytest.mark.integration
def test_ip_invalid_format():
    # IP API 不拒绝非法格式，而是 status=1 + 空列表——验证接口不崩溃
    response = client.get("/ip", params={"ip": "abc.def"})
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    assert data["province"] == []


@allure.feature("IP定位接口")
@allure.story("边界场景")
@allure.title("越界 IP 被容错，返回空省市")
@pytest.mark.integration
def test_ip_out_of_range():
    # 999.x.x.x 超出合法 IP 范围，同样走容错路径而非报错
    response = client.get("/ip", params={"ip": "999.999.999.999"})
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    assert data["province"] == []


@allure.feature("IP定位接口")
@allure.story("参数化场景")
@pytest.mark.integration
@pytest.mark.parametrize("ip", [
    "abc.def",
    "999.999.999.999",
    "114.114.114.114",
])
def test_ip_unlocatable(ip):
    # 无法定位的 IP（非法格式、越界、骨干网 DNS）均应返回空省市而非崩溃
    response = client.get("/ip", params={"ip": ip})
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "1"
    assert data["province"] == []
