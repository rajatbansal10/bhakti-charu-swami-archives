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

#### Windows (PowerShell)
```powershell
# Copy the example environment file
Copy-Item .env.example .env

# Edit the .env file with your configuration
notepad .env
```

#### Linux/macOS
```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your configuration
nano .env  # or use your preferred text editor
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

### 3. Install Dependencies

#### Windows (PowerShell)
```powershell
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
.\\.venv\\Scripts\\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

#### Linux/macOS
```bash
# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Initialize the Database

#### Windows (PowerShell)
```powershell
# Apply database migrations
alembic upgrade head

# Create initial admin user
python -m app.scripts.create_admin
```

#### Linux/macOS
```bash
# Apply database migrations
alembic upgrade head

# Create initial admin user
python3 -m app.scripts.create_admin
```

### 5. Run the Development Server

#### Windows (PowerShell)
```powershell
# Make sure your virtual environment is activated
.\\.venv\\Scripts\\Activate.ps1

# Run the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Linux/macOS
```bash
# Make sure your virtual environment is activated
source .venv/bin/activate

# Run the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at:
- http://localhost:8000 (main application)
- http://localhost:8000/docs (API documentation)
- http://localhost:8000/admin (Admin interface)

### Common Issues and Solutions

#### Port Already in Use
If you get an error that port 8000 is in use, you can:
1. Stop the existing process using port 8000:
   ```bash
   # Linux/macOS
   sudo lsof -i :8000
   kill -9 <PID>
   
   # Windows
   netstat -ano | findstr :8000
   taskkill /PID <PID> /F
   ```
2. Or run the server on a different port:
   ```bash
   uvicorn app.main:app --reload --port 8001
   ```

#### Missing Dependencies
If you encounter missing module errors, make sure to:
1. Activate your virtual environment
2. Install all requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. For Windows-specific dependencies, you might need:
   ```powershell
   pip install python-magic-bin
   ```

#### Database Issues
If you have database connection problems:
1. Make sure your database server is running
2. Verify the connection string in `.env`
3. Try recrecing the database:
   ```bash
   # Delete the database file (SQLite)
   rm instance/local.db
   
   # Recreate and apply migrations
   alembic upgrade head
   ```

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
