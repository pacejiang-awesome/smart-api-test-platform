import json
from unittest.mock import Mock

import pytest
import requests

from ai_assist import case_generator


API_SPEC = {
    "api_name": "地理编码",
    "params": [
        {"name": "address", "required": True, "desc": "待解析地址"},
    ],
    "rules": "地址不能为空",
}

VALID_CASE = {
    "name": "合法地址",
    "params": {"address": "北京市天安门广场"},
    "expected": "返回有效坐标",
    "description": "验证基本链路",
}


def _response(response_data):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = response_data
    return response


def _completion(content, finish_reason="stop"):
    return {
        "choices": [
            {
                "message": {"content": content},
                "finish_reason": finish_reason,
            }
        ]
    }


def test_generate_cases_requires_deepseek_key(monkeypatch):
    # 缺少密钥时应在发送请求前失败，避免无意义的外部调用
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    post = Mock()
    monkeypatch.setattr(case_generator.requests, "post", post)

    with pytest.raises(EnvironmentError, match="DEEPSEEK_API_KEY"):
        case_generator.generate_cases(API_SPEC)

    post.assert_not_called()


def test_generate_cases_sends_deepseek_request_and_returns_cases(monkeypatch):
    # 验证迁移后的地址、模型和结构化输出设置都实际进入请求
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek-key")
    response = _response(_completion(json.dumps({"cases": [VALID_CASE]})))
    post = Mock(return_value=response)
    monkeypatch.setattr(case_generator.requests, "post", post)

    result = case_generator.generate_cases(API_SPEC)

    assert result == [VALID_CASE]
    _, kwargs = post.call_args
    assert post.call_args.args == ("https://api.deepseek.com/chat/completions",)
    assert kwargs["headers"]["Authorization"] == "Bearer test-deepseek-key"
    assert kwargs["json"]["model"] == "deepseek-v4-pro"
    assert kwargs["json"]["thinking"] == {"type": "disabled"}
    assert kwargs["json"]["response_format"] == {"type": "json_object"}
    assert kwargs["json"]["max_tokens"] == 4096
    assert kwargs["timeout"] == 120


def test_generate_cases_propagates_http_error(monkeypatch):
    # 认证、余额或限流等 HTTP 错误应保留 requests 的原始异常类型
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek-key")
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError("402 Payment Required")
    monkeypatch.setattr(case_generator.requests, "post", Mock(return_value=response))

    with pytest.raises(requests.HTTPError, match="402"):
        case_generator.generate_cases(API_SPEC)


def test_generate_cases_rejects_non_json_http_response(monkeypatch):
    # 网关返回 HTML 等非 JSON 内容时，应给出稳定错误而不是泄露完整响应
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek-key")
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.side_effect = json.JSONDecodeError("invalid", "<html>", 0)
    monkeypatch.setattr(case_generator.requests, "post", Mock(return_value=response))

    with pytest.raises(ValueError, match="non-JSON HTTP response"):
        case_generator.generate_cases(API_SPEC)


def test_generate_cases_retries_invalid_content_once(monkeypatch):
    # 模型偶发输出非法 JSON 时应加强提示重试，而不是直接丢弃本次生成
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek-key")
    invalid = _response(_completion("not-json"))
    valid = _response(_completion(json.dumps({"cases": [VALID_CASE]})))
    post = Mock(side_effect=[invalid, valid])
    monkeypatch.setattr(case_generator.requests, "post", post)

    result = case_generator.generate_cases(API_SPEC)

    assert result == [VALID_CASE]
    assert post.call_count == 2
    retry_prompt = post.call_args_list[1].kwargs["json"]["messages"][1]["content"]
    assert "上一次输出未通过 JSON 或字段校验" in retry_prompt


def test_generate_cases_stops_after_one_retry(monkeypatch):
    # 连续两次无效时应返回最后一次校验错误，避免失控重试和额外费用
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek-key")
    post = Mock(return_value=_response(_completion("not-json")))
    monkeypatch.setattr(case_generator.requests, "post", post)

    with pytest.raises(ValueError, match="valid JSON"):
        case_generator.generate_cases(API_SPEC)

    assert post.call_count == 2


@pytest.mark.parametrize(
    "response_data, error",
    [
        ({}, "Unexpected DeepSeek response structure"),
        ({"choices": []}, "Unexpected DeepSeek response structure"),
        (_completion(None), "empty content"),
        (_completion('{"cases": []}', finish_reason="length"), "truncated"),
        (_completion("not-json"), "valid JSON"),
    ],
)
def test_generate_cases_rejects_invalid_response_content(
    monkeypatch, response_data, error
):
    # 响应结构、空内容、截断和非法 JSON 都不应被误当成有效用例
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek-key")
    monkeypatch.setattr(
        case_generator.requests,
        "post",
        Mock(return_value=_response(response_data)),
    )

    with pytest.raises(ValueError, match=error):
        case_generator.generate_cases(API_SPEC)


@pytest.mark.parametrize(
    "payload, error",
    [
        ([VALID_CASE], "JSON object"),
        ({}, "non-empty list"),
        ({"cases": []}, "non-empty list"),
        ({"cases": [{"name": "缺字段"}]}, "missing fields"),
        ({"cases": [{**VALID_CASE, "name": ""}]}, "non-empty string"),
        ({"cases": [{**VALID_CASE, "params": "address=北京"}]}, "must be an object"),
    ],
)
def test_generate_cases_validates_case_contract(monkeypatch, payload, error):
    # 即使 JSON 语法正确，也必须满足调用方依赖的用例字段契约
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek-key")
    response_data = _completion(json.dumps(payload, ensure_ascii=False))
    monkeypatch.setattr(
        case_generator.requests,
        "post",
        Mock(return_value=_response(response_data)),
    )

    with pytest.raises(ValueError, match=error):
        case_generator.generate_cases(API_SPEC)


def test_generate_cases_error_does_not_include_api_key(monkeypatch):
    # 模型响应异常时，错误信息不得包含鉴权密钥
    api_key = "test-secret-deepseek-key"
    monkeypatch.setenv("DEEPSEEK_API_KEY", api_key)
    response_data = {"choices": [{"unexpected": True}]}
    monkeypatch.setattr(
        case_generator.requests,
        "post",
        Mock(return_value=_response(response_data)),
    )

    with pytest.raises(ValueError) as exc_info:
        case_generator.generate_cases(API_SPEC)

    assert api_key not in str(exc_info.value)
    assert case_generator.requests.post.call_count == 2
