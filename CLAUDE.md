# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Unlock-VIP is a lightweight FastAPI-based service for downloading CSDN (Chinese Software Developer Network) articles and documents. It uses cookie-based authentication for CSDN access and ThreadPoolExecutor for asynchronous task processing. The service has been optimized for simplicity with no external dependencies like Redis or Celery.

## Essential Commands

### Development Setup
```bash
# Create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure cookies (required for CSDN authentication)
cp cookies.json.example cookies.json
# Edit cookies.json with actual CSDN cookies
```

### Running the Application
```bash
# Start FastAPI application (single process)
python run.py

# Or use uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_thread_pool.py

# Run with coverage
pytest --cov=app tests/
```

### Code Quality
```bash
# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

## Architecture Overview

### Core Components

**FastAPI Application** (`app/main.py`)
- Single-process application with lifespan management
- Built-in ThreadPoolExecutor for async tasks
- API documentation at `/docs`
- Health check at `/health`
- No authentication required - simplified for direct use

**Thread Pool** (`app/services/file_service.py`)
- Python's built-in ThreadPoolExecutor
- 4 worker threads by default (configurable)
- Automatic lifecycle management
- In-memory task status storage

**Service Layer** (`app/services/`)
- `article_service.py`: CSDN blog scraping with cookie auth
- `wenku_service.py`: CSDN document processing with markdown rendering
- `file_service.py`: File management and thread pool

### Key Design Patterns

1. **CSDN Cookie Authentication**: Uses cookies.json for CSDN access
2. **Thread Pool Processing**: All downloads handled via ThreadPoolExecutor
3. **In-Memory Task Storage**: Task status stored in memory dictionary
4. **Service Layer**: Business logic separated from API endpoints
5. **Task Status Polling**: Clients poll for download completion
6. **No External Dependencies**: No Redis, Celery, or database required

### API Endpoints

**Article Operations**
- `POST /api/article/submit` - Create download task (returns task_id)
- `GET /api/article/task/{task_id}/status` - Check task status
- `GET /api/article/task/{task_id}/result` - Get task result with HTML content
- `GET /api/file/{filename}` - Download completed file

### Important Configuration Files

- `.env` - Environment variables (PORT, THREAD_POOL_WORKERS)
- `cookies.json` - CSDN authentication cookies (create from example)

### Browser Integration

Userscripts in `userscripts/` provide browser integration:
- `unlock_vip.js` - Adds download buttons to CSDN pages
- `csdn_helper.js` - Additional CSDN utilities

### Testing Strategy

Tests focus on:
- Thread pool operations (`test_thread_pool.py`)
- Complete download flow (`test_complete_flow.py`)
- Wenku downloads (`test_wenku_download.py`)

### Common Development Tasks

**Adding New Services**
1. Create service class in `app/services/`
2. Add API endpoints in `app/api/`
3. Add task worker function if needed
4. Write comprehensive tests

**Debugging Download Issues**
1. Check cookies.json validity
2. Verify thread pool is running
3. Check task logs in console output
4. Test with different article types (blog vs wenku)

**Production Deployment**
1. Set appropriate THREAD_POOL_WORKERS in .env
2. Use a production ASGI server (Gunicorn + Uvicorn)
3. Set up reverse proxy (Nginx/Caddy) if needed
4. Configure log rotation

### Key Technical Decisions

1. **Cookie-based CSDN Auth**: Uses cookies.json for CSDN access
2. **ThreadPoolExecutor**: Built-in Python thread pool instead of Celery
3. **In-Memory Storage**: Task status stored in memory (simple and fast)
4. **Multi-format Support**: Handles both blog articles and documents
5. **No Authentication**: Simplified deployment and usage
6. **Single Process**: Easy to deploy and manage
