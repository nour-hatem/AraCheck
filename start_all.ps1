Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "       Starting AraCheck Application      " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$baseDir = $PSScriptRoot

Write-Host "1. Starting FastAPI Backend Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList `
    "-NoExit", `
    "-Command", `
    "cd '$baseDir'; " + `
    "echo 'Installing Backend Requirements...'; " + `
    "pip install -r requirements.txt; " + `
    "echo 'Starting Server...'; " + `
    "uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload" `
    -WindowStyle Normal

Write-Host "2. Starting Next.js Frontend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList `
    "-NoExit", `
    "-Command", `
    "cd '$baseDir\frontend'; " + `
    "echo 'Installing Frontend Dependencies...'; " + `
    "npm install; " + `
    "echo 'Starting Frontend...'; " + `
    "npm run dev" `
    -WindowStyle Normal

Write-Host "==========================================" -ForegroundColor Green
Write-Host " All services are starting in new windows." -ForegroundColor Green
Write-Host " - Backend API: http://localhost:8000/docs" -ForegroundColor Green
Write-Host " - Frontend UI: http://localhost:3000"      -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
