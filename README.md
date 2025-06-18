# PSADT AI Agent - Backend API

A Flask-based backend service that generates production-ready PowerShell App Deployment Toolkit (PSADT v3.9+) scripts from natural language descriptions.

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- SQLite 3
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd AIPackager_v2
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Initialize database:**
   ```bash
   alembic upgrade head
   ```

6. **Run the server:**
   ```bash
   python -m flask --app src.ai_psadt_agent run --debug
   ```

The API will be available at `http://localhost:5000`

## 🔑 API Authentication

### API Key Configuration

The service uses API key authentication. Configure your API key in the `.env` file:

```bash
API_KEY=your-secure-api-key-here
```

### API Key Rotation

For security best practices, rotate your API keys regularly:

#### 1. Generate New API Key
```bash
# Generate a cryptographically secure random key
python -c "import secrets; print('psadt-agent-' + secrets.token_urlsafe(32))"
```

#### 2. Update Environment Variables
```bash
# Update .env file
API_KEY=psadt-agent-new-secure-key-here

# For production deployments, update your secrets management:
# - GitHub Actions: Update repository secrets
# - Docker: Update environment variables
# - Kubernetes: Update secret manifests
```

#### 3. Restart Service
```bash
# Development
python -m flask --app src.ai_psadt_agent run

# Production (example with systemd)
sudo systemctl restart psadt-agent
```

#### 4. Update Client Applications
Update all client applications with the new API key:

```bash
# Example API call with new key
curl -X POST http://localhost:5000/v1/generate \
  -H "X-API-Key: psadt-agent-new-secure-key-here" \
  -H "Content-Type: application/json" \
  -d '{"installer_metadata": {...}}'
```

### Security Best Practices

- **Never commit API keys** to version control
- **Use different keys** for development, staging, and production
- **Rotate keys regularly** (recommended: monthly)
- **Monitor API usage** for suspicious activity
- **Use HTTPS** in production environments
- **Implement rate limiting** (already configured)

## 📖 API Documentation

### Core Endpoints

#### Health Check
```bash
GET /health
```

#### Generate PSADT Script
```bash
POST /v1/generate
Content-Type: application/json
X-API-Key: your-api-key

{
  "installer_metadata": {
    "name": "Adobe Reader",
    "version": "2023.008.20470",
    "vendor": "Adobe Inc.",
    "installer_type": "msi",
    "installer_path": "AdobeReader.msi",
    "silent_args": "/quiet",
    "architecture": "x64"
  },
  "user_notes": "Install for all users",
  "save_to_package": true
}
```

#### Validate PSADT Script
```bash
POST /v1/validate
Content-Type: application/json

{
  "script_content": "# Your PSADT script content here"
}
```

#### CRUD Operations for Packages
```bash
GET    /packages           # List all packages
POST   /packages           # Create new package
GET    /packages/{id}      # Get specific package
PUT    /packages/{id}      # Update package
DELETE /packages/{id}      # Delete package
```

### Rate Limits

- **Generation endpoint**: 100 requests per 10 minutes per IP
- **Validation endpoint**: 200 requests per 10 minutes per IP
- **General endpoints**: 1000 requests per day per IP

## 🛠 Development

### Project Structure

```
src/ai_psadt_agent/
├── api/                    # Flask blueprints & routes
│   ├── routes/
│   └── auth.py            # Authentication & rate limiting
├── services/              # Business logic & AI services
├── domain_models/         # SQLAlchemy & Pydantic models
├── infrastructure/        # Database & external integrations
└── cli/                   # Command-line interface
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/ai_psadt_agent --cov-report=html

# Run specific test file
pytest tests/test_api.py
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy --strict src/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 🐳 Deployment

### Docker

```bash
# Build image
docker build -t psadt-agent .

# Run container
docker run -p 5000:5000 --env-file .env psadt-agent
```

### Windows Executable

Generate a standalone executable for Windows:

```bash
# Install shiv
pip install shiv

# Build executable
python scripts/build_executable.py

# Run on Windows
./dist/psadt-agent.pyz
```

## 📊 Monitoring

### Metrics Endpoint

The service exposes Prometheus metrics at `/metrics`:

```bash
curl http://localhost:5000/metrics
```

Available metrics:
- Request counts by endpoint
- Response times
- Generation success/failure rates
- Database connection metrics

### Structured Logging

Configure structured JSON logs via environment variables:

```bash
LOG_FORMAT=structured  # or 'human' for development
```

Log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key for LLM | - | Yes |
| `API_KEY` | Service API key | - | Yes |
| `LLM_PROVIDER` | LLM provider | `openai` | No |
| `LOG_FORMAT` | Log format | `human` | No |
| `FLASK_ENV` | Flask environment | `production` | No |
| `DATABASE_URL` | Database connection | `sqlite:///aipackager.db` | No |

### LLM Provider Configuration

Currently supports OpenAI. Configure via environment variables:

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-key
```

## 🎯 Features

- ✅ **CRUD API** for package management
- ✅ **AI Script Generation** with RAG-enhanced prompts
- ✅ **Script Validation** with compliance checking
- ✅ **Rate Limiting** and authentication
- ✅ **SQLite Database** with migrations
- ✅ **Structured Logging** with Loguru
- ✅ **OpenAPI Documentation** at `/docs`
- ✅ **Prometheus Metrics** at `/metrics`
- ✅ **Windows Executable** packaging

## 🧪 Testing

The project includes comprehensive test coverage:

- **Unit tests** for all services and models
- **Integration tests** for API endpoints
- **Mutation testing** with mutmut
- **Security scanning** with Bandit

Run the full test suite:

```bash
# Standard tests
pytest

# Mutation testing
mutmut run

# Security scan
bandit -r src/
safety check
```

## 📋 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For questions and support:

- Create an issue in the GitHub repository
- Check the documentation at `/docs`
- Review the API examples in `examples/`

---

**Built with ❤️ for PowerShell App Deployment Toolkit automation**
