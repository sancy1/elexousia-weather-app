#!/usr/bin/env pwsh
# Elexousia Weather API - Complete Installation Script for Windows

param(
    [switch]$SkipEnvCheck,
    [switch]$SkipVenv
)

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  ELEXOUSIA WEATHER API - COMPLETE INSTALLATION" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Python installation
if (-not $SkipEnvCheck) {
    Write-Host "[1/7] Checking Python installation..." -ForegroundColor Yellow
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "      ✓ $pythonVersion" -ForegroundColor Green
        
        # Check Python version is 3.12+
        if ($pythonVersion -match "Python 3\.(\d+)") {
            $minorVersion = [int]$matches[1]
            if ($minorVersion -lt 12) {
                Write-Host "      ⚠ Python 3.12+ recommended (found $pythonVersion)" -ForegroundColor Yellow
            }
        }
    }
    catch {
        Write-Host "      ✗ Python not found! Please install Python 3.12+" -ForegroundColor Red
        exit 1
    }
    
    # Check pip
    Write-Host "[2/7] Checking pip..." -ForegroundColor Yellow
    try {
        $pipVersion = pip --version 2>&1
        Write-Host "      ✓ $pipVersion" -ForegroundColor Green
    }
    catch {
        Write-Host "      ✗ pip not found!" -ForegroundColor Red
        exit 1
    }
}

# Step 2: Create virtual environment
if (-not $SkipVenv) {
    Write-Host "[3/7] Creating virtual environment..." -ForegroundColor Yellow
    if (Test-Path "venv") {
        Write-Host "      ⚠ Virtual environment already exists. Removing..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force "venv"
    }
    python -m venv venv
    Write-Host "      ✓ Virtual environment created" -ForegroundColor Green
}

# Step 3: Activate virtual environment
Write-Host "[4/7] Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1
if (-not $?) {
    Write-Host "      ✗ Failed to activate virtual environment" -ForegroundColor Red
    Write-Host "      Try running: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    exit 1
}
Write-Host "      ✓ Virtual environment activated" -ForegroundColor Green

# Step 4: Upgrade pip
Write-Host "[5/7] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip
Write-Host "      ✓ pip upgraded" -ForegroundColor Green

# Step 5: Install dependencies
Write-Host "[6/7] Installing dependencies (this may take a few minutes)..." -ForegroundColor Yellow

# Install base requirements first
Write-Host "      Installing base requirements..." -ForegroundColor Gray
pip install -r requirements/base.txt

# Install dev requirements (includes testing tools)
Write-Host "      Installing development requirements..." -ForegroundColor Gray
pip install -r requirements/dev.txt

Write-Host "      ✓ All dependencies installed" -ForegroundColor Green

# Step 6: Check critical packages
Write-Host "[7/7] Verifying critical packages..." -ForegroundColor Yellow

$criticalPackages = @(
    "fastapi",
    "uvicorn",
    "psycopg2-binary",
    "langchain-ollama",
    "ollama",
    "pytest"
)

$allOk = $true
foreach ($package in $criticalPackages) {
    $check = pip show $package 2>$null
    if ($check) {
        $version = ($check | Select-String "Version:").ToString().Replace("Version: ", "")
        Write-Host "      ✓ $package $version" -ForegroundColor Green
    } else {
        Write-Host "      ✗ $package NOT INSTALLED" -ForegroundColor Red
        $allOk = $false
    }
}

if (-not $allOk) {
    Write-Host ""
    Write-Host "      Some packages failed to install. Try running:" -ForegroundColor Yellow
    Write-Host "      pip install -r requirements/base.txt --no-cache-dir" -ForegroundColor Gray
}

# Step 7: Check .env file
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  ENVIRONMENT CONFIGURATION" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan

if (Test-Path ".env") {
    Write-Host "  ✓ .env file found" -ForegroundColor Green
    
    # Check required variables
    $envContent = Get-Content ".env" -Raw
    $hasDbUrl = $envContent -match "DATABASE_URL="
    $hasWeatherKey = $envContent -match "WEATHER_API_KEY="
    $hasSecretKey = $envContent -match "SECRET_KEY="
    
    if (-not $hasDbUrl) {
        Write-Host "  ⚠ WARNING: DATABASE_URL not set in .env" -ForegroundColor Yellow
    }
    if (-not $hasWeatherKey) {
        Write-Host "  ⚠ WARNING: WEATHER_API_KEY not set in .env" -ForegroundColor Yellow
    }
    if (-not $hasSecretKey) {
        Write-Host "  ⚠ WARNING: SECRET_KEY not set in .env" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠ .env file not found" -ForegroundColor Yellow
    Write-Host "  Copying .env.example to .env..." -ForegroundColor Gray
    Copy-Item ".env.example" ".env"
    Write-Host "  ✓ .env file created. Please edit with your credentials." -ForegroundColor Green
}

# Step 8: Check Ollama (optional)
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  OLLAMA STATUS (Optional)" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan

try {
    $ollamaCheck = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 2
    if ($ollamaCheck.StatusCode -eq 200) {
        Write-Host "  ✓ Ollama is running" -ForegroundColor Green
        
        # Check for required models
        $ollamaModels = $ollamaCheck.Content | ConvertFrom-Json
        $hasLlama = $false
        $hasEmbed = $false
        
        foreach ($model in $ollamaModels.models) {
            if ($model.name -like "llama3.2*") { $hasLlama = $true }
            if ($model.name -like "mxbai-embed-large*") { $hasEmbed = $true }
        }
        
        if (-not $hasLlama) {
            Write-Host "  ⚠ WARNING: llama3.2 model not found. Run: ollama pull llama3.2" -ForegroundColor Yellow
        }
        if (-not $hasEmbed) {
            Write-Host "  ⚠ WARNING: mxbai-embed-large model not found. Run: ollama pull mxbai-embed-large" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "  ⚠ Ollama is not running (optional - for local LLM)" -ForegroundColor Yellow
    Write-Host "    To use Ollama: Run 'ollama serve' in a separate terminal" -ForegroundColor Gray
}

# Step 9: Summary
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  INSTALLATION COMPLETE!" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "  To start the API server:" -ForegroundColor Cyan
Write-Host "    1. Activate environment: .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "    2. Run the server: python run.py" -ForegroundColor White
Write-Host "    3. Or use the start script: .\start.ps1" -ForegroundColor White
Write-Host ""
Write-Host "  API will be available at:" -ForegroundColor Cyan
Write-Host "    http://localhost:8000" -ForegroundColor White
Write-Host "    Swagger UI: http://localhost:8000/api/docs" -ForegroundColor White
Write-Host "    ReDoc: http://localhost:8000/api/redoc" -ForegroundColor White
Write-Host ""
Write-Host "  Quick test:" -ForegroundColor Cyan
Write-Host "    curl http://localhost:8000/api/health" -ForegroundColor White
Write-Host ""