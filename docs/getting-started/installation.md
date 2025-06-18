# Installation

This guide walks you through installing and setting up the PSADT AI Agent on your system.

## Prerequisites

Before installing PSADT AI Agent, ensure you have the following prerequisites:

- **Python 3.12+** - Required for running the application
- **Git** - For cloning the repository
- **OpenAI API Key** - For AI script generation functionality
- **Virtual Environment Tool** - `venv` or similar for dependency isolation

### System Requirements

=== "Windows"

    - Windows 10/11 or Windows Server 2019+
    - PowerShell 5.1+ (for generated scripts)
    - 4GB RAM minimum, 8GB recommended
    - 2GB free disk space

=== "Linux"

    - Ubuntu 20.04+, CentOS 8+, or equivalent
    - 4GB RAM minimum, 8GB recommended
    - 2GB free disk space

=== "macOS"

    - macOS 11+ (Big Sur or later)
    - 4GB RAM minimum, 8GB recommended
    - 2GB free disk space

## Installation Methods

### Method 1: From Source (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/psadt-ai-agent/psadt-ai-agent.git
   cd psadt-ai-agent
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment:**

   === "Windows"
       ```cmd
       .venv\Scripts\activate
       ```

   === "Linux/macOS"
       ```bash
       source .venv/bin/activate
       ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Initialize the database:**
   ```bash
   alembic upgrade head
   ```

### Method 2: Windows Executable

For Windows users who prefer a standalone executable:

1. **Download the latest release:**
   - Visit the [Releases page](https://github.com/psadt-ai-agent/psadt-ai-agent/releases)
   - Download `psadt-agent.pyz` from the latest release

2. **Set up environment variables:**
   ```powershell
   $env:API_KEY = "your-secure-api-key"
   $env:OPENAI_API_KEY = "your-openai-key"
   ```

3. **Run the executable:**
   ```powershell
   python psadt-agent.pyz
   ```

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Required
API_KEY=your-secure-api-key-here
OPENAI_API_KEY=your-openai-api-key-here

# Optional
LLM_PROVIDER=openai
LOG_FORMAT=human
FLASK_ENV=production
DATABASE_URL=sqlite:///aipackager.db
PORT=5000
HOST=0.0.0.0
```

### API Key Generation

Generate a secure API key for your instance:

```bash
python -c "import secrets; print('psadt-agent-' + secrets.token_urlsafe(32))"
```

### OpenAI API Key

1. Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create a new API key
3. Copy the key and add it to your `.env` file

!!! warning "Security Note"
    Never commit API keys to version control. Always use environment variables or secure secret management systems.

## Verification

### 1. Start the Server

```bash
flask --app src.ai_psadt_agent run
```

### 2. Check Health Endpoint

```bash
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-06-17T08:00:00Z",
  "version": "1.0.0"
}
```

### 3. Test Script Generation

```bash
curl -X POST http://localhost:5000/v1/generate \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "installer_metadata": {
      "name": "Test App",
      "version": "1.0.0",
      "vendor": "Test Corp",
      "installer_type": "msi"
    }
  }'
```

## Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Check what's using port 5000
lsof -i :5000  # macOS/Linux
netstat -ano | findstr :5000  # Windows

# Use a different port
flask --app src.ai_psadt_agent run --port 8080
```

#### Missing Dependencies
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

#### Database Issues
```bash
# Reset database
rm aipackager.db
alembic upgrade head
```

#### Permission Errors (Windows)
```powershell
# Run as Administrator or adjust execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Getting Help

If you encounter issues:

1. Check the [FAQ](../about/support.md#frequently-asked-questions)
2. Review server logs for error messages
3. Visit the [Issues page](https://github.com/psadt-ai-agent/psadt-ai-agent/issues)
4. Join our [Discord community](https://discord.gg/psadt-ai-agent)

## Next Steps

- **[Quick Start Guide](quick-start.md)** - Generate your first PSADT script
- **[Configuration](configuration.md)** - Advanced configuration options
- **[API Overview](../user-guide/api-overview.md)** - Learn about the REST API
- **[Examples](../examples/basic-usage.md)** - See practical examples

---

*Installation complete!* 🎉 You're ready to start generating PSADT scripts with AI.
