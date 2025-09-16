# Veda Foundation — Bhakti Charu Swami Archives

A modern web application for managing and sharing spiritual content including audio, images, PDFs, and videos.

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL (recommended) or SQLite
- Node.js 18+ (for frontend assets)
- Redis (for caching and background tasks)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd veda-foundation-archives

# Create and activate virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and update it:

```bash
# Copy example config
cp .env.example .env
```

Edit `.env` with your settings:

```ini
# App Settings
APP_ENV=development
SECRET_KEY=your-secret-key

# Database (choose one)
DATABASE_URL=sqlite+aiosqlite:///./local.db  # For development
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost/veda_archives  # For production

# Redis
REDIS_URL=redis://localhost:6379/0

# Storage (S3 or local)
STORAGE_TYPE=local  # or 's3'
LOCAL_STORAGE_PATH=./storage
# S3_* settings required if using S3

# Email (required for password reset)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASS=your-password
SMTP_FROM="Veda Foundation <noreply@vedafoundation.org>"
```

### 3. Database Setup

#### Option A: SQLite (Development)
```bash
# No additional setup needed for SQLite
```

#### Option B: PostgreSQL (Production)
1. Install PostgreSQL
2. Create database and user:
   ```sql
   CREATE DATABASE veda_archives;
   CREATE USER veda_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE veda_archives TO veda_user;
   ```

### 4. Run Migrations

```bash
# Initialize Alembic (first time only)
alembic init -t async alembic

# Edit alembic.ini and alembic/env.py as shown below
```

In `alembic.ini`:
```ini
sqlalchemy.url = postgresql+asyncpg://user:pass@localhost/veda_archives
# or for SQLite:
# sqlalchemy.url = sqlite+aiosqlite:///./local.db
```

In `alembic/env.py`:
```python
from app.models import Base
target_metadata = Base.metadata
```

Then run migrations:
```bash
alembic upgrade head
```

### 5. Create Admin User

```bash
python -m app.scripts.create_admin
```

### 6. Start Development Server

```bash
uvicorn app.main:app --reload
```

Access the application at http://localhost:8000

## 🛠 Project Structure

```
.
├── app/                      # Application code
│   ├── api/                  # API endpoints
│   ├── core/                 # Core functionality
│   ├── db/                   # Database configuration
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic models
│   ├── services/             # Business logic
│   ├── static/               # Static files
│   ├── templates/            # Jinja2 templates
│   └── utils/                # Utility functions
├── alembic/                  # Database migrations
├── tests/                    # Test files
├── .env.example              # Example environment config
└── requirements.txt          # Python dependencies
```

## 🧪 Testing

### Running Tests

Run the full test suite with coverage:

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests with coverage
pytest --cov=app --cov-report=term-missing

# Run a specific test file
pytest tests/test_models/test_user.py -v

# Run tests with coverage report in HTML
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in your browser
```

### Test Organization

- Unit tests are in `tests/unit/`
- Integration tests are in `tests/integration/`
- End-to-end tests are in `tests/e2e/`
- Fixtures and configuration are in `tests/conftest.py`

### Writing Tests

- Use descriptive test function names starting with `test_`
- Group related tests in classes
- Use fixtures for common test data
- Mock external services
- Follow the Arrange-Act-Assert pattern

### Code Quality

Run code quality checks:

```bash
# Format code with Black
black .

# Sort imports with isort
isort .

# Check for style issues with flake8
flake8

# Run type checking with mypy
mypy .

# Check for security issues with bandit
bandit -r app/
```

## 🚀 Deployment

### Production with Docker

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Deployment

1. Set up a production-ready WSGI server (Uvicorn + Gunicorn)
2. Configure Nginx as reverse proxy
3. Set up process manager (systemd/PM2)
4. Enable HTTPS with Let's Encrypt

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Alembic](https://alembic.sqlalchemy.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [HTMX](https://htmx.org/)
