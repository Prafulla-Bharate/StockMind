# StockMind Backend - Complete Architecture & Flow Documentation

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [Directory Structure](#directory-structure)
4. [Core Configuration](#core-configuration)
5. [Database Models](#database-models)
6. [API Architecture](#api-architecture)
7. [Real-time WebSocket Flow](#real-time-websocket-flow)
8. [Celery Task Scheduling](#celery-task-scheduling)
9. [Services Layer](#services-layer)
10. [Data Flow](#data-flow)
11. [Deployment & Docker](#deployment--docker)

---

## 1. Project Overview

**StockMind** is a comprehensive stock market intelligence platform built with Django REST Framework. It provides:
- Real-time stock price updates via WebSockets
- Technical analysis with indicators (RSI, MACD, Bollinger Bands, etc.)
- ML-based stock price predictions using LSTM neural networks
- Sentiment analysis on financial news using Google Gemini AI
- Market scanning for gainers, losers, and unusual volume
- Portfolio management and watchlist tracking
- User authentication with JWT tokens
- Subscription-based API access

**Python Version**: 3.11  
**Django Version**: 4.2.7  
**DRF Version**: 3.14.0

---

## 2. Tech Stack

### Backend Framework
- **Django** 4.2.7 - Web framework
- **Django REST Framework** 3.14.0 - REST API
- **Daphne** 4.0.0 - ASGI server (for WebSockets)
- **Gunicorn** 21.2.0 - WSGI server (for HTTP)

### Authentication & Security
- **djangorestframework-simplejwt** 5.3.0 - JWT authentication
- **django-cors-headers** 4.3.1 - CORS support
- **cryptography** 41.0.7 - Encryption
- **PyJWT** 2.8.0 - JWT handling

### Database
- **PostgreSQL** 15 - Primary database
- **psycopg2-binary** 2.9.9 - PostgreSQL adapter

### Caching & Message Broker
- **Redis** 7.0 - Cache, session store, message broker
- **django-redis** 5.4.0 - Redis cache backend
- **Channels** 4.0.0 - WebSocket support
- **channels-redis** 4.1.0 - Redis backend for Channels

### Async Task Queue
- **Celery** 5.3.4 - Distributed task queue
- **django-celery-beat** 2.5.0 - Periodic task scheduler
- **redis** 5.0.1 - Celery broker/result backend

### Data Processing & ML
- **pandas** 2.2.2 - Data manipulation
- **numpy** 1.26.4 - Numerical computing
- **scikit-learn** 1.4.2 - Machine learning
- **TensorFlow** 2.16.1 - Deep learning
- **Keras** 3.3.3 - Neural networks
- **statsmodels** 0.14.1 - Statistical models

### Market Data & APIs
- **yfinance** - Free stock data (no rate limits!)
- **requests** 2.31.0 - HTTP client
- **httpx** 0.25.2 - Async HTTP client
- **google-generativeai** 0.3.2 - Google Gemini API for sentiment
- **textblob** 0.17.1 - NLP fallback
- **nltk** 3.8.1 - Natural language processing

### Technical Analysis
- **ta** 0.11.0 - Technical analysis indicators
- **TA-Lib** 0.4.28 - Advanced indicators (requires system lib)

### Streaming & Real-time
- **kafka-python** 2.0.2 - Kafka consumer/producer
- **confluent-kafka** 2.3.0 - Confluent Kafka client
- **pyspark** 3.5.1 - Distributed processing

### Big Data / HDFS
- **hdfs** 2.7.0 - Hadoop file system

### Monitoring
- **prometheus-client** 0.19.0 - Prometheus metrics
- **sentry-sdk** 1.38.0 - Error tracking

### Development & Utilities
- **python-decouple** 3.8 - Environment config
- **python-dotenv** 1.0.0 - .env file support
- **Pillow** 10.1.0 - Image processing
- **django-filter** - Filtering support

---

## 3. Directory Structure

```
stockmind_backend/
├── config/                          # Django configuration
│   ├── settings.py                  # Main settings (imports from settings/)
│   ├── settings/
│   │   ├── base.py                  # Base config (DB, cache, middleware, apps)
│   │   ├── development.py           # Dev-specific overrides
│   │   └── production.py            # Production overrides
│   ├── asgi.py                      # ASGI config (WebSockets + HTTP)
│   ├── wsgi.py                      # WSGI config (HTTP only)
│   ├── celery.py                    # Celery config with Beat schedule
│   └── urls.py                      # URL routing (all app endpoints)
│
├── apps/                            # Django applications
│   ├── authentication/
│   │   ├── models.py                # User, UserProfile, RefreshToken models
│   │   ├── views.py                 # Register, Login, Logout, Profile views
│   │   ├── serializers.py           # Auth serializers
│   │   ├── permissions.py           # Custom permissions
│   │   ├── signals.py               # Django signals (e.g., post-save hooks)
│   │   └── urls.py                  # Auth endpoints
│   │
│   ├── market/
│   │   ├── models.py                # Stock, StockPrice, TechnicalIndicator, MarketScanResult, NewsArticle, Sentiment, StockPrediction
│   │   ├── views.py                 # StockDetail, MarketScanner, Predictions views
│   │   ├── serializers.py           # Market serializers
│   │   ├── filters.py               # Filtering logic
│   │   └── urls.py                  # Market endpoints
│   │
│   ├── portfolio/
│   │   ├── models.py                # PortfolioHolding, Watchlist models
│   │   ├── views.py                 # Holdings & Watchlist CRUD
│   │   ├── serializers.py           # Portfolio serializers
│   │   └── urls.py                  # Portfolio endpoints
│   │
│   └── analytics/
│       ├── models.py                # Empty (analytics logic in views)
│       ├── views.py                 # Analytics calculations
│       ├── serializers.py           # Analytics serializers
│       └── urls.py                  # Analytics endpoints
│
├── services/                        # Business logic & external integrations
│   ├── external/
│   │   ├── gemini_api.py           # Google Gemini sentiment analysis
│   │   └── news_api.py             # Financial news API integration
│   │
│   ├── market_data/
│   │   ├── fetcher.py              # yfinance data fetching
│   │   ├── indicators.py           # Technical indicator calculation
│   │   └── scanner.py              # Market scanning logic
│   │
│   ├── ml/
│   │   └── lstm_predictor.py       # LSTM model inference
│   │
│   ├── streaming/
│   │   ├── kafka_consumer.py       # Kafka message consumption
│   │   └── kafka_producer.py       # Kafka message production
│   │
│   └── websocket/
│       ├── routing.py              # WebSocket URL patterns
│       ├── consumers.py            # MarketConsumer (subscribe/unsubscribe)
│       └── broadcaster.py          # Functions to broadcast updates via WebSocket
│
├── tasks/                           # Celery tasks (Beat scheduler)
│   ├── market_tasks.py             # fetch_market_data, calculate_technical_indicators
│   ├── prediction_tasks.py         # update_predictions
│   ├── scanner_tasks.py            # run_market_scanner
│   ├── sentiment_tasks.py          # fetch_and_analyze_news
│   └── cleanup_tasks.py            # cleanup_old_data
│
├── middleware/                      # Django middleware
│   ├── rate_limit.py               # Rate limiting (dev stub)
│   └── metrics.py                  # Prometheus metrics (dev stub)
│
├── utils/                           # Utility functions
│   ├── exceptions.py               # Custom exception handler
│   ├── responses.py                # Standard response format
│   ├── renderer.py                 # CamelCase JSON renderer
│   └── constants.py                # App constants
│
├── models/                          # ML models (Keras/TensorFlow)
│   ├── lstm_model.keras            # LSTM model weights
│   └── lstm_model_best.keras       # Best checkpoint
│
├── scripts/
│   └── train_lstm_model.py         # Script to train LSTM on historical data
│
├── logs/                            # Application logs
├── static/                          # Static files (CSS, JS, images)
│
├── manage.py                        # Django CLI
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Docker container config
├── docker-compose.yml               # Multi-container orchestration
└── README.md                        # Project documentation
```

---

## 4. Core Configuration

### 4.1 Settings Hierarchy

**`config/settings.py`** → **`config/settings/base.py`** (Imports from base)

**`config/settings/base.py`** contains:

```python
# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'stockmind',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Cache (Redis)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://localhost:6379/0',
    }
}

# Channels (WebSocket)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('localhost', 6379)],
        }
    }
}

# Celery
CELERY_BROKER_URL = 'redis://localhost:6379/1'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/2'

# JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework_simplejwt.authentication.JWTAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
}

# Custom User Model
AUTH_USER_MODEL = 'authentication.User'

# Installed Apps
INSTALLED_APPS = [
    'apps.authentication',
    'apps.market',
    'apps.portfolio',
    'apps.analytics',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'channels',
    'django_celery_beat',
    # ... Django default apps
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'middleware.rate_limit.RateLimitMiddleware',
    'middleware.metrics.PrometheusMiddleware',
    # ... other middleware
]
```

### 4.2 ASGI Configuration (WebSockets + HTTP)

**`config/asgi.py`**:
```python
application = ProtocolTypeRouter({
    'http': get_asgi_application(),  # HTTP requests
    'websocket': AuthMiddlewareStack(  # WebSocket connections
        URLRouter(websocket_urlpatterns)  # ws/market/
    ),
})
```

### 4.3 Celery Beat Schedule

**`config/celery.py`** defines automatic tasks:

```python
app.conf.beat_schedule = {
    'fetch-market-data-every-minute': {
        'task': 'tasks.market_tasks.fetch_market_data',
        'schedule': crontab(minute='*'),  # Every minute
    },
    'calculate-technical-indicators': {
        'task': 'tasks.market_tasks.calculate_technical_indicators',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'update-predictions-hourly': {
        'task': 'tasks.prediction_tasks.update_predictions',
        'schedule': crontab(minute=0),  # Every hour
    },
    'fetch-news-every-30min': {
        'task': 'tasks.sentiment_tasks.fetch_and_analyze_news',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    'cleanup-old-data-daily': {
        'task': 'tasks.cleanup_tasks.cleanup_old_data',
        'schedule': crontab(hour=0, minute=0),  # Midnight
    },
}
```

---

## 5. Database Models

### 5.1 Authentication App

**`User` Model**:
- Custom user model (extends AbstractUser)
- Email-based authentication (not username)
- Fields: `id` (UUID), `email`, `full_name`, `avatar_url`, `is_email_verified`
- Timestamps: `created_at`, `updated_at`

**`UserProfile` Model**:
- One-to-one relationship with User
- Subscription tiers: `basic`, `premium`, `pro`
- API key for authentication
- Daily request counting & limits
- Notification preferences (JSON)
- Related to User via `profile` accessor

**`RefreshToken` Model**:
- Stores JWT refresh tokens
- Track revocation status & expiration
- Unique token per user

### 5.2 Market App

**`Stock` Model**:
- Primary key: `symbol` (e.g., "AAPL")
- Fields: `name`, `sector`, `industry`, `market_cap`, `exchange`, `currency`
- Related models: `prices`, `indicators`, `scan_results`, `news`

**`StockPrice` Model**:
- Time-series OHLCV data
- Fields: `open`, `high`, `low`, `close`, `volume`, `adjusted_close`
- FK to Stock, unique on (stock, timestamp)
- Ordered by timestamp descending
- Properties: `change`, `change_percent`

**`TechnicalIndicator` Model**:
- Calculated metrics for each stock/timestamp
- Fields:
  - **Moving Averages**: `sma_20`, `sma_50`, `sma_200`, `ema_12`, `ema_26`
  - **Momentum**: `rsi_14`, `macd`, `macd_signal`, `macd_histogram`
  - **Volatility**: `bollinger_upper`, `bollinger_middle`, `bollinger_lower`, `atr_14`
  - **Volume**: `obv` (On-Balance Volume)

**`MarketScanResult` Model**:
- Scan results (daily/weekly/monthly)
- Flags: `is_unusual_volume`, `is_breakout`, `is_gainer`, `is_loser`
- Trend: `Bullish`, `Bearish`, `Neutral`
- Support/Resistance levels

**`NewsArticle` Model**:
- FK to Stock
- Fields: `title`, `description`, `source`, `url`, `published_at`

**`Sentiment` Model**:
- AI sentiment analysis results
- Fields: `ai_sentiment` (positive/neutral/negative), `ai_score` (float -1 to 1)
- Analysis text
- Related to NewsArticle

**`StockPrediction` Model**:
- ML predictions for short/medium/long term
- Short-term (7 days), Medium-term (30 days), Long-term (90 days)
- Each term has: `target`, `change`, `confidence`, `trend`
- Overall: `bullish_score`, `risk_level`, `overall_sentiment`

### 5.3 Portfolio App

**`PortfolioHolding` Model**:
- User's stock holdings
- Fields: `shares`, `average_price`, `purchase_date`, `notes`
- Unique on (user, stock)
- Properties: `total_cost`, `current_value`, `profit_loss`, `profit_loss_percent`

**`Watchlist` Model**:
- User's watched stocks
- Fields: `alert_price_above`, `alert_price_below`, `notes`
- Unique on (user, stock)

### 5.4 Analytics App
- Models empty (logic in views)

**Relationships Summary**:
```
User (1) ──→ (1) UserProfile
User (1) ──→ (M) RefreshToken
User (1) ──→ (M) PortfolioHolding → (M) Stock
User (1) ──→ (M) Watchlist → (M) Stock
Stock (1) ──→ (M) StockPrice
Stock (1) ──→ (M) TechnicalIndicator
Stock (1) ──→ (M) MarketScanResult
Stock (1) ──→ (M) NewsArticle
Stock (1) ──→ (M) Sentiment
Stock (1) ──→ (M) StockPrediction
NewsArticle (1) ──→ (1) Sentiment (optional)
```

---

## 6. API Architecture

### 6.1 URL Routes

**Main URLs** (`config/urls.py`):
```
/                                   → Landing page (HTML)
/admin/                            → Django admin
/api/auth/                         → Authentication endpoints
/api/market/                       → Market data endpoints
/api/portfolio/                    → Portfolio endpoints
/api/analytics/                    → Analytics endpoints
/api/token/refresh/                → JWT token refresh
```

### 6.2 Authentication Endpoints (`apps/authentication/urls.py`)

```
POST   /api/auth/register/          → RegisterView.post()
POST   /api/auth/login/             → LoginView.post()
POST   /api/auth/logout/            → LogoutView.post()
GET    /api/auth/profile/           → ProfileView.get()
PATCH  /api/auth/profile/           → ProfileView.patch()
```

**Register Response**:
```json
{
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "fullName": "John Doe",
      "isEmailVerified": false
    }
  },
  "message": "Registration successful",
  "status": "success"
}
```

**Login Response**:
```json
{
  "data": {
    "token": "access_token...",
    "refresh": "refresh_token...",
    "user": { ... }
  },
  "message": "Login successful",
  "status": "success"
}
```

### 6.3 Market Endpoints (`apps/market/urls.py`)

```
GET    /api/market/stock/{symbol}/         → StockDetailView.get()
GET    /api/market/scanner/                → MarketScannerView.get()
GET    /api/market/predictions/{symbol}/   → StockPredictionView.get()
GET    /api/market/sentiment/{symbol}/     → SentimentView.get()
GET    /api/market/news/{symbol}/          → NewsView.get()
```

**Stock Detail Response**:
```json
{
  "data": {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "price": 180.45,
    "change": 2.15,
    "changePercent": 1.20,
    "volume": 52000000,
    "marketCap": 2800000000000,
    "high52w": 199.62,
    "low52w": 125.07,
    "historicalData": [
      {
        "date": "2024-12-19",
        "open": 178.30,
        "high": 181.50,
        "low": 177.80,
        "close": 180.45,
        "volume": 52000000
      }
    ],
    "indicators": {
      "rsi": 65.4,
      "macd": 2.34,
      "sma20": 179.50,
      "sma50": 176.80
    }
  },
  "message": "",
  "status": "success"
}
```

**Market Scanner Response**:
```json
{
  "data": {
    "timeframe": "daily",
    "timestamp": "2024-12-20T15:30:00Z",
    "gainers": [
      {
        "symbol": "NVDA",
        "price": 134.50,
        "changePercent": 5.23,
        "trend": "Bullish"
      }
    ],
    "losers": [ ... ],
    "mostActive": [ ... ],
    "unusualVolume": [ ... ],
    "breakouts": [ ... ],
    "marketOverview": {
      "totalScanned": 5000,
      "bullish": 2400,
      "bearish": 1600,
      "avgChange": 0.45
    }
  },
  "status": "success"
}
```

### 6.4 Portfolio Endpoints (`apps/portfolio/urls.py`)

```
GET    /api/portfolio/holdings/              → PortfolioHoldingsView.get()
POST   /api/portfolio/holdings/              → PortfolioHoldingsView.post()
GET    /api/portfolio/holdings/{id}/         → PortfolioHoldingDetailView.get()
PATCH  /api/portfolio/holdings/{id}/         → PortfolioHoldingDetailView.patch()
DELETE /api/portfolio/holdings/{id}/         → PortfolioHoldingDetailView.delete()

GET    /api/portfolio/watchlist/             → WatchlistView.get()
POST   /api/portfolio/watchlist/             → WatchlistView.post()
GET    /api/portfolio/watchlist/{id}/        → WatchlistDetailView.get()
PATCH  /api/portfolio/watchlist/{id}/        → WatchlistDetailView.patch()
DELETE /api/portfolio/watchlist/{id}/        → WatchlistDetailView.delete()
```

### 6.5 Request/Response Format

**Standard Success Response**:
```json
{
  "data": null or {...},
  "message": "Operation successful",
  "status": "success",
  "success": true
}
```

**Standard Error Response**:
```json
{
  "data": null,
  "message": "Error description",
  "status": "error",
  "errors": { "field": ["error"] },
  "success": false,
  "code": 400
}
```

**Authentication Header**:
```
Authorization: Bearer <access_token>
```

**Pagination** (default 100 per page):
```
?page=1&page_size=50
```

---

## 7. Real-time WebSocket Flow

### 7.1 WebSocket Architecture

**Connection URL**: `ws://localhost:8000/ws/market/`

**Routing** (`services/websocket/routing.py`):
```python
websocket_urlpatterns = [
    path('ws/market/', MarketConsumer.as_asgi()),
]
```

### 7.2 MarketConsumer Lifecycle

**`services/websocket/consumers.py`**:

```python
class MarketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Client connects → accept connection
        # Initialize subscribed_symbols set
        
    async def disconnect(self, close_code):
        # Client disconnects → leave all groups
        
    async def receive(self, text_data):
        # Receive JSON message from client
        # Action: "subscribe" or "unsubscribe"
        # Call subscribe_to_stock() or unsubscribe_from_stock()
        
    async def subscribe_to_stock(self, symbol):
        # Add to group: f"stock_{symbol}"
        # Send confirmation message
        # Send current cached price if available
        
    async def unsubscribe_from_stock(self, symbol):
        # Remove from group
        # Send confirmation
        
    async def stock_update(self, event):
        # Called when group_send sends "stock_update"
        # Send JSON to WebSocket client
        
    async def indicator_update(self, event):
        # Called when group_send sends "indicator_update"
        
    async def sentiment_update(self, event):
        # Called when group_send sends "sentiment_update"
```

### 7.3 Client Message Format

**Subscribe**:
```json
{
  "type": "subscribe",
  "symbol": "AAPL"
}
```

**Response**:
```json
{
  "type": "subscribed",
  "symbol": "AAPL",
  "message": "Subscribed to AAPL"
}
```

**Unsubscribe**:
```json
{
  "type": "unsubscribe",
  "symbol": "AAPL"
}
```

### 7.4 Server Broadcasting

**Broadcasting Functions** (`services/websocket/broadcaster.py`):

```python
def broadcast_stock_update(symbol, data):
    # Send to group: f"stock_{symbol}"
    # Triggers: MarketConsumer.stock_update(event)
    
def broadcast_indicator_update(symbol, indicators):
    # Send to group: f"stock_{symbol}"
    # Triggers: MarketConsumer.indicator_update(event)
    
def broadcast_sentiment_update(symbol, sentiment_data):
    # Send to group: f"stock_{symbol}"
    # Triggers: MarketConsumer.sentiment_update(event)
    
def broadcast_prediction_update(symbol, prediction_data):
    # Send to group: f"stock_{symbol}"
    # Triggers: MarketConsumer.prediction_update(event)
```

**Example Broadcast Call** (from Celery task):
```python
# In tasks/market_tasks.py
quote = fetcher.fetch_real_time_quote(symbol)
broadcast_stock_update(symbol, quote)
# All clients subscribed to "stock_AAPL" receive update
```

### 7.5 Real-Time Flow Diagram

```
Celery Beat (every minute)
        ↓
fetch_market_data() task
        ↓
MarketDataFetcher.fetch_real_time_quote("AAPL")
        ↓
Save to StockPrice table
        ↓
Cache in Redis
        ↓
broadcast_stock_update("AAPL", quote_data)
        ↓
Channel Layer (Redis)
        ↓
Group: "stock_AAPL"
        ↓
All connected MarketConsumers in group receive update
        ↓
WebSocket sends JSON to client: { type: "stock_update", data: {...} }
```

---

## 8. Celery Task Scheduling

### 8.1 Task Queue Configuration

**Broker**: Redis on port 6379, DB 1  
**Result Backend**: Redis on port 6379, DB 2  
**Scheduler**: Django Celery Beat (database scheduler)

### 8.2 Scheduled Tasks

**Every Minute** - `tasks.market_tasks.fetch_market_data`:
- Fetch real-time quotes for top 100 stocks
- Save to StockPrice table
- Cache in Redis
- Broadcast via WebSocket
- Send to Kafka topic

**Every 5 Minutes** - `tasks.market_tasks.calculate_technical_indicators`:
- Calculate RSI, MACD, SMA, EMA, Bollinger Bands, ATR, OBV
- Save to TechnicalIndicator table
- Cache results

**Every Hour** - `tasks.prediction_tasks.update_predictions`:
- Get historical price data (500 days)
- Run LSTM model inference
- Generate short/medium/long term predictions
- Save to StockPrediction table
- Broadcast via WebSocket

**Every 30 Minutes** - `tasks.sentiment_tasks.fetch_and_analyze_news`:
- Fetch latest news articles for top 50 stocks
- Analyze sentiment using Google Gemini API
- Fallback to TextBlob if Gemini fails
- Save to NewsArticle and Sentiment tables

**Daily at 4 PM (Market Close)** - `tasks.scanner_tasks.run_market_scanner`:
- Scan all stocks for:
  - Unusual volume
  - Breakouts
  - Top gainers/losers
  - Trend analysis (bullish/bearish)
  - Support/resistance levels
- Save MarketScanResult

**Daily at Midnight** - `tasks.cleanup_tasks.cleanup_old_data`:
- Delete old StockPrice records (>1 year)
- Archive historical data
- Cleanup cache

### 8.3 Task Routing

```python
app.conf.task_routes = {
    'tasks.market_tasks.*': {'queue': 'market_data'},
    'tasks.prediction_tasks.*': {'queue': 'predictions'},
    'tasks.sentiment_tasks.*': {'queue': 'sentiment'},
    'tasks.scanner_tasks.*': {'queue': 'default'},
}
```

### 8.4 Running Celery

**Start Worker**:
```bash
celery -A config worker -l info -Q market_data,predictions,sentiment,default
```

**Start Beat Scheduler**:
```bash
celery -A config beat -l info
```

---

## 9. Services Layer

### 9.1 Market Data Service

**`services/market_data/fetcher.py`** - Uses yfinance (no rate limits):

```python
fetcher = MarketDataFetcher()

# Fetch real-time quote
quote = fetcher.fetch_real_time_quote("AAPL")
# Returns: {symbol, price, change, changePercent, volume, open, high, low, timestamp}

# Fetch historical data
historical = fetcher.fetch_historical_data("AAPL", period='1y', interval='1d')
# Returns: List of {date, open, high, low, close, volume}

# Fetch company overview
overview = fetcher.fetch_company_overview("AAPL")
# Returns: {name, sector, industry, marketCap, peRatio, beta, ...}

# Save price to DB
fetcher.save_stock_price("AAPL", quote_data)
```

### 9.2 Technical Indicators

**`services/market_data/indicators.py`**:

```python
calculator = TechnicalIndicatorCalculator()

indicators = calculator.calculate_indicators("AAPL")
# Calculates and saves:
# - Moving Averages (SMA 20/50/200, EMA 12/26)
# - Momentum (RSI, MACD, MACD Signal, MACD Histogram)
# - Volatility (Bollinger Bands, ATR)
# - Volume (OBV)

# Returns: TechnicalIndicator model instance
```

### 9.3 Market Scanner

**`services/market_data/scanner.py`**:

```python
scanner = MarketScanner()

results = scanner.scan(timeframe='daily')
# For each stock analyzes:
# - Volume patterns (unusual volume detection)
# - Price breakouts
# - Gainers/losers
# - Trend direction (bullish/bearish)
# - Support/resistance levels
```

### 9.4 External APIs

**Google Gemini Sentiment Analysis** (`services/external/gemini_api.py`):

```python
analyzer = GeminiSentimentAnalyzer()

sentiment = analyzer.analyze_article(title, description)
# Returns: {sentiment: "positive"|"neutral"|"negative", score: float(-1 to 1), analysis: str}

# If Gemini fails → fallback to TextBlob
```

**News API** (`services/external/news_api.py`):

```python
news_service = NewsAPIService()

articles = news_service.fetch_news("AAPL")
# Fetches latest articles from financial news sources
```

### 9.5 ML Predictions

**`services/ml/lstm_predictor.py`**:

```python
predictor = LSTMPredictor()

predictions = predictor.predict(df, steps=90)
# Input: DataFrame with historical prices
# Output: List of 90 predicted closing prices

# Current implementation: Simple stub (returns last price)
# Production: Load trained Keras model
```

**Training Script** (`scripts/train_lstm_model.py`):
```python
trainer = LSTMModelTrainer()

# Fetch 5 years of data for multiple stocks
data = trainer.fetch_training_data(['AAPL', 'MSFT', 'GOOGL'], period='5y')

# Prepare data: normalize, create sequences
X, y = trainer.prepare_data(data)

# Build & train LSTM
trainer.build_model()
trainer.train(X, y)

# Save model
trainer.save_model('models/lstm_model.keras')
```

### 9.6 Streaming (Kafka)

**Kafka Producer** (`services/streaming/kafka_producer.py`):
```python
producer = StockDataProducer()

producer.send_market_data("AAPL", quote_data)
# Topic: "stock_prices"
# Serializes as JSON
```

**Kafka Consumer** (`services/streaming/kafka_consumer.py`):
```python
consumer = StockDataConsumer()

# Listen on "stock_prices" topic
# Consume and process messages
```

---

## 10. Data Flow

### 10.1 New User Registration Flow

```
1. Client: POST /api/auth/register/
   {email, password, fullName}

2. RegisterView.post():
   - Validate via RegisterSerializer
   - Create User (CustomUserManager)
   - Create UserProfile with API key
   - Generate JWT tokens (RefreshToken + access)

3. Response: {token, user}

4. Signals: apps/authentication/signals.py
   - post_save User signal
   - Create UserProfile if not exists
   - Initialize notification preferences
```

### 10.2 User Login Flow

```
1. Client: POST /api/auth/login/
   {email, password}

2. LoginView.post():
   - Validate credentials via LoginSerializer
   - Generate JWT tokens (RefreshToken.for_user())
   - Update profile.last_login_ip

3. Response: {token, refresh, user}

4. Client: Store tokens in localStorage
```

### 10.3 Real-Time Stock Update Flow

```
Timeline: Every 1 minute (Celery Beat)

1. Beat Schedule triggers: fetch_market_data()

2. Task execution:
   a. Loop through active stocks (top 100)
   b. MarketDataFetcher.fetch_real_time_quote("AAPL")
      - Check cache (Redis)
      - If not cached, call yfinance API
      - Return quote data
   c. fetcher.save_stock_price("AAPL", quote)
      - Create StockPrice record in DB
      - Unique on (stock, timestamp)
   d. cache.set(f"latest_price_AAPL", quote, 300)
      - Cache for 5 minutes
   e. producer.send_market_data("AAPL", quote)
      - Send to Kafka topic "stock_prices"
   f. broadcast_stock_update("AAPL", quote)
      - Get Redis channel layer
      - Send to group "stock_AAPL"

3. WebSocket Broadcasting:
   a. Group message sent to Redis
   b. All MarketConsumers in group "stock_AAPL" receive
   c. MarketConsumer.stock_update(event) called
   d. JSON sent to all connected WebSocket clients

4. Client receives:
   {type: "stock_update", data: {symbol, price, change, volume, timestamp}}
```

### 10.4 Technical Indicator Flow

```
Timeline: Every 5 minutes (Celery Beat)

1. Beat Schedule triggers: calculate_technical_indicators()

2. Loop through active stocks:
   a. TechnicalIndicatorCalculator.calculate_indicators("AAPL")
      - Get last 200 StockPrice records
      - Calculate:
        * Moving Averages (20, 50, 200 day)
        * RSI (14 day)
        * MACD
        * Bollinger Bands
        * ATR
        * OBV
   b. Save to TechnicalIndicator table (unique on stock, timestamp)
   c. cache.set(f"indicators_AAPL", indicators, 600)
   d. broadcast_indicator_update("AAPL", indicators)

3. Clients subscribed to "AAPL" receive indicator update
```

### 10.5 ML Prediction Flow

```
Timeline: Every 1 hour (Celery Beat)

1. Beat Schedule triggers: update_predictions()

2. Loop through top 50 stocks:
   a. Get 500 days of StockPrice data
   b. LSTMPredictor.predict(df, steps=90)
      - Load trained Keras model
      - Generate 90 future predictions
   c. Calculate targets & trends:
      * 7-day (short-term)
      * 30-day (medium-term)
      * 90-day (long-term)
   d. Create StockPrediction record with:
      - target prices
      - % change
      - confidence levels
      - trend direction
      - overall sentiment
   e. broadcast_prediction_update("AAPL", prediction_data)

3. Clients receive prediction updates via WebSocket
```

### 10.6 Sentiment Analysis Flow

```
Timeline: Every 30 minutes (Celery Beat)

1. Beat Schedule triggers: fetch_and_analyze_news()

2. Loop through top 50 stocks:
   a. NewsAPIService.fetch_news("AAPL")
      - Query financial news APIs
      - Get latest articles
   b. For each article:
      c. GeminiSentimentAnalyzer.analyze_article(title, description)
         - Send to Google Gemini API
         - Request JSON response: {sentiment, score, analysis}
         - Retry with exponential backoff (3 attempts)
      d. If Gemini fails → fallback to TextBlob
      e. Save to NewsArticle table
      f. Save to Sentiment table
   g. aggregate_sentiment("AAPL")
      - Average sentiment from last 7 days
      - Count bullish/neutral/bearish
      - Determine overall sentiment
   h. broadcast_sentiment_update("AAPL", sentiment_data)

3. Clients receive sentiment updates
```

### 10.7 Market Scanner Flow

```
Timeline: Daily at 4 PM ET (Market Close) - Celery Beat

1. Beat Schedule triggers: run_market_scanner(timeframe='daily')

2. MarketScanner.scan(timeframe='daily'):
   a. Get all active stocks
   b. For each stock analyze:
      - Current price vs volume patterns
      - Detect unusual volume (>2x avg)
      - Detect breakouts (>5% daily change)
      - Classify as gainer/loser
      - Calculate trend (RSI, MACD)
      - Find support/resistance levels
   c. Categorize results:
      * Top gainers
      * Top losers
      * Most active
      * Unusual volume
      * Breakouts

3. Save MarketScanResult for each stock

4. When clients request: GET /api/market/scanner/?timeframe=daily
   a. Query latest scan timestamp
   b. Separate results by category
   c. Calculate market overview stats
   d. Cache for 10 minutes
   e. Return to client
```

### 10.8 Portfolio Management Flow

```
1. User: POST /api/portfolio/holdings/
   {symbol, shares, averagePrice, purchaseDate}

2. PortfolioHoldingsView.post():
   a. Validate via PortfolioHoldingCreateSerializer
   b. Create PortfolioHolding with user=request.user
   c. Unique constraint on (user, stock)
   d. Response: holding data

3. Get Holdings: GET /api/portfolio/holdings/
   a. Query: PortfolioHolding.objects.filter(user=user)
   b. For each holding calculate:
      - Total cost = shares × average_price
      - Current value = shares × latest_stock_price
      - Profit/Loss = current_value - total_cost
      - ROI% = (profit_loss / total_cost) × 100
   c. Return serialized holdings

4. Update Holdings: PATCH /api/portfolio/holdings/{id}/
   a. Validate user owns holding
   b. Update shares, average_price, notes
   c. Return updated holding

5. Delete Holdings: DELETE /api/portfolio/holdings/{id}/
   a. Validate user owns holding
   b. Delete record
```

---

## 11. Deployment & Docker

### 11.1 Dockerfile

```dockerfile
FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ postgresql-client libpq-dev \
    build-essential wget

# Install TA-Lib system library
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib/ && \
    ./configure --prefix=/usr && \
    make && make install

# Copy requirements & install Python packages
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

# Run migrations & start server
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
```

### 11.2 Docker Compose Services

```yaml
version: '3.8'

services:
  postgres:        # PostgreSQL database
  redis:           # Cache & message broker
  zookeeper:       # Kafka coordination
  kafka:           # Message streaming
  spark-master:    # Distributed processing
  spark-worker:    # Worker nodes
  web:             # Django app (Daphne for WebSockets)
  celery-worker:   # Task queue worker
  celery-beat:     # Task scheduler
```

### 11.3 Starting Services

```bash
# Start all services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Check logs
docker-compose logs -f web

# Stop services
docker-compose down
```

### 11.4 Environment Variables (.env)

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=stockmind
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=postgres
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# JWT
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# APIs
GEMINI_API_KEY=your-gemini-key
NEWS_API_KEY=your-news-api-key

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# Spark
SPARK_MASTER_URL=spark://spark-master:7077
```

---

## Summary: Technology Stack & Architecture

| Component | Tech | Purpose |
|-----------|------|---------|
| **Framework** | Django 4.2 + DRF 3.14 | REST API backend |
| **Real-time** | Channels 4.0 + Redis | WebSocket for live updates |
| **Database** | PostgreSQL 15 | Persistent storage |
| **Cache** | Redis 7.0 | Performance & caching |
| **Task Queue** | Celery 5.3 + Beat | Scheduled background jobs |
| **Auth** | JWT (simplejwt) | Token-based authentication |
| **ML** | TensorFlow + Keras | LSTM price predictions |
| **Data** | Pandas + NumPy | Data processing |
| **Market Data** | yfinance | Stock quotes (free, no rate limits) |
| **Sentiment** | Google Gemini API | AI sentiment analysis |
| **Streaming** | Kafka + PySpark | Real-time data processing |
| **Monitoring** | Prometheus | Metrics collection |
| **Deployment** | Docker + Docker Compose | Containerization |
| **ASGI Server** | Daphne 4.0 | WebSocket + HTTP |
| **WSGI Server** | Gunicorn 21.2 | HTTP only (production) |

---

## Key Workflows at a Glance

1. **New Stock Update** (Every minute):
   - Celery Beat → fetch_market_data → yfinance → StockPrice DB → Redis cache → WebSocket broadcast

2. **Technical Analysis** (Every 5 minutes):
   - Celery Beat → calculate_technical_indicators → TechnicalIndicator DB → WebSocket broadcast

3. **Predictions** (Every hour):
   - Celery Beat → LSTM inference → StockPrediction DB → WebSocket broadcast

4. **News & Sentiment** (Every 30 minutes):
   - Celery Beat → NewsAPI → Gemini API → Sentiment DB → WebSocket broadcast

5. **User Registration**:
   - POST /api/auth/register → User + UserProfile created → JWT tokens returned

6. **Portfolio Management**:
   - User adds holdings → PortfolioHolding table → Calculate P&L with latest prices

7. **WebSocket Real-time**:
   - Client: ws://localhost:8000/ws/market/
   - Subscribe: {type: "subscribe", symbol: "AAPL"}
   - Receive: {type: "stock_update", data: {...}}

