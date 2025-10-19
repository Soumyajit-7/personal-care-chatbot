function Show-Menu {
    Clear-Host
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                                                            ║" -ForegroundColor Cyan
    Write-Host "║     Personal Care Chatbot - Docker Launcher                ║" -ForegroundColor Cyan
    Write-Host "║                                                            ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Choose an option:"
    Write-Host ""
    Write-Host "  1) Start FastAPI Server" -ForegroundColor Green
    Write-Host "  2) Start CLI Application (Interactive)" -ForegroundColor Green
    Write-Host "  3) View Logs" -ForegroundColor Yellow
    Write-Host "  4) Stop All Services" -ForegroundColor Red
    Write-Host "  5) Clean Everything (Remove volumes)" -ForegroundColor Red
    Write-Host "  6) Exit" -ForegroundColor Gray
    Write-Host ""
}

function Start-API {
    Write-Host "🚀 Starting FastAPI application..." -ForegroundColor Cyan
    docker-compose up -d postgres redis api
    Write-Host ""
    Write-Host "✅ FastAPI is running at http://localhost:8000" -ForegroundColor Green
    Write-Host "📖 API Docs: http://localhost:8000/docs" -ForegroundColor Green
    Write-Host ""
    Read-Host "Press Enter to continue"
}

function Start-CLI {
    Write-Host "🚀 Starting CLI application..." -ForegroundColor Cyan
    docker-compose up -d postgres redis
    Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    Write-Host ""
    Write-Host "Starting interactive CLI..." -ForegroundColor Green
    docker-compose --profile cli run --rm cli
}

function View-Logs {
    Write-Host "📊 Viewing logs (Ctrl+C to exit)..." -ForegroundColor Cyan
    docker-compose logs -f
}

function Stop-Services {
    Write-Host "🛑 Stopping all services..." -ForegroundColor Yellow
    docker-compose --profile cli down
    Write-Host "✅ All services stopped" -ForegroundColor Green
    Read-Host "Press Enter to continue"
}

function Clean-All {
    Write-Host "⚠️  WARNING: This will remove all containers, volumes, and data!" -ForegroundColor Red
    $confirm = Read-Host "Are you sure? (yes/no)"
    if ($confirm -eq "yes") {
        Write-Host "🧹 Cleaning everything..." -ForegroundColor Yellow
        docker-compose --profile cli down -v
        docker system prune -f
        Write-Host "✅ Cleanup complete" -ForegroundColor Green
    } else {
        Write-Host "❌ Cancelled" -ForegroundColor Red
    }
    Read-Host "Press Enter to continue"
}

# Main loop
while ($true) {
    Show-Menu
    $choice = Read-Host "Enter your choice [1-6]"
    
    switch ($choice) {
        "1" { Start-API }
        "2" { Start-CLI }
        "3" { View-Logs }
        "4" { Stop-Services }
        "5" { Clean-All }
        "6" { 
            Write-Host "Goodbye!" -ForegroundColor Cyan
            exit 
        }
        default {
            Write-Host "Invalid option. Please try again." -ForegroundColor Red
            Start-Sleep -Seconds 2
        }
    }
}
