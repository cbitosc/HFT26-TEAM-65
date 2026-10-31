# WildlifeAI Launcher Script
Write-Host "========================================================" -ForegroundColor Green
Write-Host " AI-Powered Wildlife Monitoring & Camera-Trap Analytics" -ForegroundColor Cyan
Write-Host " CBIT Hacktoberfest '26 - Team 65 (The Chosen One)" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""

Set-Location D:\HFT26-TEAM-65-main

# Open browser automatically after 1 second
Start-Process "http://127.0.0.1:8000"

# Launch FastAPI server using the D: drive virtual environment
& D:\HFT26-TEAM-65-main\.venv\Scripts\python.exe -m src.backend.main
