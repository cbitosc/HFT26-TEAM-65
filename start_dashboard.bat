@echo off
title WildlifeAI - Camera-Trap Analytics Studio (TEAM-65)
echo ========================================================
echo  AI-Powered Wildlife Monitoring & Camera-Trap Analytics
echo  CBIT Hacktoberfest '26 - Team 65 (The Chosen One)
echo ========================================================
echo.
cd /d D:\HFT26-TEAM-65-main

echo Starting WildlifeAI Server on D: drive...
start "" http://127.0.0.1:8000
D:\HFT26-TEAM-65-main\.venv\Scripts\python.exe -m src.backend.main
pause
