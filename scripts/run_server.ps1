# PSADT AI Agent - PowerShell Server Runner
# This script helps start the PSADT AI Agent on Windows systems

param(
    [string]$Port = "5000",
    [string]$Host = "0.0.0.0",
    [string]$Environment = "production",
    [switch]$Help,
    [switch]$Executable
)

# Help message
if ($Help) {
    Write-Host @"
PSADT AI Agent - PowerShell Server Runner

SYNOPSIS
    .\run_server.ps1 [-Port <port>] [-Host <host>] [-Environment <env>] [-Executable] [-Help]

DESCRIPTION
    Starts the PSADT AI Agent backend service for generating PowerShell App Deployment Toolkit scripts.

PARAMETERS
    -Port <string>
        Port number to run the server on (default: 5000)

    -Host <string>
        Host address to bind to (default: 0.0.0.0)

    -Environment <string>
        Environment mode: development, production (default: production)

    -Executable
        Use the standalone executable instead of Flask development server

    -Help
        Show this help message

EXAMPLES
    .\run_server.ps1
        Start server on default port 5000

    .\run_server.ps1 -Port 8080 -Environment development
        Start development server on port 8080

    .\run_server.ps1 -Executable
        Use the standalone executable build

ENVIRONMENT VARIABLES
    Set these before running the script:

    Required:
    - API_KEY: Your API authentication key
    - OPENAI_API_KEY: Your OpenAI API key

    Optional:
    - LOG_FORMAT: 'structured' for JSON logs, 'human' for readable logs
    - DATABASE_URL: Database connection string (default: sqlite:///aipackager.db)

"@
    exit 0
}

# ASCII Art Banner
Write-Host @"
    ____  _____ ___    ____  ______   ___    ____   ___   ____  ____
   |    \|     |   |  /    ||      | /   \  /    | /  _] |    \|    |
   |  o  )   __| _   ||  o  ||      ||     ||   __||  [_  |  _  )  | |
   |   _/|  |_ |  |  ||     ||_|  |_||  O  ||  |  ||    | |  |  |  | |
   |  |  |   _]|  |  ||  _  |  |  |  |     ||  |_ ||   _| |  |  |  | |
   |  |  |  |  |  |  ||  |  |  |  |  |     ||     ||  |   |  |  |  | |
   |__|  |__|  |__|__||__|__|  |__|   \___/ |___,_||__|   |__|__|____|

   AI Agent for PowerShell App Deployment Toolkit Script Generation

"@ -ForegroundColor Cyan

# Check if running from correct directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

if (-not (Test-Path "$ProjectRoot\src\ai_psadt_agent")) {
    Write-Host "❌ Error: Please run this script from the project root directory" -ForegroundColor Red
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
    Write-Host "Expected: $ProjectRoot" -ForegroundColor Yellow
    exit 1
}

Set-Location $ProjectRoot

# Check environment variables
Write-Host "🔧 Checking environment configuration..." -ForegroundColor Yellow

$RequiredVars = @("API_KEY", "OPENAI_API_KEY")
$MissingVars = @()

foreach ($var in $RequiredVars) {
    if (-not [Environment]::GetEnvironmentVariable($var)) {
        $MissingVars += $var
    }
}

if ($MissingVars.Count -gt 0) {
    Write-Host "❌ Missing required environment variables:" -ForegroundColor Red
    foreach ($var in $MissingVars) {
        Write-Host "  - $var" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "💡 Set them using:" -ForegroundColor Yellow
    Write-Host "  `$env:API_KEY = 'your-api-key-here'" -ForegroundColor Cyan
    Write-Host "  `$env:OPENAI_API_KEY = 'your-openai-key-here'" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Or create a .env file in the project root." -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Environment variables configured" -ForegroundColor Green

# Set environment variables for Flask
$env:PORT = $Port
$env:HOST = $Host

if ($Environment -eq "development") {
    $env:FLASK_ENV = "development"
    $env:FLASK_DEBUG = "1"
}

# Check if using executable
if ($Executable) {
    $ExecutablePath = "$ProjectRoot\dist\psadt-agent.pyz"

    if (-not (Test-Path $ExecutablePath)) {
        Write-Host "❌ Executable not found: $ExecutablePath" -ForegroundColor Red
        Write-Host "💡 Build it first with: python scripts\build_executable.py" -ForegroundColor Yellow
        exit 1
    }

    Write-Host "🚀 Starting PSADT AI Agent (executable mode)..." -ForegroundColor Green
    Write-Host "📦 Using executable: $ExecutablePath" -ForegroundColor Cyan
    Write-Host "🌐 Server will be available at: http://${Host}:${Port}" -ForegroundColor Cyan
    Write-Host "📚 API Documentation: http://${Host}:${Port}/docs" -ForegroundColor Cyan
    Write-Host "📊 Metrics: http://${Host}:${Port}/metrics" -ForegroundColor Cyan
    Write-Host "💚 Health Check: http://${Host}:${Port}/health" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
    Write-Host ""

    try {
        python $ExecutablePath
    }
    catch {
        Write-Host "❌ Error starting executable: $_" -ForegroundColor Red
        exit 1
    }
}
else {
    # Check if virtual environment exists
    if (-not (Test-Path "$ProjectRoot\.venv")) {
        Write-Host "❌ Virtual environment not found" -ForegroundColor Red
        Write-Host "💡 Create it with: python -m venv .venv" -ForegroundColor Yellow
        Write-Host "💡 Then activate it with: .venv\Scripts\Activate.ps1" -ForegroundColor Yellow
        exit 1
    }

    # Check if dependencies are installed
    $RequirementsFile = "$ProjectRoot\requirements.txt"
    if (-not (Test-Path $RequirementsFile)) {
        Write-Host "❌ Requirements file not found: $RequirementsFile" -ForegroundColor Red
        exit 1
    }

    Write-Host "🚀 Starting PSADT AI Agent (development mode)..." -ForegroundColor Green
    Write-Host "🐍 Using Python Flask development server" -ForegroundColor Cyan
    Write-Host "🌐 Server will be available at: http://${Host}:${Port}" -ForegroundColor Cyan
    Write-Host "📚 API Documentation: http://${Host}:${Port}/docs" -ForegroundColor Cyan
    Write-Host "📊 Metrics: http://${Host}:${Port}/metrics" -ForegroundColor Cyan
    Write-Host "💚 Health Check: http://${Host}:${Port}/health" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
    Write-Host ""

    # Set Flask app
    $env:FLASK_APP = "src.ai_psadt_agent"

    try {
        if ($Environment -eq "development") {
            flask run --host=$Host --port=$Port --debug
        } else {
            flask run --host=$Host --port=$Port
        }
    }
    catch {
        Write-Host "❌ Error starting Flask server: $_" -ForegroundColor Red
        Write-Host "💡 Make sure you're in the virtual environment:" -ForegroundColor Yellow
        Write-Host "  .venv\Scripts\Activate.ps1" -ForegroundColor Cyan
        Write-Host "💡 And dependencies are installed:" -ForegroundColor Yellow
        Write-Host "  pip install -r requirements.txt" -ForegroundColor Cyan
        exit 1
    }
}
