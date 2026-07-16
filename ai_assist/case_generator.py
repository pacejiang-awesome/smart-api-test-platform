# AI-assisted test case generation from API specifications
import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

_DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
_DEEPSEEK_MODEL = "deepseek-v4-pro"
_MAX_ATTEMPTS = 2
_REQUIRED_CASE_FIELDS = {"name", "params", "expected", "description"}

_SYSTEM_PROMPT = (
    "你是一个 API 测试专家。根据用户提供的接口信息，生成测试用例。"
    "只输出 JSON 对象，不要任何解释文字。JSON 对象的根字段必须是 cases。"
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
        '{"cases": [{"name": "用例名称", "params": {"参数名": "参数值"}, '
        '"expected": "期望结果描述", "description": "测试意图"}]}'
    )


def _preview(value: object, limit: int = 200) -> str:
    text = value if isinstance(value, str) else repr(value)
    return text if len(text) <= limit else text[:limit] + "..."


def _validate_cases(payload: object) -> list[dict]:
    if not isinstance(payload, dict):
        raise ValueError("DeepSeek output must be a JSON object")

    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("DeepSeek output 'cases' must be a non-empty list")

    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"DeepSeek case at index {index} must be an object")

        missing = _REQUIRED_CASE_FIELDS - case.keys()
        if missing:
            fields = ", ".join(sorted(missing))
            raise ValueError(f"DeepSeek case at index {index} is missing fields: {fields}")

        for field in ("name", "expected", "description"):
            value = case[field]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"DeepSeek case at index {index} field '{field}' "
                    "must be a non-empty string"
                )

        if not isinstance(case["params"], dict):
            raise ValueError(
                f"DeepSeek case at index {index} field 'params' must be an object"
            )

    return cases


def _extract_cases(response_data: object) -> list[dict]:
    try:
        choice = response_data["choices"][0]
        content = choice["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise ValueError(
            "Unexpected DeepSeek response structure; "
            f"response preview: {_preview(response_data)}"
        ) from e

    if choice.get("finish_reason") == "length":
        raise ValueError("DeepSeek response was truncated; increase max_tokens")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("DeepSeek returned empty content")

    try:
        payload = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(
            "DeepSeek did not return valid JSON; "
            f"content preview: {_preview(content)}"
        ) from e

    return _validate_cases(payload)


def _request_cases(api_spec: dict, api_key: str, is_retry: bool) -> list[dict]:
    user_prompt = _build_user_prompt(api_spec)
    if is_retry:
        user_prompt += (
            "\n上一次输出未通过 JSON 或字段校验。"
            "请严格输出一个合法 JSON 对象，确保字符串中的引号已正确转义，"
            "不要输出 Markdown 代码块或解释文字。"
        )
    resp = requests.post(
        _DEEPSEEK_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": _DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "thinking": {"type": "disabled"},
            "response_format": {"type": "json_object"},
            "max_tokens": 4096,
        },
        timeout=120,
    )
    resp.raise_for_status()

    try:
        response_data = resp.json()
    except ValueError as e:
        raise ValueError("DeepSeek returned a non-JSON HTTP response") from e

    return _extract_cases(response_data)


def generate_cases(api_spec: dict) -> list[dict]:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise EnvironmentError("DEEPSEEK_API_KEY not found in environment")

    last_error = None
    for attempt in range(_MAX_ATTEMPTS):
        try:
            return _request_cases(api_spec, api_key, is_retry=attempt > 0)
        except ValueError as e:
            last_error = e

    raise last_error
