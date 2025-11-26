# Run XIBE-CHAT CLI with the virtual environment Python
Set-Location $PSScriptRoot

# Use the Python from the virtual environment
if (Test-Path ".venv\Scripts\python.exe") {
    Write-Host "Running in virtual environment..." -ForegroundColor Green
    & .\.venv\Scripts\python.exe ai_cli.py
    exit $LASTEXITCODE
} else {
    Write-Host "Error: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please create a virtual environment first:" -ForegroundColor Yellow
    Write-Host "  python -m venv .venv" -ForegroundColor Cyan
    Write-Host "  .\.venv\Scripts\python.exe -m pip install -r requirements.txt" -ForegroundColor Cyan
    exit 1
}

