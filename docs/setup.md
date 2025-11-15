# Setup Instructions

## Prerequisites
- Python 3.11+
- Docker and Docker Compose
- PostgreSQL (optional if using Docker)
- Redis (optional if using Docker)

## Quick Start with Docker

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-financial-chatbot
```

2. Copy environment file:
```bash
cp .env.example .env
```

3. Start services:
```bash
docker-compose up -d
```

4. Run database migrations:
```bash
docker-compose exec backend alembic upgrade head
```

5. Access the applications:
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Admin Portal: http://localhost:8501

## Local Development Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements-dev.txt
```

3. Set up database:
```bash
# Start PostgreSQL and Redis (or use Docker)
docker-compose up -d postgres redis

# Run migrations
alembic upgrade head
```

4. Start the backend:
```bash
uvicorn backend.main:app --reload
```

5. Start the admin portal:
```bash
streamlit run frontend/admin-portal/app.py
```

## Configuration

Edit `.env` file to configure:
- Database connection
- OpenAI API key (optional)
- JWT secret key
- File upload settings
- Business rule limits

## Testing

Run tests:
```bash
pytest tests/
```

With coverage:
```bash
pytest --cov=backend tests/
```