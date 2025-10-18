# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Unlock-VIP is a simplified FastAPI-based service for downloading CSDN (Chinese Software Developer Network) articles and documents. It uses cookie-based authentication for CSDN access and Celery for asynchronous task processing. The service has been optimized to remove API authentication and caching mechanisms for simplified operation.

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
# Start Redis (required for Celery)
redis-server

# Start Celery worker (in separate terminal)
python celery_worker.py

# Start FastAPI application
python run.py
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_article_service.py

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
- Entry point with lifespan management
- API documentation at `/docs`
- Health check at `/health`
- No authentication required - simplified for direct use

**Celery Task Queue** (`app/core/celery_app.py`)
- Redis-backed task processing
- Async article downloads
- File cleanup tasks

**Service Layer** (`app/services/`)
- `article_service.py`: CSDN blog scraping with cookie auth
- `wenku_service.py`: CSDN document processing with markdown rendering
- `file_service.py`: File management and cleanup

### Key Design Patterns

1. **CSDN Cookie Authentication**: Uses cookies.json for CSDN access (not API authentication)
2. **Async Processing**: All downloads handled via Celery tasks
3. **Service Layer**: Business logic separated from API endpoints
4. **Task Status Polling**: Clients poll for download completion
5. **Automatic Cleanup**: Scheduled tasks remove old files
6. **No API Authentication**: Direct access without API keys for simplified operation

### API Endpoints

**Article Operations**
- `POST /api/article/submit` - Create download task (no auth required)
- `GET /api/article/task/{task_id}/status` - Check task status
- `GET /api/article/task/{task_id}/result` - Get task result with HTML content
- `GET /api/file/{filename}` - Download completed file

### Important Configuration Files

- `.env` - Development environment variables
- `.env.prod` - Production environment template
- `cookies.json` - CSDN authentication cookies (create from example)
- `docker-compose.yml` - Development stack
- `docker-compose.prod.yml` - Production stack with Nginx/SSL

### Browser Integration

Userscripts in `userscripts/` provide browser integration:
- `unlock_vip.js` - Adds download buttons to CSDN pages
- `csdn_helper.js` - Additional CSDN utilities

### Testing Strategy

Tests focus on:
- Complete download flow (`test_complete_flow.py`)
- Thread pool operations (`test_thread_pool.py`)
- File cleanup (`test_cleanup.py`)
- Wenku downloads (`test_wenku_download.py`)

### Common Development Tasks

**Adding New Services**
1. Create service class in `app/services/`
2. Add API endpoints in `app/api/`
3. Create Celery tasks if needed in `app/tasks/`
4. Write comprehensive tests

**Debugging Download Issues**
1. Check cookies.json validity
2. Verify Celery worker is running
3. Check task logs in Flower dashboard
4. Test with different article types (blog vs wenku)

**Production Deployment**
1. Use Docker Compose production configuration
2. Configure SSL certificates (optional)
3. Set up monitoring with Flower
4. Configure log rotation

### Key Technical Decisions

1. **Cookie-based CSDN Auth**: Uses cookies.json for CSDN access instead of browser automation
2. **Async Downloads**: Celery handles all time-consuming operations
3. **File Cleanup**: Automatic removal prevents storage issues
4. **Multi-format Support**: Handles both blog articles and documents
5. **No API Authentication**: Removed to simplify deployment and usage
6. **No Result Caching**: Removed Redis caching for simplified architecture