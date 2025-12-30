import { api } from './axios';
import type { 
  ApiResponse, 
  StockData, 
  MarketScannerResponse,
  NewsFeedResponse,
  AIPredictionResponse,
  StatisticalPrediction
} from './types';

export const marketService = {
  async getStockData(symbol: string): Promise<StockData> {
    const response = await api.get<ApiResponse<StockData>>(`/market/stock/${symbol}`);
    return response.data.data;
  },

  async getMarketScanner(timeframe: 'daily' | 'weekly' | 'monthly'): Promise<MarketScannerResponse> {
    const response = await api.get<ApiResponse<MarketScannerResponse>>('/market/scanner', {
      params: { timeframe }
    });
    return response.data.data;
  },

  async getNewsFeed(symbol: string, companyName?: string): Promise<NewsFeedResponse> {
    const response = await api.get<ApiResponse<NewsFeedResponse>>('/market/news', {
      params: { symbol, companyName }
    });
    return response.data.data;
  },

  async getAIPrediction(symbol: string, historicalData: any): Promise<AIPredictionResponse> {
    const safeSymbol = (symbol ?? '').toString().trim().toUpperCase();
    if (!safeSymbol) {
      throw new Error('Symbol is required for AI prediction');
    }
    
    // Log the exact payload for debugging
    const payload = {
      symbol: safeSymbol,
      historicalData
    };
    if (import.meta.env.DEV) {
      // eslint-disable-next-line no-console
      console.debug('[market] AI Prediction payload:', payload);
    }

    try {
      const response = await api.post<ApiResponse<AIPredictionResponse>>('/market/ai-prediction', payload);
      return response.data.data;
    } catch (error: any) {
      // Enhanced error logging to show backend validation errors
      if (import.meta.env.DEV && error.response?.data) {
        // eslint-disable-next-line no-console
        console.error('[market] AI Prediction error details:', error.response.data);
      }
      throw error;
    }
  },

  async getStatisticalPrediction(symbol: string, historicalData: any): Promise<StatisticalPrediction> {
    const safeSymbol = (symbol ?? '').toString().trim().toUpperCase();
    if (!safeSymbol) {
      throw new Error('Symbol is required for statistical prediction');
    }

    const payload = {
      symbol: safeSymbol,
      historicalData
    };

    if (import.meta.env.DEV) {
      console.debug('[market] Statistical Prediction payload:', payload);
      console.debug('[market] Historical data length:', historicalData?.length || 0);
    }

    try {
      const response = await api.post<ApiResponse<StatisticalPrediction>>('/market/statistical-prediction', payload);
      
      if (import.meta.env.DEV) {
        console.debug('[market] Statistical Prediction response:', response.data);
      }

      return response.data.data;
    } catch (error: any) {
      if (import.meta.env.DEV && error.response?.data) {
        console.error('[market] Statistical Prediction error details:', error.response.data);
      }
      throw error;
    }
  },

  async getAISentiment(symbol: string): Promise<{ 
    sentiment: string;
    sentimentScore: number;
    analysis: string;
    timestamp: string;
  }> {
    const response = await api.get<ApiResponse<{
      sentiment: string;
      sentimentScore: number;
      analysis: string;
      timestamp: string;
    }>>(`/market/sentiment/${symbol}`);
    return response.data.data;
  }
};