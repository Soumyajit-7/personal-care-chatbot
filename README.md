
# Personal Care Product Chatbot 🤖

A production-ready, AI-powered chatbot for personal care products with advanced web scraping capabilities, conversational memory, and multi-modal deployment options.


## 📋 Table of Contents

1. [Overview](#-overview)
2. [Features](#-features)
3. [Architecture](#-architecture)
4. [Prerequisites](#-prerequisites)
5. [Installation](#-installation)
6. [Configuration](#-configuration)
7. [Running the Application](#-running-the-application)
8. [Usage Guide](#-usage-guide)
9. [API Documentation](#-api-documentation)
10. [Project Structure](#-project-structure)
11. [Development](#-development)

---

## 🎯 Overview

The **Personal Care Product Chatbot** is an intelligent conversational AI system that helps users discover, compare, and learn about personal care products through natural language conversations.

### Core Capabilities

- **🔍 Smart Web Scraping**: Extracts product data (name, brand, price, ratings, reviews) from e-commerce websites
- **💬 Conversational AI**: Natural language queries powered by GROQ's Llama 4 Scout (17B parameters)
- **📊 Product Analysis**: Find best value, top-rated items, and budget recommendations
- **🔄 Session Persistence**: Resume conversations with full context retention
- **🚨 Smart Escalation**: Automatically redirects policy queries to human support
- **📈 Rich Insights**: Analyzes customer reviews, ratings, and product features

---

## ✨ Features

### 1. Intelligent Web Scraping
- Multi-page extraction (up to 50 products per session)
- Comprehensive data: name, brand, price, images, descriptions, reviews
- Customer reviews with individual ratings
- Aggregate ratings and review counts
- Robust error handling with fallback mechanisms

### 2. Conversational AI
- Context-aware responses with 20-message conversation history
- Multi-turn dialogues with memory
- Supports queries like:
  - "What lipsticks do you have?"
  - "Which is the cheapest?"
  - "Show me top-rated products"
  - "What do customers say about this?"

### 3. Agentic Architecture (LangGraph)

User Input → Escalation Check → URL Extraction → Scraping → Query Answering
                 ↓                                              ↓
            Escalation Node ← ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘

**5 Intelligent Nodes**:
- **Escalation Check**: Detects policy/offer queries
- **URL Extraction**: Identifies URLs in messages
- **Scraping Node**: Executes web scraping
- **Query Answering**: Uses knowledge base for responses
- **Escalation Node**: Provides support contact

### 4. Dual Interface Support

**REST API (FastAPI)**:
- RESTful endpoints
- Async request handling
- Swagger/OpenAPI docs at `/docs`

**CLI (Terminal)**:
- Interactive interface with colors
- Commands: `/help`, `/history`, `/load`, `/sessions`
- Session management

---

## 🏗️ Architecture

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | LangGraph 0.2.45 | Agentic state machine |
| **LLM** | GROQ (Llama 4 Scout 17B) | Natural language processing |
| **API** | FastAPI 0.115.0 | REST API server |
| **Database** | PostgreSQL 15 | Conversation & checkpoints |
| **Cache/PubSub** | Redis 7 | Real-time events |
| **Scraping** | Selenium + Chromium | Web data extraction |
| **Parsing** | BeautifulSoup4 | HTML processing |
| **Data** | Pandas 2.2.3 | CSV handling |
| **Container** | Docker + Compose | Deployment |

### System Flow

```
User → FastAPI/CLI → LangGraph → GROQ LLM
                         ↓
                  PostgreSQL (History)
                  Redis (Pub/Sub)
                  CSV Files (Products)
                  Selenium (Scraping)
```

---

## 📋 Prerequisites

### Required

1. **Docker Desktop** (v20.10+)
   - Download: https://www.docker.com/products/docker-desktop

2. **GROQ API Key** (Required!)
   - Sign up: https://console.groq.com
   - Free tier available

### System Requirements

- **OS**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+)
- **RAM**: 8 GB minimum (16 GB recommended)
- **Storage**: 5 GB free space
- **Network**: Internet connection

---

## 🚀 Installation

### Quick Start (5 minutes)


# 1. Clone repository or download ZIP
```
cd personal-care-chatbot
```
# 2. Create environment file

create .env file or copy from .env.example

# 3. Edit and configure .env file

## ⚙️ Configuration

### Environment Variables (.env)

```
# ============ DATABASE ============
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=chatbot_user
POSTGRES_PASSWORD=chatbot_pass
POSTGRES_DB=chatbot_db

# ============ REDIS ============
REDIS_HOST=redis
REDIS_PORT=6379

# ============ GROQ API (REQUIRED!) ============
GROQ_API_KEY=gsk_your_api_key_here

# ============ APPLICATION ============
APP_HOST=0.0.0.0
APP_PORT=8000
DATA_DIR=/app/data/csvs

# ============ BUSINESS ============
SUPPORT_CONTACT_NUMBER=+91-1800-XXX-XXXX
```

# 4. Build and start
```
docker-compose build
docker-compose up -d postgres redis api
```
# 5. Access
API: http://localhost:8000
Docs: http://localhost:8000/docs
# CLI: 
```
docker-compose --profile cli run --rm cli
```

### Key Configuration Notes

- **GROQ_API_KEY**: Get from https://console.groq.com (REQUIRED)
- **DATA_DIR**: CSV storage location (auto-created)
- **SUPPORT_CONTACT_NUMBER**: Shown during escalation



## 🎮 Running the Application

### Method 1: Using Scripts (Easiest)

**Windows**:
```
# Interactive menu
.\run.bat
# or
.\run.ps1

# Quick commands
.\quick-start.ps1 api   # Start API
.\quick-start.ps1 cli   # Start CLI
.\quick-start.ps1 stop  # Stop all
```

**Linux/Mac**:
```
chmod +x run.sh
./run.sh
```

### Method 2: Docker Compose

```
# Start API
docker-compose up -d postgres redis api

# Start CLI (interactive)
docker-compose --profile cli run --rm cli

# View logs
docker-compose logs -f api

# Stop all
docker-compose --profile cli down
```

### Method 3: Local Development

```
# Start services (Docker)
docker-compose up -d postgres redis

# Set environment
export POSTGRES_HOST=localhost
export REDIS_HOST=localhost
export GROQ_API_KEY=your_key

# Install dependencies
pip install -r requirements.txt

# Run API
python -m app.main

# Run CLI (separate terminal)
python -m app.cli
```

---

## 📖 Usage Guide

### FastAPI Interface

#### 1. Access API Documentation
```
http://localhost:8000/docs
```

#### 2. Chat Endpoint

```
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me lipsticks under 500 rupees"
  }'
```

**Response**:
```
{
  "response": "I don't have products loaded yet...",
  "session_id": "session_20251019073000_abc123",
  "user_id": "user_def456",
  "requires_human": false
}
```

#### 3. Scrape Products

```
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "https://www.myntra.com/personal-care?f=Categories%3ALipstick",
    "session_id": "session_20251019073000_abc123"
  }'
```

#### 4. Get History

```
curl "http://localhost:8000/history/session_20251019073000_abc123"
```

### CLI Interface

#### Starting CLI
```
docker-compose --profile cli run --rm cli
```

#### Available Commands

| Command | Description |
|---------|-------------|
| `/help` | Show help message |
| `/history` | View conversation history |
| `/clear` | Clear screen |
| `/new` | Start new conversation |
| `/load` | Load previous session |
| `/sessions` | List all sessions |
| `/status` | Show session info |
| `/exit` or `/quit` | Exit chatbot |

#### Example Conversation

```
You: /new
✅ New conversation started!

You: https://www.myntra.com/personal-care?f=Categories%3ALipstick
Bot: ✅ Successfully scraped 50 products...

You: What are the top 3 cheapest lipsticks?
Bot: Based on the data, here are the top 3:
1. Maybelline SuperStay - ₹349 (4.3/5, 1,245 reviews)
2. Lakme 9 to 5 - ₹399 (4.1/5, 856 reviews)
3. Sugar Cosmetics - ₹449 (4.5/5, 2,341 reviews)

You: What do customers say about Sugar?
Bot: Customers love it! Reviews highlight:
⭐⭐⭐⭐⭐ "Amazing staying power!"
⭐⭐⭐⭐⭐ "Doesn't dry lips"
Overall: 4.5/5 from 2,341 reviews

You: I want to return a product
Bot: For returns, please contact: +91-1800-XXX-XXXX
```

---

## 📡 API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. Health Check
```
GET /health
```
**Response**: `{ "status": "healthy" }`

#### 2. Root
```
GET /
```
Returns API information and available endpoints.

#### 3. Chat
```
POST /chat
```
**Body**:
```
{
  "message": "string (required)",
  "session_id": "string (optional)",
  "user_id": "string (optional)"
}
```

**Response**:
```
{
  "response": "string",
  "session_id": "string",
  "user_id": "string",
  "requires_human": "boolean",
  "contact_info": "string | null"
}
```

#### 4. History
```
GET /history/{session_id}?limit=50
```
Returns conversation history for a session.

---

## 📁 Project Structure

```
personal-care-chatbot/
│
├── 📄 docker-compose.yml          # Service orchestration
├── 📄 Dockerfile                  # Container definition
├── 📄 docker-entrypoint.py        # Startup script
├── 📄 requirements.txt            # Dependencies
├── 📄 .env                        # Environment variables
│
├── run.bat                        # Windows launcher
├── run.ps1                        # PowerShell launcher
├── quick-start.ps1                # Quick commands
│
├── 📦 app/
│   ├── main.py                    # FastAPI server
│   ├── cli.py                     # CLI interface
│   ├── config.py                  # Configuration
│   │
│   ├── graph/                     # LangGraph
│   │   ├── state.py               # State definition
│   │   ├── nodes.py               # 5 processing nodes
│   │   ├── graph.py               # Graph construction
│   │   └── prompts.py             # System prompts
│   │
│   ├── tools/                     # External tools
│   │   ├── scraper_tool.py        # Tool wrapper
│   │   └── scrape_general.py      # Scraping logic
│   │
│   ├── database/                  # Persistence
│   │   ├── postgres.py            # PostgreSQL ops
│   │   └── redis_client.py        # Redis pub/sub
│   │
│   ├── models/                    # Data models
│   │   └── schemas.py             # Pydantic models
│   │
│   └── utils/                     # Utilities
│       ├── session.py             # ID generation
│       ├── csv_handler.py         # Knowledge base
│       
│
└── 📂 data/csvs/                  # Product data storage
```

### Key Components

**Core Application**:
- `main.py`: FastAPI with chat/history/health endpoints
- `cli.py`: Interactive terminal with colors and commands
- `config.py`: Centralized settings with Pydantic

**LangGraph Nodes** (app/graph/nodes.py):
1. `check_escalation_node`: Detects policy queries
2. `url_extraction_node`: Extracts URLs
3. `scraping_node`: Executes scraping
4. `query_answering_node`: Answers from knowledge base
5. `escalation_node`: Provides support contact

**Data Layer**:
- `postgres.py`: Stores conversations and checkpoints
- `redis_client.py`: Pub/sub and caching
- `csv_handler.py`: Product search and filtering

**Tools**:
- `scraper_tool.py`: LangChain tool decorator
- `scrape_general.py`: Selenium-based scraping with review extraction

---

## 🧪 Development

### Local Setup

```
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start services
docker-compose up -d postgres redis

# 4. Set environment
export POSTGRES_HOST=localhost
export REDIS_HOST=localhost
export GROQ_API_KEY=your_key

# 5. Run application
python -m app.main  # API
python -m app.cli   # CLI
```

### Adding Features

#### New Graph Node
```
# app/graph/nodes.py
def my_node(state: AgentState) -> AgentState:
    # Process state
    return state

# app/graph/graph.py
workflow.add_node("my_node", nodes.my_node)
workflow.add_edge("previous_node", "my_node")
```

#### New API Endpoint
```
# app/main.py
@app.get("/my-endpoint")
async def my_endpoint():
    return {"data": "value"}
```

#### New CLI Command
```
# app/cli.py
elif command == '/mycommand':
    do_something()
    continue
```

### Database Access

```
# PostgreSQL
docker exec -it chatbot_postgres psql -U chatbot_user -d chatbot_db

# Redis
docker exec -it chatbot_redis redis-cli
```

### Viewing Logs

```
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f postgres
```

---

## 🎯 Common Use Cases

### 1. Product Discovery
```
User: "Show me all lipsticks"
Bot: "We have 50 lipsticks from brands including Maybelline, Lakme, Sugar..."
```

### 2. Price Comparison
```
User: "Which lipstick is cheapest?"
Bot: "Maybelline SuperStay at ₹349 (4.3/5 rating)"
```

### 3. Rating-Based Search
```
User: "Show me top-rated products"
Bot: [Lists products sorted by rating]
```

### 4. Review Analysis
```
User: "What do customers say about this?"
Bot: [Provides review summary and ratings]
```

### 5. Support Escalation
```
User: "I want a refund"
Bot: "For refunds, contact: +91-1800-XXX-XXXX"
```

---

## 🔍 How It Works

### 1. User sends message
↓
### 2. Message saved to PostgreSQL
↓
### 3. Load last 20 messages (context)
↓
### 4. LangGraph processes:
   - Check for escalation keywords
   - Extract URL if present
   - Scrape if URL found
   - Query CSV knowledge base
   - Generate response with GROQ
↓
### 5. Save checkpoint (last 10 messages)
↓
### 6. Publish event to Redis
↓
### 7. Return response to user

### Data Storage

- **Conversations**: PostgreSQL `conversations` table
- **Checkpoints**: PostgreSQL `checkpoints` table (last 10 messages)
- **Products**: CSV files in `data/csvs/`
- **Sessions**: Redis cache for quick access
- **Events**: Redis pub/sub for real-time updates


