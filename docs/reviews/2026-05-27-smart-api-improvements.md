# Smart API Test Platform Improvement Review

Date: 2026-05-27

This review is based on a local read-through of the repository and one test run:

```bash
pytest -q
```

Result: 19 tests passed. The run produced a `.pytest_cache` permission warning and may update the ignored local `test_results.db` runtime database.

## Summary

The project already has a clear shape: pytest-based API tests, a small FastAPI dashboard, SQLite persistence, Docker packaging, GitHub Actions, and a GLM-based test case generator.

The most valuable next improvements are:

1. Split real external API tests from mockable unit tests.
2. Fix request parameter mutation in the HTTP client.
3. Add pagination to the results API.
4. Move database configuration to environment variables.
5. Pin dependency versions for reproducible CI and deployments.

## High Priority

### 1. Separate Integration Tests From Unit Tests

Current tests call the real Amap API directly from files such as:

- `tests/test_geocode.py`
- `tests/test_poi_search.py`

This verifies the real service path, but it also makes CI depend on network stability, API quota, third-party behavior, and valid secrets.

Recommended action:

- Mark real API tests with `@pytest.mark.integration`.
- Add mock-based tests for local behavior.
- Configure CI to run unit tests by default.
- Run integration tests only when `AMAP_API_KEY` is present or on a scheduled/manual workflow.

Example command split:

```bash
pytest -m "not integration"
pytest -m integration
```

### 2. Avoid Mutating Caller Parameters

In `core/http_client.py`, the current client mutates the caller-provided `params` dictionary:

```python
merged_params = params or {}
merged_params["key"] = config.amap_api_key
```

If a caller reuses the same dictionary, the API key remains inserted after the call. This is a subtle side effect.

Recommended action:

```python
merged_params = {**(params or {}), "key": config.amap_api_key}
```

### 3. Add Pagination to `/results`

`api/main.py` currently loads all rows:

```python
rows = db.query(TestResult).order_by(TestResult.run_at.desc()).all()
```

This is fine for a small local demo, but it will slow down as test history grows.

Recommended action:

- Add `limit` and `offset` query parameters.
- Default to the most recent 100 records.
- Return total count separately from the current page.

Suggested response shape:

```json
{
  "total": 500,
  "limit": 100,
  "offset": 0,
  "results": []
}
```

### 4. Make Database URL Configurable

`core/db.py` hardcodes:

```python
DATABASE_URL = "sqlite:///./test_results.db"
```

This couples local development, Docker, CI, and server deployments to the same path.

Recommended action:

- Add `DATABASE_URL` support through environment variables.
- Keep `sqlite:///./test_results.db` as the default.
- Add `DATABASE_URL` to `.env.example`.

## Medium Priority

### 5. Remove or Gate Fixed Test Delay

`conftest.py` adds a fixed delay after every test:

```python
time.sleep(0.3)
```

This slows the suite as test count grows. If the delay exists for rate limiting, it should be configurable and applied only to real integration tests.

Recommended action:

- Remove it for unit tests.
- Use an environment variable such as `API_TEST_DELAY_SECONDS` for integration runs if needed.

### 6. Pin Dependencies

`requirements.txt` currently uses unpinned dependencies:

```text
pytest
requests
allure-pytest
fastapi
uvicorn[standard]
sqlalchemy
python-dotenv
aiofiles
```

This makes local runs, CI, and Docker builds vulnerable to upstream breaking changes.

Recommended action:

- Pin direct dependencies to compatible ranges.
- Consider `pip-tools` or `uv` for a generated lock file.

Example:

```text
pytest>=9,<10
requests>=2.32,<3
fastapi>=0.115,<1
sqlalchemy>=2,<3
```

### 7. Complete `.env.example`

`.env.example` only includes:

```env
AMAP_API_KEY=your_amap_api_key_here
```

The AI module also requires `GLM_API_KEY`, and database configuration would benefit from a documented default.

Recommended action:

```env
AMAP_API_KEY=your_amap_api_key_here
GLM_API_KEY=your_glm_api_key_here
DATABASE_URL=sqlite:///./test_results.db
```

### 8. Improve AI Response Error Handling

`ai_assist/case_generator.py` assumes the GLM response always contains a valid JSON array in:

```python
resp.json()["choices"][0]["message"]["content"]
```

Recommended action:

- Validate the response structure before indexing.
- Catch `json.JSONDecodeError`.
- Include a concise preview of the invalid model output in the exception.
- Consider validating generated cases with a small schema before returning them.

## Low Priority

### 9. Run Docker as a Non-Root User

The current `Dockerfile` runs the app as the default root user.

Recommended action:

- Create a dedicated application user.
- Switch to that user before `CMD`.

This reduces risk when running the container on a shared host or cloud server.

### 10. Update README Roadmap

The repository already contains GitHub Actions workflows:

- `.github/workflows/ci.yml`
- `.github/workflows/network-check.yml`

But `README.md` still marks GitHub Actions CI as unfinished.

Recommended action:

- Mark CI as complete if the current workflow is accepted.
- Or clarify what remains, such as integration-test gating, coverage upload, or Allure report publishing.

### 11. Fix `.pytest_cache` Permission Noise

The test run passed, but pytest emitted a cache permission warning for `.pytest_cache`.

Recommended action:

- Delete and regenerate `.pytest_cache` if possible.
- Or fix local permissions on that directory.

This is not a product bug, but it makes test output noisier than necessary.

## Suggested Implementation Order

1. Fix `core/http_client.py` parameter mutation.
2. Add `.env.example` entries.
3. Add `/results` pagination.
4. Make `DATABASE_URL` configurable.
5. Split unit and integration tests.
6. Pin dependencies.
7. Harden AI response parsing.
8. Clean up Docker and README polish.

## 修复状态

| # | 问题 | 状态 |
|---|------|------|
| 2 | HTTP client 参数污染（`core/http_client.py`） | ✅ 已修复（c331f57） |

