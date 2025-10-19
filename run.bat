@echo off
REM run.bat - Windows version

:menu
cls
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║     Personal Care Chatbot - Docker Launcher                ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo Choose an option:
echo.
echo   1) Start FastAPI Server
echo   2) Start CLI Application (Interactive)
echo   3) View Logs
echo   4) Stop All Services
echo   5) Clean Everything (Remove volumes)
echo   6) Exit
echo.
set /p choice="Enter your choice [1-6]: "

if "%choice%"=="1" goto start_api
if "%choice%"=="2" goto start_cli
if "%choice%"=="3" goto view_logs
if "%choice%"=="4" goto stop_services
if "%choice%"=="5" goto clean_all
if "%choice%"=="6" goto exit
goto menu

:start_api
cls
echo 🚀 Starting FastAPI application...
docker-compose up -d postgres redis api
echo.
echo ✅ FastAPI is running at http://localhost:8000
echo 📖 API Docs: http://localhost:8000/docs
echo.
pause
goto menu

:start_cli
cls
echo 🚀 Starting CLI application...
docker-compose up -d postgres redis
echo ⏳ Waiting for services to be ready...
timeout /t 5 /nobreak >nul
echo.
echo Starting interactive CLI...
docker-compose --profile cli run --rm cli
goto menu

:view_logs
cls
echo 📊 Viewing logs (Ctrl+C to exit)...
docker-compose logs -f
goto menu

:stop_services
cls
echo 🛑 Stopping all services...
docker-compose --profile cli down
echo ✅ All services stopped
pause
goto menu

:clean_all
cls
echo ⚠️  WARNING: This will remove all containers, volumes, and data!
set /p confirm="Are you sure? (yes/no): "
if /i "%confirm%"=="yes" (
    echo 🧹 Cleaning everything...
    docker-compose --profile cli down -v
    docker system prune -f
    echo ✅ Cleanup complete
) else (
    echo ❌ Cancelled
)
pause
goto menu

:exit
echo Goodbye!
exit /b 0
