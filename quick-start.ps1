param(
    [Parameter(Position=0)]
    [ValidateSet("api", "cli", "stop", "clean", "logs")]
    [string]$Action = "help"
)

switch ($Action) {
    "api" {
        Write-Host "🚀 Starting FastAPI..." -ForegroundColor Cyan
        docker-compose up -d postgres redis api
        Write-Host "✅ Running at http://localhost:8000" -ForegroundColor Green
    }
    "cli" {
        Write-Host "🚀 Starting CLI..." -ForegroundColor Cyan
        docker-compose up -d postgres redis
        Start-Sleep -Seconds 5
        docker-compose --profile cli run --rm cli
    }
    "stop" {
        Write-Host "🛑 Stopping services..." -ForegroundColor Yellow
        docker-compose --profile cli down
    }
    "clean" {
        Write-Host "🧹 Cleaning..." -ForegroundColor Yellow
        docker-compose --profile cli down -v
        docker system prune -f
    }
    "logs" {
        docker-compose logs -f
    }
    default {
        Write-Host "Personal Care Chatbot - Docker Commands" -ForegroundColor Cyan
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Usage: .\quick-start.ps1 <command>" -ForegroundColor Green
        Write-Host ""
        Write-Host "Commands:"
        Write-Host "  api    - Start FastAPI server"
        Write-Host "  cli    - Start CLI application"
        Write-Host "  stop   - Stop all services"
        Write-Host "  logs   - View logs"
        Write-Host "  clean  - Remove everything"
        Write-Host ""
        Write-Host "Examples:"
        Write-Host "  .\quick-start.ps1 api"
        Write-Host "  .\quick-start.ps1 cli"
    }
}
