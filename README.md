# Smart API Test Platform

API automation testing platform targeting the Amap (高德地图) Open API.
Explores AI-assisted test case generation using Claude API.

## Features

- Full test coverage for Amap geocoding and POI search APIs
  (normal / error / boundary / parameterized scenarios)
- Allure-based HTML test reports
- FastAPI backend with SQLite persistence for execution history
- Bootstrap 5 dashboard — test case list, execution history, report links
- AI module: generates test case drafts from API documentation via Claude API

## Tech Stack

| Layer | Technology |
|-------|------------|
| Test Framework | pytest · requests · allure-pytest |
| Backend | FastAPI · SQLite · SQLAlchemy |
| Frontend | Bootstrap 5 |
| AI Module | Claude API (anthropic SDK) |
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
git clone <repo-url>
cd smart-api-test-platform
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set your Amap API key:

```
AMAP_API_KEY=your_key_here
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

## Roadmap

- [x] Project scaffolding
- [ ] Geocoding API — full scenario coverage
- [ ] POI search tests
- [ ] FastAPI backend + SQLite persistence
- [ ] Bootstrap 5 dashboard
- [ ] AI-assisted test case generation
- [ ] Docker + Tencent Cloud deployment
