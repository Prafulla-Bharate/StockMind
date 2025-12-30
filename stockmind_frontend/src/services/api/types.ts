// Common API types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

// Auth types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest extends LoginRequest {
  fullName: string;
}

export interface AuthResponse {
  token: string;
  user: UserProfile;
}

export interface UserProfile {
  id: string;
  email: string;
  fullName: string | null;
  avatarUrl: string | null;
  createdAt: string;
}

// Market data types
export interface StockData {
  symbol: string;
  name: string;
  currency: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap: number;
  high52w: number;
  low52w: number;
  historicalData: HistoricalDataPoint[];
  indicators: {
    rsi: number;
    macd: number;
    sma20: number;
    sma50: number;
  };
}

export interface HistoricalDataPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// Scanner types
export interface MarketScannerResponse {
  timeframe: 'daily' | 'weekly' | 'monthly';
  timestamp: string;
  gainers: StockScanData[];
  losers: StockScanData[];
  mostActive: StockScanData[];
  unusualVolume: StockScanData[];
  breakouts: StockScanData[];
  marketOverview: {
    totalScanned: number;
    bullish: number;
    bearish: number;
    avgChange: number;
  };
}

export interface StockScanData {
  symbol: string;
  name: string;
  currency: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  avgVolume: number;
  volumeRatio: number;
  isUnusualVolume: boolean;
  isBreakout: boolean;
  resistance: number;
  support: number;
  rsi: number;
  sma20: number;
  sma50: number;
  trend: 'Bullish' | 'Bearish';
}

// Portfolio types
export interface PortfolioHolding {
  id: string;
  symbol: string;
  currency?: string;
  shares: number;
  averagePrice: number;
  purchaseDate: string;
  notes: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface WatchlistItem {
  id: string;
  symbol: string;
  currency?: string;
  addedAt: string;
}

// News types
export interface NewsArticle {
  title: string;
  description: string;
  url: string;
  source: string;
  publishedAt: string;
  urlToImage: string | null;
  sentiment: {
    score: number;
    label: string;
    explanation: string;
  };
}

export interface NewsFeedResponse {
  news: NewsArticle[];
  overallSentiment: {
    score: number;
    label: string;
    totalArticles: number;
    bullish: number;
    neutral: number;
    bearish: number;
  };
}

// Prediction types
export interface AIPredictionResponse {
  prediction: string;
  currency?: string;
}

export interface StatisticalPrediction {
  symbol: string;
  currency?: string;
  timestamp: string;
  currentPrice: string;
  technicalIndicators: {
    sma20: string;
    sma50: string;
    rsi: string;
    macd: string;
    macdSignal: string;
    macdHistogram: string;
    bollingerUpper: string;
    bollingerLower: string;
    volatility: string;
  };
  signals: {
    macd: 'Bullish' | 'Bearish';
    rsi: 'Overbought' | 'Oversold' | 'Neutral';
    ma_cross: 'Bullish' | 'Bearish';
    price_vs_sma20: 'Above' | 'Below';
    bollinger: 'Overbought' | 'Oversold' | 'Normal';
    volume: 'Increasing' | 'Normal';
  };
  predictions: {
    shortTerm: PredictionTimeframe;
    mediumTerm: PredictionTimeframe;
    longTerm: PredictionTimeframe;
  };
  supportResistance: {
    resistance: string;
    support: string;
    distance_to_resistance: string;
    distance_to_support: string;
  };
  overallOutlook: {
    bullishScore: string;
    sentiment: 'Bullish' | 'Bearish' | 'Neutral';
    riskLevel: 'High' | 'Medium' | 'Low';
  };
}

interface PredictionTimeframe {
  period: string;
  targetPrice: string;
  change: string;
  confidence: 'High' | 'Medium' | 'Low';
  trend: 'Uptrend' | 'Downtrend';
}

// Portfolio Summary Types
export interface CurrencyBreakdown {
  currency: string;
  totalValue: number;
  totalCost: number;
  profitLoss: number;
  profitLossPercent: number;
  holdings: number;
}

export interface PortfolioSummary {
  totalHoldings: number;
  currencyBreakdown: CurrencyBreakdown[];
  note: string;
}