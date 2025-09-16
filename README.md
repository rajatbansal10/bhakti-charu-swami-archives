# Veda Foundation — Bhakti Charu Swami Archives

A modern web application for managing and sharing spiritual content including audio, images, PDFs, and videos.

## Features

- **User Authentication**: Secure login with username/password or email OTP
- **Role-Based Access Control**: Different permission levels for viewers, uploaders, editors, and admins
- **Media Management**: Upload, organize, and manage various media types
- **Full-Text Search**: Powerful search functionality across all content
- **Responsive Design**: Works on desktop and mobile devices
- **Audit Logging**: Track all important actions in the system

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy, Pydantic v2
- **Database**: SQLite (development), PostgreSQL (production)
- **Storage**: S3-compatible object storage (e.g., AWS S3, MinIO, Ceph)
- **Frontend**: Jinja2 templates, HTMX, Tailwind CSS, Alpine.js
- **Containerization**: Docker

## Prerequisites

- Python 3.12+
- Docker and Docker Compose (for containerized deployment)
- S3-compatible storage (e.g., AWS S3, MinIO, Ceph)
- SMTP server for email notifications

## Getting Started

### 1. Clone the repository

```bash
git clone <repository-url>
cd veda-foundation-archives
```

### 2. Set up environment variables

Copy the example environment file and update the values:

```bash
cp .env.example .env
```

Edit the `.env` file with your configuration:

```env
# Application
APP_NAME="Veda Foundation — Bhakti Charu Swami Archives"
APP_ENV=dev
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///./local.db
# For production: postgresql+psycopg://user:password@localhost:5432/veda

# S3 Storage
S3_ENDPOINT_URL=https://your-s3-endpoint.com
S3_REGION=us-east-1
S3_BUCKET=veda-archives
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# Email
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASS=your-email-password
SMTP_FROM="Veda Foundation <noreply@vedafoundation.org>"

# Security
SESSION_SECRET=your-session-secret
```

### 3. Install dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Initialize the database

```bash
# Create and apply migrations
alembic upgrade head

# Create initial admin user
python -m app.scripts.create_admin
```

### 5. Run the development server

```bash
uvicorn app.main:app --reload
```

The application will be available at http://localhost:8000

## Deployment

### Docker Compose (Recommended for Production)

1. Update the `.env` file with your production settings
2. Run the following commands:

```bash
docker-compose build
docker-compose up -d
```

### Manual Deployment

1. Set up a PostgreSQL database
2. Configure a reverse proxy (Nginx/Apache) with SSL
3. Set up a process manager (e.g., systemd, Supervisor)
4. Configure your S3-compatible storage
5. Deploy the application using your preferred method (e.g., Git, CI/CD)

## Development

### Running Tests

```bash
pytest
```

### Code Style

This project uses:
- Black for code formatting
- isort for import sorting
- flake8 for linting

Run the following commands before committing:

```bash
black .
isort .
flake8
```

## Project Structure

```
.
├── alembic/                  # Database migrations
├── app/                      # Application code
│   ├── api/                  # API routes
│   ├── auth/                 # Authentication and authorization
│   ├── core/                 # Core functionality
│   ├── db/                   # Database configuration
│   ├── models/               # Database models
│   ├── schemas/              # Pydantic models
│   ├── services/             # Business logic
│   ├── static/               # Static files (CSS, JS, images)
│   ├── templates/            # Jinja2 templates
│   ├── utils/                # Utility functions
│   ├── config.py             # Application configuration
│   └── main.py               # FastAPI application
├── tests/                    # Test files
├── .env.example              # Example environment variables
├── .gitignore                # Git ignore file
├── alembic.ini               # Alembic configuration
├── docker-compose.yml         # Docker Compose configuration
├── Dockerfile                # Docker configuration
├── pyproject.toml            # Project metadata and dependencies
├── README.md                 # This file
└── requirements.txt          # Python dependencies
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Alembic](https://alembic.sqlalchemy.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [HTMX](https://htmx.org/)
