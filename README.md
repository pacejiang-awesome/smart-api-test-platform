# Smart API Test Platform

API automation testing platform targeting the Amap (高德地图) Open API.
Explores AI-assisted test case generation using DeepSeek API (deepseek-v4-flash).

## Features

- Full test coverage for Amap geocoding and POI search APIs
  (normal / error / boundary / parameterized scenarios)
- Allure-based HTML test reports
- FastAPI backend with SQLite persistence for execution history
- Bootstrap 5 dashboard — test result summary and execution history
- AI module: generates test case drafts from API documentation via DeepSeek API

## Tech Stack

| Layer | Technology |
|-------|------------|
| Test Framework | pytest · requests · allure-pytest |
| Backend | FastAPI · SQLite · SQLAlchemy |
| Frontend | Bootstrap 5 |
| AI Module | DeepSeek API (deepseek-v4-flash) |
| Deployment | Docker · Tencent Cloud |
| CI | GitHub Actions |

## Project Structure

```
smart-api-test-platform/
├── tests/          # Test suites (geocode, POI search)
├── core/           # HTTP client, config, DB utilities
├── api/            # FastAPI application
├── models/         # Data models
├── ai_assist/      # AI-assisted test case generator
├── web/            # Frontend templates and static assets
├── docs/decisions/ # Architecture decision records
└── reports/        # Generated Allure HTML reports
```

## Getting Started

**Prerequisites:** Python 3.10+, Java 8+ (required by Allure CLI)

```bash
git clone https://github.com/pacejiang-awesome/smart-api-test-platform.git
cd smart-api-test-platform
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your API keys:

```
AMAP_API_KEY=your_amap_key
DEEPSEEK_API_KEY=your_deepseek_key
```

**Run tests:**
```bash
pytest
allure serve allure-results
```

**Start backend:**
```bash
uvicorn api.main:app --reload
```

**Run with Docker:**
```bash
docker build -t smart-api-test-platform .
docker run --env-file .env -p 8000:8000 smart-api-test-platform
```

## Roadmap

- [x] Project scaffolding
- [x] Geocoding API — full scenario coverage
- [x] POI search tests
- [x] FastAPI backend + SQLite persistence
- [x] Bootstrap 5 dashboard
- [x] AI-assisted test case generation
- [x] Docker + Tencent Cloud deployment
- [x] GitHub Actions CI
- [x] GitHub Actions CD (auto-deploy to Tencent Cloud)
