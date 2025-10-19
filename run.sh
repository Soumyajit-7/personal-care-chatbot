#!/bin/bash

set -e

function show_menu() {
    clear
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║     Personal Care Chatbot - Docker Launcher                ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Choose an option:"
    echo ""
    echo "  1) Start FastAPI Server"
    echo "  2) Start CLI Application (Interactive)"
    echo "  3) View Logs"
    echo "  4) Stop All Services"
    echo "  5) Clean Everything (Remove volumes)"
    echo "  6) Exit"
    echo ""
    read -p "Enter your choice [1-6]: " choice
}

function start_api() {
    echo "🚀 Starting FastAPI application..."
    docker-compose up -d postgres redis api
    echo ""
    echo "✅ FastAPI is running at http://localhost:8000"
    echo "📖 API Docs: http://localhost:8000/docs"
    echo ""
    read -p "Press Enter to continue..."
}

function start_cli() {
    echo "🚀 Starting CLI application..."
    docker-compose up -d postgres redis
    echo "⏳ Waiting for services to be ready..."
    sleep 5
    echo ""
    echo "Starting interactive CLI..."
    docker-compose --profile cli run --rm cli
}

function view_logs() {
    echo "📊 Viewing logs (Ctrl+C to exit)..."
    docker-compose logs -f
}

function stop_services() {
    echo "🛑 Stopping all services..."
    docker-compose --profile cli down
    echo "✅ All services stopped"
    read -p "Press Enter to continue..."
}

function clean_all() {
    echo "⚠️  WARNING: This will remove all containers, volumes, and data!"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" == "yes" ]; then
        echo "🧹 Cleaning everything..."
        docker-compose --profile cli down -v
        docker system prune -f
        echo "✅ Cleanup complete"
    else
        echo "❌ Cancelled"
    fi
    read -p "Press Enter to continue..."
}

# Main loop
while true; do
    show_menu
    case $choice in
        1)
            start_api
            ;;
        2)
            start_cli
            ;;
        3)
            view_logs
            ;;
        4)
            stop_services
            ;;
        5)
            clean_all
            ;;
        6)
            echo "Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid option. Please try again."
            sleep 2
            ;;
    esac
done
