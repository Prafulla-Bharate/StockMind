# StockMind Backend - Architecture Diagrams

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Web Browser / Mobile App                                                         │
│  - REST API calls (HTTP)                                                         │
│  - WebSocket connection (Real-time updates)                                      │
└───────┬──────────────────────────────────────────────────────────────────────────┘
        │
        ├─────────────────────────────────────┬────────────────────────────────────┐
        │                                     │                                    │
        ▼                                     ▼                                    ▼
┌──────────────────┐             ┌──────────────────┐          ┌──────────────────┐
│  HTTP/REST API   │             │  WebSocket       │          │   JWT Auth       │
│  Port 8000       │             │  Connection      │          │   Middleware     │
│  (Daphne ASGI)   │             │  Port 8000       │          │                  │
└────────┬─────────┘             └────────┬─────────┘          └──────────────────┘
         │                                 │
         └─────────────────┬───────────────┘
                           │
        ┌──────────────────▼───────────────────────────┐
        │   DJANGO APPLICATION LAYER                   │
        ├──────────────────────────────────────────────┤
        │                                              │
        │  ┌─ ASGI (config/asgi.py) ──────────────┐   │
        │  │ ProtocolTypeRouter:                  │   │
        │  │ - HTTP → Django (REST Framework)     │   │
        │  │ - WebSocket → Channels               │   │
        │  └──────────────────────────────────────┘   │
        │                                              │
        │  ┌─ URL ROUTING (config/urls.py) ──────┐   │
        │  │ /api/auth/       → Authentication    │   │
        │  │ /api/market/     → Market Data       │   │
        │  │ /api/portfolio/  → Portfolio Mgmt    │   │
        │  │ /api/analytics/  → Analytics        │   │
        │  │ /ws/market/      → WebSocket        │   │
        │  └──────────────────────────────────────┘   │
        │                                              │
        │  ┌─ MIDDLEWARE ──────────────────────────┐   │
        │  │ - RateLimitMiddleware                 │   │
        │  │ - PrometheusMiddleware                │   │
        │  │ - AuthMiddlewareStack (for WS)        │   │
        │  └──────────────────────────────────────┘   │
        │                                              │
        └──────────────────┬──────────────────────────┘
                           │
        ┌──────────────────▼──────────────────────────────────────────┐
        │        DJANGO APPLICATIONS (apps/)                         │
        ├───────────────────────────────────────────────────────────┤
        │                                                            │
        │  ┌─ AUTHENTICATION ────────────────────────────────────┐  │
        │  │ - User Model (Custom, email-based)                 │  │
        │  │ - UserProfile (subscription tiers, API keys)       │  │
        │  │ - RefreshToken (JWT token management)              │  │
        │  │ Views: Register, Login, Logout, Profile            │  │
        │  └────────────────────────────────────────────────────┘  │
        │                                                            │
        │  ┌─ MARKET ─────────────────────────────────────────────┐  │
        │  │ - Stock (symbol, name, sector, etc)                 │  │
        │  │ - StockPrice (OHLCV data, time-series)              │  │
        │  │ - TechnicalIndicator (RSI, MACD, SMA, etc)          │  │
        │  │ - MarketScanResult (gainers, losers, breakouts)     │  │
        │  │ - NewsArticle (financial news)                      │  │
        │  │ - Sentiment (AI sentiment analysis)                 │  │
        │  │ - StockPrediction (ML predictions)                  │  │
        │  │ Views: StockDetail, MarketScanner, Predictions      │  │
        │  └────────────────────────────────────────────────────┘  │
        │                                                            │
        │  ┌─ PORTFOLIO ──────────────────────────────────────────┐  │
        │  │ - PortfolioHolding (user's stock holdings)          │  │
        │  │ - Watchlist (user's watched stocks)                 │  │
        │  │ Views: CRUD operations for holdings & watchlist     │  │
        │  └────────────────────────────────────────────────────┘  │
        │                                                            │
        │  ┌─ ANALYTICS ──────────────────────────────────────────┐  │
        │  │ - Portfolio performance calculations                │  │
        │  │ - Risk metrics & allocation analysis                │  │
        │  └────────────────────────────────────────────────────┘  │
        │                                                            │
        └────────────────────┬───────────────────────────────────────┘
                             │
        ┌────────────────────▼───────────────────────────────────┐
        │      SERVICES LAYER (services/)                        │
        ├───────────────────────────────────────────────────────┤
        │                                                       │
        │  ┌─ MARKET DATA ─────────────────────────────────┐   │
        │  │ - fetcher.py: yfinance data fetching         │   │
        │  │ - indicators.py: Technical analysis calc      │   │
        │  │ - scanner.py: Market screening logic         │   │
        │  └──────────────────────────────────────────────┘   │
        │                                                       │
        │  ┌─ EXTERNAL APIs ──────────────────────────────┐   │
        │  │ - gemini_api.py: Google Gemini sentiment     │   │
        │  │ - news_api.py: Financial news sources        │   │
        │  └──────────────────────────────────────────────┘   │
        │                                                       │
        │  ┌─ MACHINE LEARNING ────────────────────────────┐   │
        │  │ - lstm_predictor.py: Price predictions       │   │
        │  └──────────────────────────────────────────────┘   │
        │                                                       │
        │  ┌─ STREAMING ──────────────────────────────────┐   │
        │  │ - kafka_producer.py: Send market data        │   │
        │  │ - kafka_consumer.py: Consume messages        │   │
        │  └──────────────────────────────────────────────┘   │
        │                                                       │
        │  ┌─ WEBSOCKET ──────────────────────────────────┐   │
        │  │ - routing.py: ws/market/ pattern             │   │
        │  │ - consumers.py: MarketConsumer               │   │
        │  │ - broadcaster.py: Broadcast helpers          │   │
        │  └──────────────────────────────────────────────┘   │
        │                                                       │
        └────────────────────┬────────────────────────────────┘
                             │
        ┌────────────────────▼────────────────────────────────────┐
        │      CELERY TASK QUEUE (config/celery.py, tasks/)       │
        ├────────────────────────────────────────────────────────┤
        │                                                         │
        │  BEAT SCHEDULER (runs at specified intervals)           │
        │                                                         │
        │  Every 1 minute  → fetch_market_data()                 │
        │  Every 5 minutes → calculate_technical_indicators()    │
        │  Every hour      → update_predictions()                │
        │  Every 30 min    → fetch_and_analyze_news()            │
        │  Daily 4 PM      → run_market_scanner()                │
        │  Daily midnight  → cleanup_old_data()                  │
        │                                                         │
        │  WORKERS (celery worker processes)                      │
        │  ├─ market_data queue (3+ workers)                      │
        │  ├─ predictions queue (2+ workers)                      │
        │  ├─ sentiment queue (2+ workers)                        │
        │  └─ default queue                                       │
        │                                                         │
        └────────────────────┬────────────────────────────────┘
                             │
        ┌────────────────────▼─────────────────────────────────────────┐
        │       EXTERNAL DATA SOURCES & MESSAGE BROKERS               │
        ├──────────────────────────────────────────────────────────────┤
        │                                                              │
        │  ┌─ DATA SOURCES ────────────────────────────────────┐      │
        │  │ - yfinance: Stock quotes, historical data        │      │
        │  │ - NewsAPI: Financial news articles               │      │
        │  │ - Google Gemini API: Sentiment analysis          │      │
        │  │ - Technical Analysis Indicators                  │      │
        │  └──────────────────────────────────────────────────┘      │
        │                                                              │
        │  ┌─ MESSAGE BROKERS & CACHING ──────────────────────┐      │
        │  │ - Redis: Cache, sessions, pub/sub                │      │
        │  │ - Kafka: Real-time data streaming                │      │
        │  │ - Channel Layers: WebSocket broadcasting         │      │
        │  └──────────────────────────────────────────────────┘      │
        │                                                              │
        └──────────────────────────────────────────────────────────────┘
                             │
        ┌────────────────────▼─────────────────────────────────────────┐
        │          PERSISTENT STORAGE LAYER                            │
        ├──────────────────────────────────────────────────────────────┤
        │                                                              │
        │  ┌─ PostgreSQL (Primary) ────────────────────────────┐      │
        │  │ - Users & Authentication                         │      │
        │  │ - Stock master data                              │      │
        │  │ - Stock prices (OHLCV time-series)               │      │
        │  │ - Technical indicators                           │      │
        │  │ - Market scan results                            │      │
        │  │ - News articles & sentiment                      │      │
        │  │ - ML predictions                                 │      │
        │  │ - User portfolios & watchlists                   │      │
        │  └──────────────────────────────────────────────────┘      │
        │                                                              │
        │  ┌─ Redis (Cache & Session Store) ───────────────────┐     │
        │  │ - Stock prices (short-lived)                      │     │
        │  │ - Technical indicators cache                      │     │
        │  │ - User session data                               │     │
        │  │ - Rate limiting counters                          │     │
        │  │ - Celery task queue & results                     │     │
        │  │ - WebSocket channel layer                         │     │
        │  └──────────────────────────────────────────────────┘      │
        │                                                              │
        │  ┌─ File Storage ────────────────────────────────────┐      │
        │  │ - ML model weights (Keras)                        │      │
        │  │ - Static files, logs                              │      │
        │  └──────────────────────────────────────────────────┘      │
        │                                                              │
        └──────────────────────────────────────────────────────────────┘
```

---

## Real-Time Data Update Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        REAL-TIME UPDATE FLOW                              │
└──────────────────────────────────────────────────────────────────────────┘

MINUTE 1:00 →  Celery Beat
                │
                ├─→ Triggers: fetch_market_data()
                │   (scheduled task)
                │
                ├─→ MarketDataFetcher.fetch_real_time_quote("AAPL")
                │   │
                │   ├─→ Check Redis Cache
                │   │   ├─ HIT → Return cached price
                │   │   └─ MISS → Continue
                │   │
                │   ├─→ Call yfinance API
                │   │   └─→ Get current price, volume, etc.
                │   │
                │   └─→ Return: {price, change, volume, timestamp}
                │
                ├─→ fetcher.save_stock_price("AAPL", quote)
                │   └─→ Database: INSERT StockPrice(symbol, timestamp, OHLCV)
                │
                ├─→ cache.set(f"latest_price_AAPL", quote, 300)
                │   └─→ Redis: Store quote for 5 minutes
                │
                ├─→ producer.send_market_data("AAPL", quote)
                │   └─→ Kafka: Publish to "stock_prices" topic
                │
                └─→ broadcast_stock_update("AAPL", quote)
                    │
                    ├─→ Get Channel Layer (Redis)
                    │
                    ├─→ group_send("stock_AAPL", {
                    │   'type': 'stock_update',
                    │   'data': {...}
                    │ })
                    │
                    └─→ All MarketConsumers in group receive message
                        │
                        ├─→ async stock_update(event)
                        │   └─→ Send JSON via WebSocket to client
                        │
                        └─→ Clients connected to ws/market/:
                            {
                              "type": "stock_update",
                              "data": {
                                "symbol": "AAPL",
                                "price": 180.45,
                                "change": 2.15,
                                "changePercent": 1.20,
                                "volume": 52000000,
                                "timestamp": "2024-12-20T15:30:00Z"
                              }
                            }

MINUTE 5:00 →  Celery Beat
                │
                └─→ Triggers: calculate_technical_indicators()
                    │
                    ├─→ For each active stock:
                    │   │
                    │   ├─→ TechnicalIndicatorCalculator.calculate_indicators()
                    │   │   │
                    │   │   ├─→ Get last 200 StockPrice records
                    │   │   │
                    │   │   ├─→ Calculate:
                    │   │   │   ├─ SMA (20, 50, 200)
                    │   │   │   ├─ EMA (12, 26)
                    │   │   │   ├─ RSI (14)
                    │   │   │   ├─ MACD
                    │   │   │   ├─ Bollinger Bands
                    │   │   │   ├─ ATR (14)
                    │   │   │   └─ OBV
                    │   │   │
                    │   │   └─→ Return calculated indicators
                    │   │
                    │   ├─→ Save to TechnicalIndicator table
                    │   │
                    │   ├─→ Cache in Redis
                    │   │
                    │   └─→ broadcast_indicator_update()
                    │       └─→ Send to group "stock_AAPL"
                    │
                    └─→ Clients receive:
                        {
                          "type": "indicator_update",
                          "data": {
                            "symbol": "AAPL",
                            "rsi": 65.4,
                            "sma20": 179.50,
                            "sma50": 176.80,
                            "macd": 2.34,
                            "timestamp": "..."
                          }
                        }

HOURLY →        Celery Beat
                │
                └─→ Triggers: update_predictions()
                    │
                    ├─→ For top 50 stocks:
                    │   │
                    │   ├─→ Get 500 days of StockPrice data
                    │   │
                    │   ├─→ LSTMPredictor.predict(df, steps=90)
                    │   │   ├─→ Load trained Keras model
                    │   │   ├─→ Normalize data
                    │   │   ├─→ Generate 90 predictions
                    │   │   └─→ Return forecast array
                    │   │
                    │   ├─→ Calculate targets:
                    │   │   ├─ 7-day (index 6)
                    │   │   ├─ 30-day (index 29)
                    │   │   └─ 90-day (index 89)
                    │   │
                    │   ├─→ Save StockPrediction
                    │   │
                    │   └─→ broadcast_prediction_update()
                    │       └─→ Send to group "stock_AAPL"
                    │
                    └─→ Clients receive:
                        {
                          "type": "prediction_update",
                          "data": {
                            "symbol": "AAPL",
                            "predictions": {
                              "shortTerm": {
                                "targetPrice": 185.23,
                                "change": 2.65,
                                "trend": "Uptrend"
                              },
                              "mediumTerm": {...},
                              "longTerm": {...}
                            }
                          }
                        }

EVERY 30 MIN →  Celery Beat
                │
                └─→ Triggers: fetch_and_analyze_news()
                    │
                    ├─→ For top 50 stocks:
                    │   │
                    │   ├─→ NewsAPIService.fetch_news("AAPL")
                    │   │   └─→ Query news sources
                    │   │
                    │   ├─→ For each article:
                    │   │   │
                    │   │   ├─→ Save to NewsArticle table
                    │   │   │
                    │   │   ├─→ GeminiSentimentAnalyzer.analyze_article()
                    │   │   │   ├─→ Send to Gemini API
                    │   │   │   ├─→ Parse JSON response
                    │   │   │   └─→ Return: {sentiment, score, analysis}
                    │   │   │
                    │   │   └─→ Save to Sentiment table
                    │   │
                    │   └─→ broadcast_sentiment_update()
                    │       └─→ Send to group "stock_AAPL"
                    │
                    └─→ Clients receive:
                        {
                          "type": "sentiment_update",
                          "data": {
                            "symbol": "AAPL",
                            "sentiment": "positive",
                            "score": 0.85,
                            "timestamp": "..."
                          }
                        }
```

---

## WebSocket Connection Lifecycle

```
┌─────────────────────────────────────────────────────────────────────┐
│              WEBSOCKET CONNECTION LIFECYCLE                         │
└─────────────────────────────────────────────────────────────────────┘

CLIENT SIDE:

1. ESTABLISH CONNECTION
   │
   ├─→ JavaScript: new WebSocket("ws://localhost:8000/ws/market/")
   │
   └─→ Server receives connection request
       │
       └─→ MarketConsumer.connect()
           ├─→ Authenticate user (AuthMiddlewareStack)
           ├─→ Accept connection: await self.accept()
           ├─→ Initialize: self.subscribed_symbols = set()
           └─→ Log: "WebSocket connected: channel_id"


2. SUBSCRIBE TO STOCK
   │
   ├─→ Client sends: {"type": "subscribe", "symbol": "AAPL"}
   │
   └─→ Server receives:
       │
       ├─→ MarketConsumer.receive(text_data)
       │   ├─→ Parse JSON
       │   ├─→ Validate symbol
       │   └─→ Call: self.subscribe_to_stock("AAPL")
       │
       └─→ MarketConsumer.subscribe_to_stock("AAPL")
           │
           ├─→ Add to group: group_add("stock_AAPL", self.channel_name)
           │   └─→ Redis: Track this connection as subscriber
           │
           ├─→ Add to set: self.subscribed_symbols.add("AAPL")
           │
           ├─→ Send confirmation:
           │   await self.send({
           │     'type': 'subscribed',
           │     'symbol': 'AAPL',
           │     'message': 'Subscribed to AAPL'
           │   })
           │
           └─→ Send current price (if cached):
               cache_key = "latest_price_AAPL"
               price_data = cache.get(cache_key)
               if price_data:
                   await self.send({
                     'type': 'stock_update',
                     'data': price_data
                   })


3. RECEIVE REAL-TIME UPDATES
   │
   ├─→ Every minute: Celery broadcasts new data
   │   │
   │   ├─→ broadcast_stock_update("AAPL", quote)
   │   │   │
   │   │   └─→ channel_layer.group_send("stock_AAPL", {
   │   │       'type': 'stock_update',
   │   │       'data': {...}
   │   │     })
   │   │
   │   └─→ Redis routes message to all channels in group
       │
       └─→ MarketConsumer.stock_update(event)
           │
           ├─→ Extract event['data']
           │
           └─→ Send to WebSocket:
               await self.send(json.dumps({
                 'type': 'stock_update',
                 'data': {...}
               }))


4. CLIENT RECEIVES UPDATES
   │
   └─→ JavaScript: ws.onmessage = (event) => {
         const message = JSON.parse(event.data);
         if (message.type === 'stock_update') {
           updateChart(message.data);
         }
       }


5. UNSUBSCRIBE FROM STOCK
   │
   ├─→ Client sends: {"type": "unsubscribe", "symbol": "AAPL"}
   │
   └─→ Server:
       │
       ├─→ MarketConsumer.receive(text_data)
       │   └─→ Call: self.unsubscribe_from_stock("AAPL")
       │
       └─→ MarketConsumer.unsubscribe_from_stock("AAPL")
           │
           ├─→ Remove from group: group_discard("stock_AAPL", ...)
           │   └─→ Redis: Stop routing updates to this channel
           │
           ├─→ Remove from set: self.subscribed_symbols.discard("AAPL")
           │
           └─→ Send confirmation:
               await self.send({
                 'type': 'unsubscribed',
                 'symbol': 'AAPL',
                 'message': 'Unsubscribed from AAPL'
               })


6. CLOSE CONNECTION
   │
   ├─→ Client: ws.close()
   │
   └─→ Server:
       │
       └─→ MarketConsumer.disconnect(close_code)
           │
           ├─→ Loop through subscribed symbols:
           │   └─→ For each symbol:
           │       group_discard("stock_{symbol}", ...)
           │
           ├─→ Clear subscribed_symbols
           │
           └─→ Log: "WebSocket disconnected: channel_id"
```

---

## Database Schema Relationships

```
┌────────────────────────────────────────────────────────────────────┐
│              DATABASE SCHEMA RELATIONSHIPS                         │
└────────────────────────────────────────────────────────────────────┘

AUTHENTICATION:
┌──────────────────┐
│      User        │                  ┌─────────────────────┐
├──────────────────┤                  │   UserProfile       │
│ id (UUID)        │◄──────1:1────────├─────────────────────┤
│ email (unique)   │                  │ id                  │
│ full_name        │                  │ subscription_tier   │
│ avatar_url       │                  │ api_key             │
│ is_active        │                  │ daily_request_count │
│ created_at       │                  │ notification_prefs  │
│ updated_at       │                  │ last_login_ip       │
└──────────────────┘                  └─────────────────────┘
        │
        │1:M
        │
        ▼
┌──────────────────┐
│  RefreshToken    │
├──────────────────┤
│ id (UUID)        │
│ token            │
│ expires_at       │
│ is_revoked       │


MARKET DATA:
┌──────────────────┐
│      Stock       │
├──────────────────┤
│ symbol (PK)      │
│ name             │
│ sector           │
│ industry         │
│ market_cap       │
│ exchange         │
│ currency         │
│ is_active        │
└──────┬───────────┘
       │1:M
       ├────────────┬───────────────┬──────────────┐
       │            │               │              │
       ▼            ▼               ▼              ▼
  ┌─────────────┐  ┌────────────┐  ┌──────────────┐  ┌──────────────┐
  │ StockPrice  │  │Technical   │  │   Market     │  │ NewsArticle  │
  ├─────────────┤  │ Indicator  │  │ ScanResult   │  ├──────────────┤
  │ timestamp   │  ├────────────┤  ├──────────────┤  │ title        │
  │ open        │  │ timestamp  │  │ timestamp    │  │ description  │
  │ high        │  │ sma_20,50  │  │ timeframe    │  │ source       │
  │ low         │  │ ema_12,26  │  │ trend        │  │ url          │
  │ close       │  │ rsi_14     │  │ is_breakout  │  │ published_at │
  │ volume      │  │ macd       │  │ is_unusual   │  └──────────────┘
  │ adj_close   │  │ bollinger  │  │ support,res  │         │1:M
  └─────────────┘  │ atr_14     │  └──────────────┘         │
                   │ obv        │                           ▼
                   └────────────┘                   ┌──────────────┐
                                                    │  Sentiment   │
                                                    ├──────────────┤
                                                    │ ai_sentiment │
                                                    │ ai_score     │
                                                    │ analysis     │
                                                    └──────────────┘

                   ┌──────────────┐
                   │ StockPredic- │
                   │    tion      │
                   ├──────────────┤
                   │ current_price│
                   │ short_term   │
                   │ medium_term  │
                   │ long_term    │
                   │ bullish_score│
                   │ timestamp    │
                   └──────────────┘


PORTFOLIO:
┌──────────────┐                  ┌─────────────────────┐
│     User     │                  │ PortfolioHolding    │
├──────────────┤                  ├─────────────────────┤
│ id (UUID)    │◄──────1:M────────│ id (UUID)           │
│              │                  │ shares              │
│              │                  │ average_price       │
│              │                  │ purchase_date       │
└──────────────┘                  │ notes               │
        │                         │ created_at          │
        │1:M                      │ updated_at          │
        │                         └──────────┬──────────┘
        │                                    │ M:1
        │                                    │
        ▼                                    ▼
   Watchlist ─────────M:1────→ Stock


CONSTRAINT: PortfolioHolding UNIQUE(user, stock)
CONSTRAINT: Watchlist UNIQUE(user, stock)
```

---

## Task Execution Timeline

```
┌─────────────────────────────────────────────────────────────────┐
│            CELERY BEAT TASK EXECUTION TIMELINE                  │
└─────────────────────────────────────────────────────────────────┘

Time      Task                              Queue        Duration
────────────────────────────────────────────────────────────────
00:00     cleanup_old_data()                default      ~2-5 min
          └─ Delete records >1 year old

00:30     fetch_and_analyze_news()          sentiment    ~3-5 min
          └─ Fetch & analyze 50 stocks

01:00     fetch_market_data()               market_data  ~1-2 min
          └─ Update prices for 100 stocks
          broadcast_stock_update() × 100

01:00     calculate_technical_indicators()  market_data  ~2-3 min
          └─ Calculate indicators for 100 stocks (every 5 min)

01:00     update_predictions() HOURLY       predictions  ~3-5 min
          └─ LSTM inference for 50 stocks

01:30     fetch_and_analyze_news()          sentiment    ~3-5 min

02:00     fetch_market_data()               market_data  ~1-2 min
          │
          └─ Repeats every minute

...

16:00     run_market_scanner(timeframe='daily')         ~5-10 min
          └─ Scan all stocks (daily at 4 PM ET)

16:00     run_market_scanner(timeframe='weekly')        ~10-15 min
          └─ Scan all stocks (Friday 4 PM ET)


QUEUE CAPACITY:
────────────────────────────────────────────────────────────────
market_data queue:    3-5 workers (high throughput needed)
predictions queue:    2-3 workers (ML-heavy)
sentiment queue:      2-3 workers (API-heavy, can be slow)
default queue:        1-2 workers (scanner, cleanup)


REDIS MEMORY USAGE:
────────────────────────────────────────────────────────────────
Cache (DB 0):         ~50-100 MB (stock prices, indicators)
Celery Broker (DB 1): ~20-50 MB (pending tasks)
Celery Results (DB 2):~30-70 MB (task results)
Channel Layer:        ~10-30 MB (WebSocket subscriptions)
────────────────────────────────────────────────────────────────
Total Redis:          ~150-300 MB recommended
```

---

## Performance & Scaling Considerations

```
┌─────────────────────────────────────────────────────────────────┐
│           PERFORMANCE & SCALING GUIDELINES                      │
└─────────────────────────────────────────────────────────────────┘

DATABASE (PostgreSQL):
──────────────────────
Indexes:
├─ Stock.symbol (PK)
├─ StockPrice (stock, timestamp) UNIQUE
├─ StockPrice.timestamp (range queries)
├─ TechnicalIndicator (stock, timestamp) UNIQUE
├─ TechnicalIndicator.timestamp
├─ MarketScanResult (timeframe, timestamp)
├─ PortfolioHolding (user, stock) UNIQUE
├─ Watchlist (user, stock) UNIQUE
└─ RefreshToken (token, user)

Partitioning:
├─ StockPrice → Partition by month (large table)
├─ TechnicalIndicator → Partition by month
├─ NewsArticle → Partition by published_at
└─ Sentiment → Partition by timestamp

Connection Pool: 20-30 connections


REDIS (Cache & Broker):
───────────────────────
Memory Management:
├─ Eviction policy: allkeys-lru (remove least recently used)
├─ Maxmemory: 1-2 GB recommended
├─ Persistence: RDB snapshot every 6 hours + AOF

Key Expiration:
├─ Stock prices: 5 minutes
├─ Technical indicators: 10 minutes
├─ Company overviews: 24 hours
├─ Market scanner results: 10 minutes
└─ Celery task results: 1 hour


CELERY TASK QUEUE:
──────────────────
Worker Configuration:
├─ Concurrency: 4-8 (adjust per CPU cores)
├─ Prefetch: 2-4 (avoid task starvation)
├─ Time limit: 30 minutes
├─ Soft time limit: 25 minutes
└─ Task timeout: 5 minutes for most tasks

Scaling:
├─ market_data: 3-5 workers (must handle 100+ stocks/min)
├─ predictions: 2-3 workers (ML-heavy, slow)
├─ sentiment: 2-3 workers (API-heavy, variable latency)
└─ default: 1-2 workers (scanner, cleanup)


WEBSOCKET (Channels):
─────────────────────
Limits:
├─ Max connections per server: ~1,000-2,000
├─ Message throughput: ~10,000 updates/min
├─ Max subscriptions per client: 100 (configurable)

Scaling:
├─ Use Redis channel layer (already configured)
├─ Add Daphne workers as needed
├─ Monitor channel layer latency
└─ Consider separate Daphne instances for WebSockets


API RATE LIMITING:
──────────────────
Current Implementation: Development stub (advisory only)
Production Implementation Needed:
├─ Per-user limits: 1000 requests/hour
├─ Per-IP limits: 100 requests/hour (anonymous)
├─ Per-endpoint limits: Vary by endpoint
└─ Sliding window algorithm recommended


HORIZONTAL SCALING:
───────────────────
Architecture:
├─ Load Balancer (nginx)
│  └─ Routes to multiple Django instances
│  └─ WebSocket sticky sessions required
│
├─ Django App Servers (multiple instances)
│  └─ Stateless (use Redis for state)
│
├─ PostgreSQL
│  └─ Single primary + read replicas
│
├─ Redis Cluster
│  └─ 6+ nodes for HA
│
├─ Celery Workers (distributed)
│  └─ 10+ workers across multiple machines
│
└─ Message Broker
   └─ Kafka for event streaming
   └─ Zookeeper for coordination


MONITORING & ALERTS:
────────────────────
Prometheus Metrics:
├─ API response time (histogram)
├─ Celery task duration
├─ Redis memory usage
├─ Database connection pool
├─ WebSocket connections
└─ Error rates by endpoint

Sentry Error Tracking:
├─ Setup already installed
├─ Configure DSN in settings
└─ Monitor exception rates


DATA RETENTION POLICY:
──────────────────────
StockPrice:
├─ Daily candles: Keep 5+ years
├─ Hourly candles: Keep 1 year
├─ Minute candles: Keep 3 months

TechnicalIndicator:
├─ Daily: Keep 5+ years
├─ Keep in sync with StockPrice

NewsArticle:
├─ Keep indefinitely (searchable history)
├─ Archive old articles to cold storage

Sentiment:
├─ Keep 2+ years (sentiment trends)

StockPrediction:
├─ Keep latest + historical (model accuracy)

Celery Task Results:
├─ Expire after 1 hour
├─ Don't store in DB (transient)
```

