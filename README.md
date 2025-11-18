# FastAPI Production-Ready Project

A modern, production-ready FastAPI application with async SQLAlchemy, Redis, Docker, and comprehensive testing.

## 🚀 Features

- **Modern Tech Stack**: FastAPI, SQLAlchemy 2.0, Pydantic v2, Redis
- **Fully Async**: Complete async/await support throughout
- **Authentication & Authorization**: JWT-based auth with role-based access control
- **Database**: PostgreSQL with async SQLAlchemy ORM
- **Caching**: Redis for caching and session management
- **Migrations**: Alembic for database migrations
- **Testing**: Comprehensive test suite with pytest
- **Logging**: Structured logging with correlation IDs
- **Docker**: Full Docker Compose setup for development and production
- **API Documentation**: Auto-generated OpenAPI/Swagger docs
- **Type Safety**: Full type hints and Pydantic validation

## 📁 Project Structure

```
fastapi-production/
├── alembic/              # Database migrations
│   ├── versions/         # Migration files
│   └── env.py           # Alembic configuration
├── src/
│   ├── api/             # API endpoints
│   │   ├── dependencies/ # FastAPI dependencies
│   │   └── v1/          # API version 1
│   ├── core/            # Core functionality
│   │   ├── config.py    # Settings management
│   │   ├── database.py  # Database configuration
│   │   ├── redis.py     # Redis configuration
│   │   ├── security.py  # Security utilities
│   │   └── logging.py   # Logging configuration
│   ├── models/          # SQLAlchemy models
│   ├── repositories/    # Data access layer
│   ├── schemas/         # Pydantic schemas
│   ├── middleware/      # Custom middleware
│   └── main.py         # Application entry point
├── tests/               # Test suite
│   ├── conftest.py     # Test configuration
│   ├── test_auth.py    # Authentication tests
│   └── test_users.py   # User endpoint tests
├── docker-compose.yml   # Docker orchestration
├── Dockerfile          # Container configuration
├── requirements.txt    # Python dependencies
├── alembic.ini        # Alembic configuration
├── pytest.ini         # Pytest configuration
├── .env               # Environment variables
└── README.md          # Project documentation
```

## 🛠️ Tech Stack

- **Framework**: FastAPI (latest)
- **Database**: PostgreSQL + SQLAlchemy 2.0 (async)
- **Cache**: Redis
- **Authentication**: JWT (python-jose)
- **Validation**: Pydantic v2
- **Migrations**: Alembic
- **Testing**: Pytest + pytest-asyncio
- **Logging**: Structlog
- **Containerization**: Docker & Docker Compose

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.12+ (for local development)
- PostgreSQL (if running without Docker)
- Redis (if running without Docker)

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd fastapi-production
```

### 2. Setup Environment Variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Run with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

The application will be available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 4. Run Database Migrations

```bash
# With Docker
docker-compose exec app alembic upgrade head

# Without Docker
alembic upgrade head
```

### 5. Create Initial Admin User (Optional)

```bash
# Use the API to register a user, then update their role in the database
# Or create a management command for this
```

## 🏃 Local Development (Without Docker)

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup PostgreSQL and Redis

Make sure PostgreSQL and Redis are running locally and update `.env` with local connection strings.

### 4. Run Migrations

```bash
alembic upgrade head
```

### 5. Run the Application

```bash
# Development mode with auto-reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Or using the Python script
python -m src.main
```

## Makefile
### 1. Установить Poetry (если нет)
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. Установить зависимости
```bash
poetry install --with dev
```

### 3. Установить pre-commit хуки
```bash
poetry run pre-commit install
```

### 4. Проверить код
```bash
make lint
```

### 5. Форматировать код
```bash
make format
```

### 6. Запустить тесты
```bash
make test
```

### 7. Создать миграцию
```bash
make db-migration
```

### 8. Запустить приложение
```bash
make run
```

## 🧪 Testing

### Run All Tests

```bash
# With Docker
docker-compose exec app pytest

# Without Docker
pytest
```

### Run Specific Tests

```bash
# Run only authentication tests
pytest tests/test_auth.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run with verbose output
pytest -v
```

### Test Coverage

```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html  # On macOS
# or
xdg-open htmlcov/index.html  # On Linux
```

## 📚 API Documentation

### Authentication Endpoints

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout user
- `GET /api/v1/auth/me` - Get current user

### User Endpoints

- `GET /api/v1/users` - List users (admin only)
- `GET /api/v1/users/me` - Get current user profile
- `GET /api/v1/users/{id}` - Get user by ID
- `PUT /api/v1/users/me` - Update current user
- `PUT /api/v1/users/me/password` - Update password
- `DELETE /api/v1/users/me` - Delete account

### Post Endpoints

- `GET /api/v1/posts` - List posts
- `POST /api/v1/posts` - Create post
- `GET /api/v1/posts/{id}` - Get post
- `PUT /api/v1/posts/{id}` - Update post
- `DELETE /api/v1/posts/{id}` - Delete post
- `GET /api/v1/posts/featured` - Get featured posts
- `GET /api/v1/posts/popular` - Get popular posts

### Health Check

- `GET /health` - Basic health check
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe

## 🔧 Configuration

All configuration is managed through environment variables in `.env`:

```env
# Application
APP_NAME=FastAPI Production App
APP_VERSION=1.0.0
DEBUG=true
ENVIRONMENT=development

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=fastapi_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redis_password

# Security
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

## 📝 Database Migrations

### Create a New Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Create empty migration
alembic revision -m "Description of changes"
```

### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade one revision
alembic upgrade +1

# Downgrade one revision
alembic downgrade -1
```

### Check Migration Status

```bash
alembic current
alembic history
```

## 🔒 Security Features

- **Password Hashing**: Bcrypt with salt
- **JWT Tokens**: Access and refresh tokens
- **Role-Based Access**: User, Moderator, Admin, Super Admin
- **Rate Limiting**: Configurable per endpoint
- **CORS**: Configurable origins
- **SQL Injection Protection**: Via SQLAlchemy ORM
- **Input Validation**: Pydantic schemas
- **Secure Headers**: Security middleware

## 📊 Monitoring & Logging

- **Structured Logging**: JSON format in production
- **Correlation IDs**: Track requests across services
- **Health Checks**: Liveness and readiness probes
- **Metrics**: Ready for Prometheus integration
- **Error Tracking**: Ready for Sentry integration

## 🚢 Deployment

### Docker Production Build

```bash
# Build production image
docker build -t fastapi-app:latest .

# Run production container
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name fastapi-app \
  fastapi-app:latest
```

### Environment-Specific Settings

- **Development**: Debug mode, auto-reload, verbose logging
- **Staging**: Production-like with debug info
- **Production**: Optimized, minimal logging, security hardened

## 📈 Performance Optimization

- **Async Operations**: Full async/await support
- **Connection Pooling**: Database and Redis pools
- **Caching**: Redis caching layer
- **Pagination**: Efficient data loading
- **Lazy Loading**: Optimized ORM queries
- **Index Optimization**: Database indexes on key fields

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- Ilkhom Khafizov - Initial work

## 🙏 Acknowledgments

- FastAPI for the amazing framework
- SQLAlchemy for the powerful ORM
- All contributors and maintainers

## 📞 Support

For support, email support@yourcompany.com or open an issue in the repository.

---

Built with ❤️ using FastAPI