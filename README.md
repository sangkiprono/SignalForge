# SignalForge API

A high-performance REST API for creating, distributing, tracking, and analyzing trading signals across Forex, Crypto, Stocks, Indices, and Commodities markets.

## Features

- JWT Authentication with role-based access (Admin, Trader, Client)
- Full Signal CRUD with automatic Risk/Reward calculation
- TradingView Webhook integration
- Real-time WebSocket notifications
- Telegram alerts on signal events
- Signal history tracking
- Performance analytics (win rate, profit factor, RR)
- API Key management
- Subscription tiers (Free, Premium, Enterprise)
- Admin dashboard endpoints

## Tech Stack

- **FastAPI** - Web framework
- **PostgreSQL** - Database
- **SQLAlchemy** - ORM (async)
- **Alembic** - Database migrations
- **Redis** - (Phase 4 caching)
- **JWT** - Authentication
- **Telegram Bot API** - Notifications
- **WebSockets** - Real-time feed

## Setup

### 1. Clone the repo

git clone https://github.com/sangkiprono/SignalForge.git
cd SignalForge

### 2. Create virtual environment

python -m venv venv
venv\Scripts\activate

### 3. Install dependencies

pip install -r requirements.txt

### 4. Configure environment

Copy .env.example to .env and fill in your values:

DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/signalforge
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
WEBHOOK_SECRET=your-webhook-secret
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-chat-id

### 5. Run migrations

python -m alembic upgrade head

### 6. Start the server

python -m uvicorn app.main:app --reload

## API Documentation

Once running, visit:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## API Endpoints

### Authentication
- POST /auth/register
- POST /auth/login
- GET /auth/me
- PUT /auth/me

### Signals
- POST /signals/
- GET /signals/
- GET /signals/active
- GET /signals/{id}
- GET /signals/{id}/history
- PUT /signals/{id}
- DELETE /signals/{id}

### Webhooks
- POST /webhooks/tradingview

### Analytics
- GET /analytics/overview
- GET /analytics/by-market
- GET /analytics/by-symbol
- GET /analytics/win-rate-by-market

### API Keys
- POST /api-keys/
- GET /api-keys/
- DELETE /api-keys/{id}

### Subscriptions
- GET /subscriptions/me
- POST /subscriptions/upgrade
- GET /subscriptions/all (Admin only)

### Admin
- GET /admin/stats
- GET /admin/users
- PUT /admin/users/{id}/role
- PUT /admin/users/{id}/toggle
- GET /admin/signals
- DELETE /admin/signals/{id}

### WebSocket
- WS /ws/signals

## WebSocket Usage

Connect to ws://localhost:8000/ws/signals?token=YOUR_JWT_TOKEN

Messages received:
- new_signal: broadcast when a signal is created
- signal_update: broadcast when signal status changes

## TradingView Webhook

Send POST to /webhooks/tradingview with header x-webhook-secret

Payload:
{
  "symbol": "EURUSD",
  "market": "forex",
  "direction": "buy",
  "entry_price": 1.0850,
  "stop_loss": 1.0800,
  "take_profit": 1.0950,
  "title": "Optional title",
  "description": "Optional description"
}

## License

MIT
