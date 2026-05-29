# 5 - 新增接口测试设计（regeo / ip / weather / district）

## 背景

Week 7+ 在现有 geocode / POI 搜索基础上，新增四个高德接口的测试覆盖。
每个接口在写用例前均通过探针脚本对关键场景实测，以实际响应为准，不依赖文档假设。

---

## A · 逆地理编码 `/geocode/regeo`

### 关键发现：status 语义与 geocode 不同

| 输入 | 文档预期 | 实测结果 |
|------|---------|---------|
| 越界坐标 `200,100` | status=0（参数非法） | status=1，infocode=10000，formatted_address=[] |
| 非数字格式 `abc,xyz` | status=0（参数非法） | status=1，infocode=10000，formatted_address=[] |
| 海洋坐标 `150,30` | 未记录 | status=1，infocode=10000，formatted_address=[] |

**结论**：regeo 对无效坐标不拒绝，而是容错处理——返回 `status=1` + `formatted_address=[]`（空列表）。

### formatted_address 类型不一致

- 有匹配结果时：字符串，如 `"北京市东城区东华门街道天安门"`
- 无匹配结果时：空列表 `[]`

这是高德历史 API 设计问题，断言时须区分两种类型：

```python
# 正常场景：断言是字符串且非空
assert isinstance(data["regeocode"]["formatted_address"], str)
assert len(data["regeocode"]["formatted_address"]) > 0

# 无结果场景：断言是空列表
assert data["regeocode"]["formatted_address"] == []
```

### extensions 参数的实际效果

| extensions 值 | 返回的额外字段 |
|--------------|-------------|
| 不传（默认 base） | addressComponent、formatted_address |
| all | 额外增加 roads、roadinters、pois、aois |

### 放弃的方案

- **断言 status=0 来验证无效输入**：实测证明 regeo 不走这条路径，断言会永远失败
- **断言具体地址字符串**：地址数据可能随高德更新微变，产生不稳定用例

---

## B · IP 定位 `/ip`

### 关键发现

| 输入 | 文档预期 | 实测结果 |
|------|---------|---------|
| 非法格式 `abc.def` | status=0 | status=1，province=[] |
| 越界 `999.x.x.x` | status=0 | status=1，province=[] |
| 骨干网 DNS `114.114.114.114` | 返回省市 | status=1，province=[]（高德无归属数据） |
| 私有 IP `192.168.x.x` | 无结果 | status=1，province='局域网'（特殊标识） |
| 不传 ip 参数 | 用调用方 IP | status=1，返回实际省市 |

**结论**：IP API 与 regeo 相同，全部返回 `status=1`，无效输入以空列表容错。

### province / city 类型不一致

- 有定位结果时：字符串，如 `"四川省"`
- 无定位结果时：空列表 `[]`

### 私有 IP 的特殊处理

`192.168.x.x` 返回 `province='局域网'`，这是高德的明确语义，不同于"定位失败"的空列表，单独立用例加以区分。

### 放弃的方案

- **用 114.114.114.114 作正常场景**：该 IP 是骨干网 DNS，高德无省级归属，无法作为稳定的正向断言
- **断言具体省市名**：`no_ip_param` 的定位结果取决于调用方 IP，跨环境不稳定，只断言非空字符串

---

## C · 天气查询 `/weather/weatherInfo`

### 关键发现

| 场景 | 实测结果 |
|------|---------|
| `extensions=base` | status=1，`lives=[{weather, temperature, city, ...}]` |
| `extensions=all` | status=1，`forecasts=[{casts: [4天]}]` |
| `extensions=xyz`（非法值） | **status=0，infocode=20000**（唯一触发 status=0 的场景） |
| `city=9999999`（无效 adcode） | status=1，`lives=[[]]`（嵌套空列表） |
| 县级 adcode `110117` | status=1，正常返回天气 |

### 无效 adcode 的特殊容错结构

```python
# 无效 adcode 返回的结构
{"status": "1", "lives": [[]]}

# 与 IP/regeo 的空列表不同，这里是嵌套空列表
assert data["lives"] == [[]]
```

### extensions 是本接口唯一有协议层校验的参数

`extensions` 只接受 `base` / `all`，其他值直接返回 `status=0`。这与 regeo / IP 的"全部容错"策略形成对比，是天气接口特有的严格校验。

---

## D · 行政区域查询 `/config/district`

### subdistrict 层级实测（以北京市为例）

| subdistrict | L1 | L2 | L3 |
|-------------|----|----|-----|
| 0 | 0 | 0 | 0 |
| 1 | 1 | 0 | 0 |
| 2 | 1 | 16 | 0 |
| 3 | 1 | 16 | 13 |

L3 为街道/乡镇级，是接口支持的最深层级。

### 不存在地名的容错

返回 `districts=[]`（顶层空列表），与天气查询的 `lives=[[]]` 不同——两个接口的容错结构不一致，断言时注意区分。

### 放弃的方案

- **断言 L2 的精确数量**：行政区划可能随区划调整变化，断言 `>=21` 比精确数更稳定
