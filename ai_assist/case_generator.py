# Week 5: GLM API integration — generates test case drafts from API docs
import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

_GLM_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
_GLM_MODEL = "glm-4.5-air"

_SYSTEM_PROMPT = (
    "你是一个 API 测试专家。根据用户提供的接口信息，生成测试用例。"
    "只输出 JSON 数组，不要任何解释文字。"
    "params 中的参数值必须是具体的字符串或数字，不能是表达式或伪代码。"
)


def _build_user_prompt(api_spec: dict) -> str:
    params_lines = "\n".join(
        f"- {p['name']}({'必填' if p['required'] else '非必填'})：{p['desc']}"
        for p in api_spec["params"]
    )
    return (
        f"接口名称：{api_spec['api_name']}\n"
        f"接口参数：\n{params_lines}\n"
        f"业务规则：{api_spec.get('rules', '无')}\n\n"
        "请生成覆盖正常、异常、边界场景的测试用例，输出格式：\n"
        '[{"name": "用例名称", "params": {"参数名": "参数值"}, '
        '"expected": "期望结果描述", "description": "测试意图"}]'
    )


def generate_cases(api_spec: dict) -> list[dict]:
    api_key = os.environ.get("GLM_API_KEY")
    if not api_key:
        raise EnvironmentError("GLM_API_KEY not found in environment")

    resp = requests.post(
        _GLM_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": _GLM_MODEL,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(api_spec)},
            ],
        },
        timeout=120,
    )
    resp.raise_for_status()

    content = resp.json()["choices"][0]["message"]["content"].strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1].rsplit("```", 1)[0]

    return json.loads(content)
