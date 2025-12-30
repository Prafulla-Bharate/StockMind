import { api } from './axios';
import type { ApiResponse, PortfolioHolding, WatchlistItem, PortfolioSummary } from './types';

export const portfolioService = {
  // Portfolio summary with multi-currency breakdown
  async getSummary(): Promise<PortfolioSummary> {
    const response = await api.get<ApiResponse<PortfolioSummary>>('/portfolio/summary');
    return response.data.data;
  },

  // Portfolio holdings
  async getHoldings(): Promise<PortfolioHolding[]> {
    const response = await api.get<ApiResponse<PortfolioHolding[]>>('/portfolio/holdings');
    return response.data.data;
  },

  async addHolding(data: Omit<PortfolioHolding, 'id' | 'createdAt' | 'updatedAt'>): Promise<PortfolioHolding> {
    const response = await api.post<ApiResponse<PortfolioHolding>>('/portfolio/holdings', data);
    return response.data.data;
  },

  async updateHolding(id: string, data: Partial<PortfolioHolding>): Promise<PortfolioHolding> {
    const response = await api.patch<ApiResponse<PortfolioHolding>>(`/portfolio/holdings/${id}`, data);
    return response.data.data;
  },

  async deleteHolding(id: string): Promise<void> {
    await api.delete(`/portfolio/holdings/${id}`);
  },

  // Watchlist
  async getWatchlist(): Promise<WatchlistItem[]> {
    const response = await api.get<ApiResponse<WatchlistItem[]>>('/portfolio/watchlist');
    return response.data.data;
  },

  async addToWatchlist(symbol: string): Promise<WatchlistItem> {
    const response = await api.post<ApiResponse<WatchlistItem>>('/portfolio/watchlist', { symbol });
    return response.data.data;
  },

  async removeFromWatchlist(id: string): Promise<void> {
    await api.delete(`/portfolio/watchlist/${id}`);
  }
};