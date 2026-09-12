# Child Safety Platform - Backend

## Project Overview
The Child Safety Platform backend is designed to provide secure, efficient, and scalable services for managing child safety reports, incidents, and cases. It integrates closely with an AI server for content analysis and threat evaluation.

## Tech Stack Summary
- **Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL (SQLAlchemy async)
- **Cache / PubSub**: Redis
- **Authentication**: JWT Bearer Tokens
- **AI Integration**: HTTPX async client communicating with AI microservice

## Setup Instructions

### Docker Setup
1. Ensure Docker and Docker Compose are installed.
2. Run `docker-compose up -d --build` (assuming docker-compose.yml exists in the root).
3. The backend API will be available at `http://localhost:8000`.

### Local Development
1. Install Python 3.11.
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Configure your environment variables in `.env`.
6. Start the development server using the local runner: `python run_local_dev.py` (which uses SQLite by default) or standard uvicorn: `uvicorn main:app --reload`.

## Environment Variables
- `APP_NAME`: Name of the application.
- `DEBUG`: Enable/disable debug mode (True/False).
- `DATABASE_URL`: Database connection string.
- `REDIS_URL`: Redis connection URL.
- `JWT_SECRET_KEY`: Secret key for token signing.
- `AI_SERVER_URL`: URL of the AI analysis server.
- `CORS_ORIGINS`: Allowed origins list for CORS middleware.

## API Endpoint Overview
- **`/api/v1/health`**: System health check.
- **`/api/v1/auth`**: User registration, login, and token refresh.
- **`/api/v1/reports`**: Submit and manage child safety reports.
- **`/api/v1/incidents`**: Fetch and manage categorized safety incidents.
- **`/api/v1/cases`**: Comprehensive case management and assignments.

## Architecture Notes
- The backend relies on async operations for all DB and HTTP requests.
- Real-time updates and emergency notifications are broadcast via WebSocket manager relying on Redis Pub/Sub.
- AI server fallback: The backend continues functioning gracefully even if the AI server is unavailable.
